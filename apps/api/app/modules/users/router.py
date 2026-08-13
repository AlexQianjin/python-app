from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import require_user
from app.dependencies.database import DatabaseSession
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserPage, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=UserPage)
async def list_users(
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=320)] = None,
) -> UserPage:
    return await service.list_users(
        session, page=page, page_size=page_size, search=search
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: DatabaseSession) -> User:
    return await service.get_user(session, user_id)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, session: DatabaseSession) -> User:
    return await service.create_user(session, payload)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int, payload: UserUpdate, session: DatabaseSession
) -> User:
    return await service.update_user(session, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: DatabaseSession) -> Response:
    await service.delete_user(session, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
