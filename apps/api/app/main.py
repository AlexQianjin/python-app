import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory, engine, get_session
from app.models import Base
from app.products import router as products_router
from app.seed import seed_products

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with async_session_factory() as session:
            seeded = await seed_products(session)
            if seeded:
                logger.info("Seeded %s products", seeded)
    except (OSError, SQLAlchemyError):
        logger.exception("Database initialization failed; API started without seeding")
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(products_router)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["connected", "unavailable"]


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except (OSError, SQLAlchemyError):
        return HealthResponse(database="unavailable")
    return HealthResponse(database="connected")


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": settings.app_name, "docs": "/docs"}
