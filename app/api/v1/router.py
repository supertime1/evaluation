from fastapi import APIRouter
from app.api.v1.endpoints import auth

router = APIRouter()

# Include authentication and user management routes
router.include_router(auth.router)
