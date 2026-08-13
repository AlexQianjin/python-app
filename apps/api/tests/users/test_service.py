from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import UserNotFoundError
from app.modules.users import repository, service
from app.modules.users.schemas import UserCreate

pytestmark = pytest.mark.asyncio


async def test_list_users_calculates_page_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repository, "list_users", AsyncMock(return_value=([], 201)))

    result = await service.list_users(
        AsyncMock(), page=2, page_size=100, search="alex"
    )

    assert result.total == 201
    assert result.pages == 3
    assert result.page == 2


async def test_get_user_raises_when_user_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repository, "get_user", AsyncMock(return_value=None))

    with pytest.raises(UserNotFoundError):
        await service.get_user(AsyncMock(), user_id=404)


async def test_create_user_normalizes_email(monkeypatch: pytest.MonkeyPatch) -> None:
    add_mock = AsyncMock(side_effect=lambda _session, user: user)
    monkeypatch.setattr(repository, "add_user", add_mock)

    user = await service.create_user(
        AsyncMock(),
        UserCreate(name="Alex Quinn", email="Alex@Example.com", role="admin"),
    )

    assert user.email == "alex@example.com"
