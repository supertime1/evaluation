from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.test_result import TestResult
from app.models.user import User
from app.models.run import Run
from app.models.experiment import Experiment

from app.schemas.test_result import (
    TestResult as TestResultSchema,
    TestResultCreate,
)
from app.api.v1.endpoints.auth import fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload


router = APIRouter()

# Current user dependency
current_active_user = fastapi_users.current_user(active=True)

@router.post("/", response_model=TestResultSchema)
async def create_test_result(
    *,
    db: AsyncSession = Depends(get_db),
    test_result_in: TestResultCreate,
    current_user: User = Depends(current_active_user)
) -> TestResultSchema:
    """
    Create a new test result.

    Args:
        test_result_in: The test result to create.
        current_user: The current user.

    Returns:
        The created test result.
    """
    # check if run belongs to the current user, by checking its experiment
    query = select(Run).options(
        joinedload(Run.experiment)
    ).where(
        and_(
            Run.id == test_result_in.run_id,
            Run.experiment.has(Experiment.user_id == str(current_user.id))
        )
    )
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or does not belong to current user")
    
    db_test_result = TestResult(
        run_id=test_result_in.run_id,
        test_case_id=test_result_in.test_case_id,
        name=test_result_in.name,
        success=test_result_in.success,
        conversational=test_result_in.conversational,
        input=test_result_in.input,
        actual_output=test_result_in.actual_output,
        expected_output=test_result_in.expected_output,
        context=test_result_in.context,
        retrieval_context=test_result_in.retrieval_context,
        metrics_data=test_result_in.metrics_data,
        additional_metadata=test_result_in.additional_metadata
    )
    
    db.add(db_test_result)
    await db.commit()
    await db.refresh(db_test_result)

    return db_test_result


@router.get("/{test_result_id}", response_model=TestResultSchema)
async def read_test_result(
    *,
    db: AsyncSession = Depends(get_db),
    test_result_id: str,
    current_user: User = Depends(current_active_user)
) -> TestResultSchema:
    """
    Get a test result by ID.

    Args:
        test_result_id: The ID of the test result to get.
        current_user: The current user.

    Returns:
        The test result.
    """
    query = select(TestResult).options(
        joinedload(TestResult.run).joinedload(Run.experiment)
    ).where(
        and_(
            TestResult.id == test_result_id,
            TestResult.run.has(Run.experiment.has(Experiment.user_id == str(current_user.id)))
        )
    )
    result = await db.execute(query)
    test_result = result.scalar_one_or_none()
    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found or does not belong to current user")
    
    return test_result

@router.post("/batch", response_model=list[TestResultSchema])
async def create_test_results_batch(
    *,
    db: AsyncSession = Depends(get_db),
    test_results_in: list[TestResultCreate],
    current_user: User = Depends(current_active_user)
) -> list[TestResultSchema]:
    """
    Create a batch of test results.

    Args:
        test_results_in: A list of test result objects to create.
        current_user: The current user.

    Returns:
        A list of created test result objects.
    """
    # check if runs belong to the current user, by checking their experiments
    run_ids = [test_result.run_id for test_result in test_results_in]
    unique_run_ids = set(run_ids)
    
    query = select(Run).options(
        joinedload(Run.experiment)
    ).where(
        and_(
            Run.id.in_(unique_run_ids),
            Run.experiment.has(Experiment.user_id == str(current_user.id))
        )
    )
    print(f"current user: {current_user.id}")
    
    result = await db.execute(query)
    runs = result.scalars().all()
    found_run_ids = {run.id for run in runs}
    
    # Check if any run_ids are missing
    missing_run_ids = unique_run_ids - found_run_ids
    if missing_run_ids:
        raise HTTPException(
            status_code=404, 
            detail=f"Some runs not found or do not belong to current user: {missing_run_ids}"
        )
    
    
    db_test_results = [
        TestResult(
            run_id=test_result.run_id,
            test_case_id=test_result.test_case_id,
            name=test_result.name,
            success=test_result.success,
            conversational=test_result.conversational,
            input=test_result.input,
            actual_output=test_result.actual_output,
            expected_output=test_result.expected_output,
            context=test_result.context,
            retrieval_context=test_result.retrieval_context,
            metrics_data=test_result.metrics_data,
            additional_metadata=test_result.additional_metadata
        )
        for test_result in test_results_in
    ]
    
    db.add_all(db_test_results) 
    await db.commit()
    
    # Replace refresh_all with individual refreshes
    for result in db_test_results:
        await db.refresh(result)

    return db_test_results