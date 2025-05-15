from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend, CookieTransport
from app.models.user import User
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.services.user_manager import get_user_manager
from app.core.config import get_settings
from uuid import UUID
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from sqlalchemy import select

settings = get_settings()

SECRET = settings.jwt_secret_key

# JWT strategy
jwt_strategy = JWTStrategy(secret=SECRET, lifetime_seconds=settings.jwt_access_token_expires)

# Authentication backend
cookie_secure = os.getenv("APP_ENV") == "production"

cookie_transport = CookieTransport(cookie_name="auth", 
                                   cookie_max_age=settings.jwt_access_token_expires, 
                                   cookie_secure=cookie_secure)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=lambda: jwt_strategy,
)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

router = APIRouter()

# Register authentication routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

@router.delete("/users/by-email/{email}")
async def delete_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(fastapi_users.current_user(active=True, superuser=True))
) -> dict:
    """
    Delete a user by email. Only superusers can perform this action.
    """
    # Find user by email
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {email} not found")
    
    # Delete the user
    await db.delete(user)
    await db.commit()
    
    return {"message": f"User {email} deleted successfully"} 