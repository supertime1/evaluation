from fastapi import APIRouter
from app.api.v1.endpoints import experiments, runs, test_results, test_cases

api_router = APIRouter()
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(test_results.router, prefix="/test-results", tags=["test-results"])
api_router.include_router(test_cases.router, prefix="/test-cases", tags=["test-cases"]) 