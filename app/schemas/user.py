from pydantic import EmailStr
from uuid import UUID
from datetime import datetime
from fastapi_users import schemas

class UserRead(schemas.BaseUser[UUID]):
    email: EmailStr
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str

class UserUpdate(schemas.BaseUserUpdate):
    pass 