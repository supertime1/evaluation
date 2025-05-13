from app.schemas.experiment import (
    Experiment,
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentWithRuns,
)
from app.schemas.run import (
    Run,
    RunCreate,
    RunUpdate,
    RunWithResults,
    RunStatus,
)
from app.schemas.test_case import (
    TestCase,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseWithResults,
    TestCaseType,
)
from app.schemas.test_result import (
    TestResult,
    TestResultCreate,
)

# Update forward references
from pydantic import BaseModel
BaseModel.model_rebuild()
