"""Integration tests for Authentication API endpoints."""

from fastapi.testclient import TestClient

from app.models.user import User


def test_auth_login_endpoint(client: TestClient, clinician_user: User):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": clinician_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == clinician_user.email


def test_auth_login_invalid_password(client: TestClient, clinician_user: User):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": clinician_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_me_authenticated(client: TestClient, clinician_token: str, clinician_user: User):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == clinician_user.email
    assert data["role"] == "clinician"

    # Also test /api/auth/me (unversioned auth prefix)
    resp_auth = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert resp_auth.status_code == 200
    assert resp_auth.json()["email"] == clinician_user.email

    # Also test /api/me (direct alias)
    resp_direct = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert resp_direct.status_code == 200
    assert resp_direct.json()["email"] == clinician_user.email


def test_auth_me_unauthorized(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_auth_logout(client: TestClient, clinician_token: str):
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
