
from fastapi import APIRouter
from app.db.session import get_db
from app.models.run import Run
from app.schemas.run import RunCreate, RunUpdate, RunWithResults
from app.api.v1.endpoints.auth import fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter()


        
# Current user dependency
current_active_user = fastapi_users.current_user(active=True)

