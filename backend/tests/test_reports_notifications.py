from conftest import auth_headers


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def employee_h(client):
    return auth_headers(client, "employee@test.com", "Employee@123")


# --- Reports ---

def test_org_report_admin_only(client, seeded):
    r = client.get("/api/reports/org", headers=admin_h(client))
    assert r.status_code == 200
    body = r.json()
    assert body["total_users"] >= 3
    assert "trainings_by_status" in body
    # Forbidden for non-admin.
    assert client.get("/api/reports/org", headers=trainer_h(client)).status_code == 403


def test_trainer_report_self_or_admin(client, seeded):
    tid = seeded["trainer"].id
    assert client.get(f"/api/reports/trainer/{tid}", headers=trainer_h(client)).status_code == 200
    assert client.get(f"/api/reports/trainer/{tid}", headers=admin_h(client)).status_code == 200
    # Employee cannot view a trainer report.
    assert client.get(f"/api/reports/trainer/{tid}", headers=employee_h(client)).status_code == 403


def test_employee_report_self_or_admin(client, seeded):
    eid = seeded["employee"].id
    assert client.get(f"/api/reports/employee/{eid}", headers=employee_h(client)).status_code == 200
    assert client.get(f"/api/reports/employee/{eid}", headers=admin_h(client)).status_code == 200
    # Another employee's report is forbidden for the trainer here (not admin/self).
    assert client.get(f"/api/reports/employee/{eid}", headers=trainer_h(client)).status_code == 403


# --- Notifications (event-driven) ---

def test_enrollment_creates_notification(client, seeded):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "Notify"}, headers=th).json()["id"]
    client.post(
        f"/api/trainings/{tid}/enrollments",
        json={"user_ids": [seeded["employee"].id]},
        headers=th,
    )
    r = client.get("/api/notifications", headers=employee_h(client))
    assert r.status_code == 200
    notes = r.json()
    assert any(n["type"] == "enrollment" for n in notes)


def test_mark_read_and_read_all(client, seeded):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "N2"}, headers=th).json()["id"]
    client.post(f"/api/trainings/{tid}/enrollments", json={"user_ids": [seeded["employee"].id]}, headers=th)
    # Create an assessment too -> second notification.
    client.post(
        "/api/assessments",
        json={"training_id": tid, "title": "Quiz", "questions": [{"question_text": "q", "question_type": "short", "correct_answer": "a"}]},
        headers=th,
    )
    eh = employee_h(client)
    notes = client.get("/api/notifications?unread_only=true", headers=eh).json()
    assert len(notes) >= 2

    first_id = notes[0]["id"]
    assert client.post(f"/api/notifications/{first_id}/read", headers=eh).json()["is_read"] is True

    r = client.post("/api/notifications/read-all", headers=eh)
    assert r.status_code == 200
    assert client.get("/api/notifications?unread_only=true", headers=eh).json() == []


def test_cannot_read_others_notification(client, seeded):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "N3"}, headers=th).json()["id"]
    client.post(f"/api/trainings/{tid}/enrollments", json={"user_ids": [seeded["employee"].id]}, headers=th)
    note_id = client.get("/api/notifications", headers=employee_h(client)).json()[0]["id"]
    # Admin trying to mark the employee's notification read -> 404 (not theirs).
    assert client.post(f"/api/notifications/{note_id}/read", headers=admin_h(client)).status_code == 404


# --- LMS stub ---

def test_lms_sync_admin_only(client, seeded):
    r = client.post("/api/integrations/lms/sync", headers=admin_h(client))
    assert r.status_code == 200
    body = r.json()
    assert body["course_count"] == len(body["courses"]) >= 1
    assert client.post("/api/integrations/lms/sync", headers=employee_h(client)).status_code == 403
