from fastapi import APIRouter
from app.api.v1.endpoints import auth, experiments

router = APIRouter()

# Include authentication and user management routes
router.include_router(auth.router)

# Include experiment routes
router.include_router(
    experiments.router,
    prefix="/experiments",
    tags=["experiments"],
)
