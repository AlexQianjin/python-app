from math import ceil

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEmailError, UserNotFoundError
from app.modules.users import repository
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserPage, UserUpdate


async def list_users(
    session: AsyncSession, *, page: int, page_size: int, search: str | None
) -> UserPage:
    users, total = await repository.list_users(
        session, page=page, page_size=page_size, search=search
    )
    return UserPage(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


async def get_user(session: AsyncSession, user_id: int) -> User:
    user = await repository.get_user(session, user_id)
    if user is None:
        raise UserNotFoundError
    return user


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    data = payload.model_dump()
    data["email"] = str(payload.email).lower()
    try:
        return await repository.add_user(session, User(**data))
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateEmailError from exc


async def update_user(
    session: AsyncSession, user_id: int, payload: UserUpdate
) -> User:
    user = await get_user(session, user_id)
    data = payload.model_dump()
    data["email"] = str(payload.email).lower()
    for field, value in data.items():
        setattr(user, field, value)
    try:
        return await repository.save_user(session, user)
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateEmailError from exc


async def delete_user(session: AsyncSession, user_id: int) -> None:
    user = await get_user(session, user_id)
    await repository.delete_user(session, user)
