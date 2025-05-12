from typing import Optional, Union
from uuid import UUID
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import BaseUserManager, UUIDIDMixin, exceptions
from app.models.user import User
from app.db.session import AsyncSessionLocal
from app.core.config import get_settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

settings = get_settings()

engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# User database adapter for FastAPI-Users
async def get_user_db():
    db = AsyncSessionLocal()
    try:
        yield SQLAlchemyUserDatabase(db, User)
    finally:
        await db.close()

# User manager for FastAPI-Users
class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = settings.jwt_secret_key
    verification_token_secret = settings.jwt_secret_key

    async def on_after_register(self, user: User, request=None):
        # You can add custom logic here (e.g., send welcome email)
        pass

    async def validate_password(self, password: str, user: Union[User, None] = None) -> None:
        if len(password) < 8:
            raise exceptions.InvalidPasswordException(reason="Password should be at least 8 characters")
        # Add more password validation as needed

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db) 