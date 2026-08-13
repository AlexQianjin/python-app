from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User


async def list_users(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: str | None,
) -> tuple[list[User], int]:
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                User.name.ilike(term),
                User.email.ilike(term),
                User.role.ilike(term),
            )
        )

    total = await session.scalar(select(func.count(User.id)).where(*filters)) or 0
    users = await session.scalars(
        select(User)
        .where(*filters)
        .order_by(User.name, User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(users), total


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def add_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def save_user(session: AsyncSession, user: User) -> User:
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()
