from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.run import Run

# Base schema with common fields
class ExperimentBase(BaseModel):
    name: str
    description: Optional[str] = None

# Schema for creating a new experiment
class ExperimentCreate(ExperimentBase):
    pass

# Schema for updating an existing experiment
class ExperimentUpdate(ExperimentBase):
    pass

# Schema for experiment response
class Experiment(ExperimentBase):
    id: str = Field(..., pattern="^exp_[a-f0-9]{8}$")
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for experiment with runs
class ExperimentWithRuns(Experiment):
    runs: List[Run] = []

    class Config:
        from_attributes = True 

ExperimentWithRuns.model_rebuild()