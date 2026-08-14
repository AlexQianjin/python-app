from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "React + FastAPI API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    cors_origins: list[str] = ["http://localhost:5173"]
    auth_jwks_url: str = "http://localhost:8001/api/auth/jwks"
    auth_issuer: str = "http://localhost:5173"
    auth_audience: str = "http://localhost:5173"
    redis_url: str | None = None
    product_cache_ttl_seconds: int = Field(default=300, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
