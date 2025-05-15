from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    app_name: str = Field("EvaluationBackend", env="APP_NAME")
    app_env: str = Field(os.getenv("APP_ENV", "development"), env="APP_ENV")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    database_url: str = Field(os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/evaluation"), env="DATABASE_URL")
    jwt_secret_key: str = Field(os.getenv("JWT_SECRET_KEY", "your-secret-key"), env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expires: int = Field(int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")), env="JWT_ACCESS_TOKEN_EXPIRES")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    email_whitelist: List[str] = Field(default_factory=list, env="EMAIL_WHITELIST")
    cors_origins: List[str] = Field(["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS")
    test_superuser_email: str = Field(os.getenv("TEST_SUPERUSER_EMAIL", "admin@example.com"), env="TEST_SUPERUSER_EMAIL")
    test_superuser_password: str = Field(os.getenv("TEST_SUPERUSER_PASSWORD", "adminpassword"), env="TEST_SUPERUSER_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in the settings

    @property
    def parsed_email_whitelist(self) -> List[str]:
        # Parse comma-separated emails into a list
        return [e.strip() for e in self.email_whitelist] if self.email_whitelist else []

@lru_cache()
def get_settings() -> Settings:
    return Settings()
