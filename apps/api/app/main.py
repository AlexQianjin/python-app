import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import router as api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import async_session_factory, engine
from app.modules.products.seed import seed_products

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


def create_app() -> FastAPI:
    configure_logging()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(api_router)

    @application.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"message": settings.app_name, "docs": "/docs"}

    return application


app = create_app()
