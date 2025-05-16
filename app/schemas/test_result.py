from datetime import datetime
from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field
from deepeval.test_case import MLLMImage
from deepeval.test_run import MetricData

# Base schema with common fields
class TestResultBase(BaseModel):
    name: str
    success: bool
    conversational: bool
    multimodal: Optional[bool] = None
    input: Optional[Union[str, List[Union[str, MLLMImage]]]] = None
    actual_output: Optional[Union[str, List[Union[str, MLLMImage]]]] = None
    expected_output: Optional[str] = None
    context: Optional[List[str]] = None
    retrieval_context: Optional[List[str]] = None
    metrics_data: Optional[List[Dict[str, Any]]] = None
    additional_metadata: Optional[Dict] = None

# Schema for creating a new test result
class TestResultCreate(TestResultBase):
    run_id: str = Field(..., pattern="^run_[a-f0-9]{8}$")
    test_case_id: str = Field(..., pattern="^tc_[a-f0-9]{8}$")

# Schema for test result response
class TestResult(TestResultBase):
    id: str = Field(..., pattern="^tr_[a-f0-9]{8}$")
    run_id: str = Field(..., pattern="^run_[a-f0-9]{8}$")
    test_case_id: str = Field(..., pattern="^tc_[a-f0-9]{8}$")
    executed_at: datetime

    class Config:
        from_attributes = True 