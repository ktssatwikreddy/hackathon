from conftest import auth_headers


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def employee_h(client):
    return auth_headers(client, "employee@test.com", "Employee@123")


def _setup_training_with_session(client, seeded):
    """Trainer-owned training + one session + enrolled employee. Returns ids."""
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "Attend"}, headers=th).json()["id"]
    sid = client.post(
        "/api/sessions",
        json={"training_id": tid, "title": "S1", "session_date": "2026-02-01"},
        headers=th,
    ).json()["id"]
    client.post(
        f"/api/trainings/{tid}/enrollments",
        json={"user_ids": [seeded["employee"].id]},
        headers=th,
    )
    return tid, sid


def test_trainer_bulk_marks_attendance(client, seeded):
    _, sid = _setup_training_with_session(client, seeded)
    r = client.post(
        "/api/attendance/bulk",
        json={"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "present"}]},
        headers=trainer_h(client),
    )
    assert r.status_code == 201, r.text
    assert r.json()[0]["status"] == "present"


def test_employee_sees_own_attendance(client, seeded):
    _, sid = _setup_training_with_session(client, seeded)
    client.post(
        "/api/attendance/bulk",
        json={"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "late"}]},
        headers=trainer_h(client),
    )
    r = client.get("/api/attendance/me", headers=employee_h(client))
    assert r.status_code == 200
    mine = r.json()
    assert len(mine) == 1
    assert mine[0]["status"] == "late"
    assert mine[0]["training_title"] == "Attend"


def test_duplicate_attendance_returns_409(client, seeded):
    _, sid = _setup_training_with_session(client, seeded)
    body = {"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "present"}]}
    assert client.post("/api/attendance/bulk", json=body, headers=trainer_h(client)).status_code == 201
    r = client.post("/api/attendance/bulk", json=body, headers=trainer_h(client))
    assert r.status_code == 409


def test_mark_unenrolled_user_422(client, seeded):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "Empty"}, headers=th).json()["id"]
    sid = client.post(
        "/api/sessions",
        json={"training_id": tid, "title": "S", "session_date": "2026-02-01"},
        headers=th,
    ).json()["id"]
    r = client.post(
        "/api/attendance/bulk",
        json={"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "present"}]},
        headers=th,
    )
    assert r.status_code == 422


def test_employee_cannot_mark_attendance(client, seeded):
    _, sid = _setup_training_with_session(client, seeded)
    r = client.post(
        "/api/attendance/bulk",
        json={"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "present"}]},
        headers=employee_h(client),
    )
    assert r.status_code == 403


def test_trainer_cannot_mark_others_session(client, seeded):
    # Admin owns this training/session.
    ah = admin_h(client)
    tid = client.post("/api/trainings", json={"title": "AdminOwned"}, headers=ah).json()["id"]
    sid = client.post(
        "/api/sessions",
        json={"training_id": tid, "title": "S", "session_date": "2026-02-01"},
        headers=ah,
    ).json()["id"]
    client.post(f"/api/trainings/{tid}/enrollments", json={"user_ids": [seeded["employee"].id]}, headers=ah)
    r = client.post(
        "/api/attendance/bulk",
        json={"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "present"}]},
        headers=trainer_h(client),
    )
    assert r.status_code == 403


def test_attendance_percentage_helper(client, seeded, db):
    from app.services.attendance_service import attendance_percentage

    _, sid = _setup_training_with_session(client, seeded)
    client.post(
        "/api/attendance/bulk",
        json={"session_id": sid, "entries": [{"user_id": seeded["employee"].id, "status": "present"}]},
        headers=trainer_h(client),
    )
    pct = attendance_percentage(db, seeded["employee"].id)
    assert pct == 100.0
