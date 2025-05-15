from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.test_result import TestResult
from app.models.user import User
from app.models.run import Run
from app.models.experiment import Experiment
from deepeval.test_run import MetricData

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

def serialize_metric_data(metric_data: list[MetricData]) -> list[dict]:
    """Convert MetricData objects to dictionaries."""
    return [
        {
            "name": metric.name,
            "score": metric.score,
            "threshold": metric.threshold,
            "success": metric.success,
            "reason": metric.reason,
            "strict_mode": metric.strict_mode,
            "evaluation_model": metric.evaluation_model,
            "error": metric.error,
            "evaluation_cost": metric.evaluation_cost,
            "verbose_logs": metric.verbose_logs
        }
        for metric in metric_data
    ] if metric_data else []

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
    
    # Convert MetricData objects to dictionaries
    metrics_data = serialize_metric_data(test_result_in.metrics_data)
    
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
        metrics_data=metrics_data,
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