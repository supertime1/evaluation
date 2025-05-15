from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.test_result import TestResult
from app.models.user import User
from app.models.run import Run

from app.schemas.test_result import (
    TestResult as TestResultSchema,
    TestResultCreate,
)
from app.api.v1.endpoints.auth import fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload


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
        selectinload(Run.experiment)
    ).where(
        Run.id == test_result_in.run_id,
        Run.experiment.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or does not belong to current user")
    
    db_test_result = TestResult(
        run_id=test_result_in.run_id,
        test_name=test_result_in.test_name,
        test_result=test_result_in.test_result,
        test_output=test_result_in.test_output,
        test_error=test_result_in.test_error
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
        selectinload(TestResult.run)
    ).where(
        TestResult.id == test_result_id,
        TestResult.run.experiment.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    test_result = result.scalar_one_or_none()
    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found or does not belong to current user")
    
    return test_result