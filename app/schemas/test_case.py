from datetime import datetime
from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field
from deepeval.test_case import MLLMImage
from enum import Enum
from app.schemas.run import TestResult

class TestCaseType(str, Enum):
    LLM = "llm"
    CONVERSATIONAL = "conversational"
    MULTIMODAL = "multimodal"

# Base schema with common fields
class TestCaseBase(BaseModel):
    name: str
    type: str
    input: Optional[Union[str, List[Union[str, MLLMImage]]]] = None
    expected_output: Optional[str] = None
    context: Optional[List[str]] = None
    retrieval_context: Optional[List[str]] = None
    additional_metadata: Optional[Dict] = None
    is_global: bool = False

# Schema for creating a new test case
class TestCaseCreate(TestCaseBase):
    pass

# Schema for updating an existing test case
class TestCaseUpdate(TestCaseBase):
    pass

# Schema for test case response
class TestCase(TestCaseBase):
    id: str = Field(..., pattern="^tc_[a-f0-9]{8}$")
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for test case with results
class TestCaseWithResults(TestCase):
    test_results: List[TestResult] = []

    class Config:
        from_attributes = True 

TestCaseWithResults.model_rebuild()