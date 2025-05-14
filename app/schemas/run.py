from datetime import datetime
from typing import Optional, Dict, Union, List
from pydantic import BaseModel, Field
from enum import Enum

from app.schemas.test_result import TestResult

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# Base schema with common fields
class RunBase(BaseModel):
    git_commit: str
    hyperparameters: Optional[Dict[str, Union[str, int, float]]] = None

# Schema for creating a new run
class RunCreate(RunBase):
    experiment_id: str = Field(..., pattern="^exp_[a-f0-9]{8}$")

# Schema for updating an existing run
class RunUpdate(BaseModel):
    status: Optional[RunStatus] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    hyperparameters: Optional[Dict[str, Union[str, int, float]]] = None

# Schema for run response
class Run(RunBase):
    id: str = Field(..., pattern="^run_[a-f0-9]{8}$")
    experiment_id: str = Field(..., pattern="^exp_[a-f0-9]{8}$")
    status: RunStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Schema for run with test results
class RunWithResults(Run):
    test_results: List[TestResult] = []

    class Config:
        from_attributes = True 

RunWithResults.model_rebuild()