from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User

FIRST_NAMES = (
    "Alex",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Jamie",
    "Avery",
    "Cameron",
    "Quinn",
    "Parker",
    "Reese",
    "Rowan",
    "Skyler",
    "Drew",
    "Blake",
    "Emerson",
    "Hayden",
    "Finley",
    "Sage",
)
LAST_NAMES = (
    "Anderson",
    "Bennett",
    "Chen",
    "Diaz",
    "Evans",
    "Foster",
    "Garcia",
    "Hughes",
    "Ivanov",
    "Johnson",
)
ROLES = ("member", "member", "member", "manager", "admin")


async def seed_users(session: AsyncSession, count: int = 200) -> int:
    """Seed an empty managed-user directory with deterministic mock data."""
    existing = await session.scalar(select(func.count(User.id)))
    if existing:
        return 0

    users = []
    for index in range(1, count + 1):
        first_name = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
        last_name = LAST_NAMES[((index - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]
        users.append(
            User(
                name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}@example.com",
                role=ROLES[(index - 1) % len(ROLES)],
                is_active=index % 11 != 0,
            )
        )

    session.add_all(users)
    await session.commit()
    return len(users)
