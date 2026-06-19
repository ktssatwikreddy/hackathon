from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings
from conftest import auth_headers

settings = get_settings()


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def employee_h(client):
    return auth_headers(client, "employee@test.com", "Employee@123")


def _course_with_enrolled_employee(client, seeded):
    """Trainer-owned training + session + enrolled employee. Returns (tid, sid)."""
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "QR"}, headers=th).json()["id"]
    sid = client.post(
        "/api/sessions",
        json={"training_id": tid, "title": "S1", "session_date": "2026-04-01"},
        headers=th,
    ).json()["id"]
    client.post(f"/api/trainings/{tid}/enrollments", json={"user_ids": [seeded["employee"].id]}, headers=th)
    return tid, sid


# --- P3: QR generation ---

def test_trainer_generates_qr(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    r = client.post(f"/api/sessions/{sid}/qr", headers=trainer_h(client))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["token"] and body["session_id"] == sid
    assert body["qr_png_base64"].startswith("data:image/png;base64,")
    assert f"/attend/{body['token']}" in body["checkin_url"]


def test_end_session_sets_status(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    r = client.post(f"/api/sessions/{sid}/end", headers=trainer_h(client))
    assert r.status_code == 200 and r.json()["status"] == "ended"


def test_qr_generation_forbidden_for_other_trainer(client, seeded):
    # Admin owns this session; trainer is not the owner.
    ah = admin_h(client)
    tid = client.post("/api/trainings", json={"title": "AdminOwned"}, headers=ah).json()["id"]
    sid = client.post("/api/sessions", json={"training_id": tid, "title": "S", "session_date": "2026-04-01"}, headers=ah).json()["id"]
    assert client.post(f"/api/sessions/{sid}/qr", headers=trainer_h(client)).status_code == 403


def test_get_and_revoke_qr(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    th = trainer_h(client)
    client.post(f"/api/sessions/{sid}/qr", headers=th)
    assert client.get(f"/api/sessions/{sid}/qr", headers=th).status_code == 200
    assert client.delete(f"/api/sessions/{sid}/qr", headers=th).status_code == 200
    # After revoke, no active QR.
    assert client.get(f"/api/sessions/{sid}/qr", headers=th).status_code == 404


def test_generate_rotates_previous_token(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    th = trainer_h(client)
    first = client.post(f"/api/sessions/{sid}/qr", headers=th).json()["token"]
    client.post(f"/api/sessions/{sid}/qr", headers=th)  # rotate
    # The old token is now inactive -> check-in with it is rejected (410).
    r = client.post("/api/attendance/checkin", json={"token": first}, headers=employee_h(client))
    assert r.status_code == 410


# --- P4: check-in ---

def test_employee_checkin_marks_present(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    token = client.post(f"/api/sessions/{sid}/qr", headers=trainer_h(client)).json()["token"]
    r = client.post("/api/attendance/checkin", json={"token": token}, headers=employee_h(client))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "present" and body["already_marked"] is False
    # Reflected in the employee's own attendance.
    mine = client.get("/api/attendance/me", headers=employee_h(client)).json()
    assert any(a["session_id"] == sid and a["status"] == "present" for a in mine)


def test_checkin_is_idempotent(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    token = client.post(f"/api/sessions/{sid}/qr", headers=trainer_h(client)).json()["token"]
    eh = employee_h(client)
    client.post("/api/attendance/checkin", json={"token": token}, headers=eh)
    r = client.post("/api/attendance/checkin", json={"token": token}, headers=eh)
    assert r.status_code == 200 and r.json()["already_marked"] is True


def test_checkin_rejects_non_enrolled(client, seeded):
    # Build a training the employee is NOT enrolled in.
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "Locked"}, headers=th).json()["id"]
    sid = client.post("/api/sessions", json={"training_id": tid, "title": "S", "session_date": "2026-04-01"}, headers=th).json()["id"]
    token = client.post(f"/api/sessions/{sid}/qr", headers=th).json()["token"]
    r = client.post("/api/attendance/checkin", json={"token": token}, headers=employee_h(client))
    assert r.status_code == 403


def test_checkin_rejects_expired_token(client, seeded):
    _, sid = _course_with_enrolled_employee(client, seeded)
    # Craft an already-expired attendance token (no DB row -> would be 410, but
    # expiry is checked first by decode -> 400).
    expired = jwt.encode(
        {"sub": str(sid), "type": "attendance", "jti": "x", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    r = client.post("/api/attendance/checkin", json={"token": expired}, headers=employee_h(client))
    assert r.status_code == 400


def test_checkin_rejects_non_attendance_token(client, seeded):
    # A normal access token must not work as a QR token.
    login = client.post("/api/auth/login", json={"email": "employee@test.com", "password": "Employee@123"}).json()
    r = client.post("/api/attendance/checkin", json={"token": login["access_token"]}, headers=employee_h(client))
    assert r.status_code == 400
