from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.run import Run
from app.models.user import User
from app.models.experiment import Experiment

from app.schemas.run import (
    Run as RunSchema,
    RunCreate,
    RunUpdate,
    RunWithResults,
    RunStatus
)
from app.api.v1.endpoints.auth import fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter()

# Current user dependency
current_active_user = fastapi_users.current_user(active=True)

@router.post("/", response_model=RunSchema)
async def create_run(
    *,
    db: AsyncSession = Depends(get_db),
    run_in: RunCreate,
    current_user: User = Depends(current_active_user)
) -> RunSchema:
    """
    Create a new run.

    Args:
        run_in: The run to create.
        current_user: The current user.

    Returns:
        The created run.
    """
    # check if the experiment belongs to the current user
    query = select(Experiment).where(
        Experiment.id == run_in.experiment_id,
        Experiment.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found or does not belong to current user")

    db_run = Run(
        experiment_id=run_in.experiment_id,
        git_commit=run_in.git_commit,
        hyperparameters=run_in.hyperparameters,
        status=RunStatus.PENDING
    )
    
    db.add(db_run)
    await db.commit()
    await db.refresh(db_run)
    
    return db_run


@router.get("/{run_id}", response_model=RunWithResults)
async def read_run(
    *,
    db: AsyncSession = Depends(get_db),
    run_id: str,
    current_user: User = Depends(current_active_user)
) -> RunWithResults:
    """
    Get a run by ID.

    Args:
        run_id: The ID of the run to get.
        current_user: The current user.

    Returns:
        The run with its results.
    """
    # First check if the run exists and belongs to the current user
    query = select(Run).options(
        selectinload(Run.test_results),
        selectinload(Run.experiment)
    ).where(
        Run.id == run_id,
        Run.experiment.has(Experiment.user_id == str(current_user.id))  # Join condition for ownership
    )
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or does not belong to current user")
    
    return run


@router.put("/{run_id}", response_model=RunSchema)
async def update_run(
    *,
    db: AsyncSession = Depends(get_db),
    run_id: str,
    run_in: RunUpdate,
    current_user: User = Depends(current_active_user)
) -> RunSchema:
    """
    Update a run.

    Args:
        run_id: The ID of the run to update.
        run_in: The run to update.
        current_user: The current user.

    Returns:
        The updated run.
    """
    # First check if the run exists and belongs to the current user
    query = select(Run).options(
        selectinload(Run.experiment)
    ).where(
        Run.id == run_id,
        Run.experiment.has(Experiment.user_id == str(current_user.id))
    )
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or does not belong to current user")
    
    # Update fields
    update_data = run_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(run, field, value)
    
    # Commit changes
    await db.commit()
    await db.refresh(run)
    
    return run

@router.delete("/{run_id}", response_model=RunSchema)
async def delete_run(
    *,
    db: AsyncSession = Depends(get_db),
    run_id: str,
    current_user: User = Depends(current_active_user)
) -> RunSchema:
    """
    Delete a run.

    Args:
        run_id: The ID of the run to delete.
        current_user: The current user.

    Returns:
        The deleted run.
    """
    # First check if the run exists and belongs to the current user
    query = select(Run).options(
        selectinload(Run.experiment)
    ).where(
        Run.id == run_id,
        Run.experiment.has(Experiment.user_id == str(current_user.id))
    )
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or does not belong to current user")

    await db.delete(run)
    await db.commit()
    
    return run
