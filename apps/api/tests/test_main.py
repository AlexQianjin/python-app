from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, require_user
from app.database import get_session
from app.main import app


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


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def reset_dependency_overrides() -> Iterator[None]:
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


async def test_root() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


async def test_health() -> None:
    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


async def test_health_when_database_is_unavailable() -> None:
    app.dependency_overrides[get_session] = override_unavailable_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "unavailable"}


async def test_me_requires_authentication() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_me_returns_authenticated_user() -> None:
    app.dependency_overrides[require_user] = override_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/me")
    assert response.status_code == 200
    assert response.json() == {
        "id": "user-1",
        "email": "alex@example.com",
        "name": "Alex Quinn",
    }
