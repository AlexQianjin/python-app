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
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    ai_document_collection: str = "ai_documents_v2"
    ai_storage_path: str = "./data/uploads"
    ai_max_upload_bytes: int = Field(default=20_000_000, ge=1)
    ai_embedding_model: str = "BAAI/bge-m3"
    ai_model: str = "gpt-4o-mini"
    ai_model_api_key: str | None = None
    ai_model_base_url: str | None = None
    ai_memory_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
