from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend, CookieTransport
from app.models.user import User
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.services.user_manager import get_user_manager
from app.core.config import get_settings
from uuid import UUID
import os

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