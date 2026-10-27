from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.urls import async_database_url

engine = create_async_engine(
    async_database_url(settings.database_url), pool_pre_ping=True
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
