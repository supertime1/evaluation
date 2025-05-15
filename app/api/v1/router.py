from fastapi import APIRouter
from app.api.v1.endpoints import auth, experiments, runs

router = APIRouter()

# Include authentication and user management routes
router.include_router(auth.router)

# Include experiment routes
router.include_router(
    experiments.router,
    prefix="/experiments",
    tags=["experiments"],
)

# Include run routes
router.include_router(
    runs.router,
    prefix="/runs",
    tags=["runs"],
)