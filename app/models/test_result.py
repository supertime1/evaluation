from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    name = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    conversational = Column(Boolean, nullable=False)
    multimodal = Column(Boolean, nullable=True)
    input = Column(JSON, nullable=True)  # Can store string or list of strings/images
    actual_output = Column(JSON, nullable=True)  # Can store string or list of strings/images
    expected_output = Column(String, nullable=True)
    context = Column(JSON, nullable=True)  # List of strings
    retrieval_context = Column(JSON, nullable=True)  # List of strings
    metrics_data = Column(JSON, nullable=True)  # List of MetricData
    additional_metadata = Column(JSON, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("Run", back_populates="test_results")
    test_case = relationship("TestCase", back_populates="test_results") 