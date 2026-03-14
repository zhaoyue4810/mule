import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.real_admin_auth
def test_admin_login_returns_jwt_token() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/admin/auth/login",
        json={"username": "admin", "password": "xince-admin-2026"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "Bearer"
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"


@pytest.mark.real_admin_auth
def test_admin_endpoint_requires_authorization() -> None:
    client = TestClient(app)
    unauthorized = client.get("/api/admin/config/yaml-status")
    assert unauthorized.status_code == 401

    login = client.post(
        "/api/admin/auth/login",
        json={"username": "admin", "password": "xince-admin-2026"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    authorized = client.get(
        "/api/admin/config/yaml-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert authorized.status_code == 200
    assert "files" in authorized.json()
