from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    app_name: str = Field("EvaluationBackend", env="APP_NAME")
    app_env: str = Field("development", env="APP_ENV")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    database_url: str = Field(..., env="DATABASE_URL")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expires: int = Field(3600, env="JWT_ACCESS_TOKEN_EXPIRES")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    email_whitelist: List[str] = Field(default_factory=list, env="EMAIL_WHITELIST")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def parsed_email_whitelist(self) -> List[str]:
        # Parse comma-separated emails into a list
        return [e.strip() for e in self.email_whitelist] if self.email_whitelist else []

@lru_cache()
def get_settings() -> Settings:
    return Settings()
