from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.users.seed import seed_users

pytestmark = pytest.mark.asyncio


async def test_seed_users_creates_200_unique_users() -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=0)
    session.commit = AsyncMock()

    seeded = await seed_users(session)

    assert seeded == 200
    users = session.add_all.call_args.args[0]
    assert len({user.email for user in users}) == 200
    session.commit.assert_awaited_once()


async def test_seed_users_leaves_existing_directory_untouched() -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=1)

    seeded = await seed_users(session)

    assert seeded == 0
    session.add_all.assert_not_called()
