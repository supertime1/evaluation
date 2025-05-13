from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.base_class import Base

class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=lambda: f"run_{uuid.uuid4().hex[:8]}")
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    git_commit = Column(String, nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Flexible hyperparameters that can store any configuration
    # This matches deepeval's hyperparameters type: Dict[str, Union[str, int, float, Prompt]]
    hyperparameters = Column(JSON, nullable=True)

    # Relationships
    experiment = relationship("Experiment", back_populates="runs")
    test_results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan") 