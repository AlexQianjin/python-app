from fastapi.testclient import TestClient

from app.main import app


def test_user_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/users" in paths
    assert "/api/users/{user_id}" in paths


def test_user_routes_require_authentication(healthy_database: None) -> None:
    response = TestClient(app).get("/api/users")

    assert response.status_code == 401
