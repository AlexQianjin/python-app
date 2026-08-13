from fastapi import APIRouter

from app.dependencies.auth import AuthenticatedUser
from app.modules.auth.schemas import CurrentUser

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=CurrentUser)
async def me(user: AuthenticatedUser) -> CurrentUser:
    return user
