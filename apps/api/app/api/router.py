from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.database import DatabaseSession
from app.modules.auth.router import router as auth_router
from app.modules.orders.router import router as orders_router
from app.modules.products.router import router as products_router
from app.modules.users.router import router as users_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(products_router)
router.include_router(users_router)
router.include_router(orders_router)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["connected", "unavailable"]


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(session: DatabaseSession) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except (OSError, SQLAlchemyError):
        return HealthResponse(database="unavailable")
    return HealthResponse(database="connected")
