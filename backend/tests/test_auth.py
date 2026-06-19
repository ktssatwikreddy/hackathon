from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings
from app.core.deps import require_roles
from app.models import UserRole

settings = get_settings()


def test_login_success(client, seeded):
    resp = client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": "Admin@123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "admin@test.com"
    assert body["user"]["role"] == "super_admin"


def test_login_wrong_password(client, seeded):
    resp = client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": "nope"}
    )
    assert resp.status_code == 401


def test_login_unknown_email(client, seeded):
    resp = client.post(
        "/api/auth/login", json={"email": "ghost@test.com", "password": "x"}
    )
    assert resp.status_code == 401


def test_me_requires_token(client, seeded):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_token(client, seeded):
    login = client.post(
        "/api/auth/login", json={"email": "trainer@test.com", "password": "Trainer@123"}
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "trainer"


def test_expired_token_rejected(client, seeded):
    expired = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_refresh_flow(client, seeded):
    tokens = client.post(
        "/api/auth/login", json={"email": "employee@test.com", "password": "Employee@123"}
    ).json()
    resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_rejects_access_token(client, seeded):
    """An access token must not be usable as a refresh token (type check)."""
    tokens = client.post(
        "/api/auth/login", json={"email": "employee@test.com", "password": "Employee@123"}
    ).json()
    resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


def test_require_roles_rejects_wrong_role(seeded):
    """Object-level unit test of the RBAC dependency."""
    import pytest
    from fastapi import HTTPException

    dependency = require_roles(UserRole.super_admin)
    # Inner dependency raises 403 for a non-admin user.
    with pytest.raises(HTTPException) as exc:
        dependency(user=seeded["employee"])
    assert exc.value.status_code == 403


def test_require_roles_allows_correct_role(seeded):
    dependency = require_roles(UserRole.super_admin, UserRole.trainer)
    assert dependency(user=seeded["trainer"]) is seeded["trainer"]
