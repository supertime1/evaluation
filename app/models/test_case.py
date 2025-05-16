from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.base_class import Base

class TestCaseType(str, enum.Enum):
    LLM = "llm"
    CONVERSATIONAL = "conversational"
    MULTIMODAL = "multimodal"

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String, primary_key=True, default=lambda: f"tc_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    input = Column(JSON, nullable=True)  # Can store string or list of strings/images
    expected_output = Column(String, nullable=True)
    context = Column(JSON, nullable=True)  # List of strings
    retrieval_context = Column(JSON, nullable=True)  # List of strings
    additional_metadata = Column(JSON, nullable=True)
    user_id = Column(String, nullable=False, index=True)  # Owner of the test case
    is_global = Column(Boolean, default=False)  # Whether this is a global test case
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_results = relationship("TestResult", back_populates="test_case") 