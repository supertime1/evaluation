from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.experiment import Experiment
from app.schemas.experiment import (
    Experiment as ExperimentSchema,
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentWithRuns
)
from app.api.v1.endpoints.auth import fastapi_users
from app.models.user import User

router = APIRouter()

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Current user dependency
current_active_user = fastapi_users.current_user(active=True)

@router.post("/", response_model=ExperimentSchema)
async def create_experiment(
    *,
    db: AsyncSession = Depends(get_db),
    experiment_in: ExperimentCreate,
    current_user: User = Depends(current_active_user)
) -> ExperimentSchema:
    """
    Create a new experiment.
    """
    # Create new experiment
    db_experiment = Experiment(
        name=experiment_in.name,
        description=experiment_in.description,
        user_id=str(current_user.id)
    )
    
    # Add to database and commit
    db.add(db_experiment)
    await db.commit()
    await db.refresh(db_experiment)
    
    return db_experiment

@router.get("/", response_model=List[ExperimentSchema])
async def read_experiments(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
) -> List[ExperimentSchema]:
    """
    Retrieve experiments for the current user.
    """
    # Build and execute query
    query = select(Experiment).where(Experiment.user_id == str(current_user.id)).offset(skip).limit(limit)
    result = await db.execute(query)
    experiments = result.scalars().all()
    
    return experiments

@router.get("/{experiment_id}", response_model=ExperimentWithRuns)
async def read_experiment(
    *,
    db: AsyncSession = Depends(get_db),
    experiment_id: str,
    current_user: User = Depends(current_active_user)
) -> ExperimentWithRuns:
    """
    Get experiment by ID with its runs.
    """
    # Get experiment with eager loading of runs
    query = select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    return experiment

@router.put("/{experiment_id}", response_model=ExperimentSchema)
async def update_experiment(
    *,
    db: AsyncSession = Depends(get_db),
    experiment_id: str,
    experiment_in: ExperimentUpdate,
    current_user: User = Depends(current_active_user)
) -> ExperimentSchema:
    """
    Update an experiment.
    """
    # Get experiment
    query = select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Update fields
    update_data = experiment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(experiment, field, value)
    
    # Commit changes
    await db.commit()
    await db.refresh(experiment)
    
    return experiment

@router.delete("/{experiment_id}", response_model=ExperimentSchema)
async def delete_experiment(
    *,
    db: AsyncSession = Depends(get_db),
    experiment_id: str,
    current_user: User = Depends(current_active_user),
    background_tasks: BackgroundTasks
) -> ExperimentSchema:
    """
    Delete an experiment.
    """
    # Get experiment
    query = select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Delete the experiment (this will cascade to runs and test results)
    await db.delete(experiment)
    await db.commit()
    
    return experiment