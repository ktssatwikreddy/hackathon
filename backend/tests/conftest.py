"""Shared pytest fixtures: in-memory SQLite + dependency overrides."""
from __future__ import annotations

import os

# Force the mock AI backend for tests regardless of .env (no network calls).
os.environ["MOCK_AI"] = "true"

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import Department, User, UserRole

# A single shared in-memory database for the whole test session.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _reset_schema():
    """Fresh schema for every test — full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(db: Session) -> dict[str, User]:
    """Create one user per role + a department. Returns them by role name."""
    dept = Department(name="Engineering", description="Eng")
    db.add(dept)
    db.flush()

    users = {
        "admin": User(
            employee_code="ADM1",
            name="Admin",
            email="admin@test.com",
            password_hash=hash_password("Admin@123"),
            role=UserRole.super_admin,
            joining_date=date(2021, 1, 1),
        ),
        "trainer": User(
            employee_code="TRN1",
            name="Trainer",
            email="trainer@test.com",
            password_hash=hash_password("Trainer@123"),
            role=UserRole.trainer,
            department_id=dept.id,
        ),
        "employee": User(
            employee_code="EMP1",
            name="Employee",
            email="employee@test.com",
            password_hash=hash_password("Employee@123"),
            role=UserRole.employee,
            department_id=dept.id,
        ),
    }
    db.add_all(users.values())
    db.commit()
    for u in users.values():
        db.refresh(u)
    return users


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
