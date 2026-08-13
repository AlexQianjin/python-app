from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_user
from app.dependencies.database import get_session
from app.main import app
from app.modules.auth.schemas import CurrentUser


class HealthySession:
    async def execute(self, _statement: object) -> None:
        return None


class UnavailableSession:
    async def execute(self, _statement: object) -> None:
        raise ConnectionError("database unavailable")


async def override_session() -> AsyncIterator[AsyncSession]:
    yield HealthySession()  # type: ignore[misc]


async def override_unavailable_session() -> AsyncIterator[AsyncSession]:
    yield UnavailableSession()  # type: ignore[misc]


async def override_user() -> CurrentUser:
    return CurrentUser(id="user-1", email="alex@example.com", name="Alex Quinn")


@pytest.fixture(autouse=True)
def reset_dependency_overrides() -> Iterator[None]:
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def healthy_database() -> None:
    app.dependency_overrides[get_session] = override_session


@pytest.fixture
def unavailable_database() -> None:
    app.dependency_overrides[get_session] = override_unavailable_session


@pytest.fixture
def authenticated_user() -> None:
    app.dependency_overrides[require_user] = override_user
