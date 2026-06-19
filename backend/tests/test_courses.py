from conftest import auth_headers


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def _course_body(trainer_id):
    return {
        "title": "QR Course",
        "category": "Technical",
        "trainer_id": trainer_id,
        "total_sessions": 3,
        "sessions": [
            {"title": "S1", "session_date": "2026-03-01", "start_time": "10:00", "end_time": "12:00", "mode": "offline"},
            {"title": "S2", "session_date": "2026-03-03", "mode": "online"},
            {"title": "S3", "session_date": "2026-03-05", "mode": "hybrid"},
        ],
    }


def test_admin_creates_course_with_sessions(client, seeded):
    r = client.post("/api/courses", json=_course_body(seeded["trainer"].id), headers=admin_h(client))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["trainer_id"] == seeded["trainer"].id
    assert body["total_sessions"] == 3
    assert len(body["sessions"]) == 3
    assert all(s["status"] == "scheduled" for s in body["sessions"])
    # start/end dates span the schedule.
    assert body["start_date"] == "2026-03-01"
    assert body["end_date"] == "2026-03-05"


def test_course_sessions_visible_via_sessions_api(client, seeded):
    tid = client.post("/api/courses", json=_course_body(seeded["trainer"].id), headers=admin_h(client)).json()["id"]
    r = client.get(f"/api/sessions?training_id={tid}", headers=admin_h(client))
    assert r.status_code == 200 and len(r.json()) == 3


def test_non_admin_cannot_create_course(client, seeded):
    r = client.post("/api/courses", json=_course_body(seeded["trainer"].id), headers=trainer_h(client))
    assert r.status_code == 403


def test_course_requires_valid_trainer(client, seeded):
    # employee id is not a trainer -> 422
    body = _course_body(seeded["employee"].id)
    r = client.post("/api/courses", json=body, headers=admin_h(client))
    assert r.status_code == 422


def test_admin_deletes_course_cascades(client, seeded):
    h = admin_h(client)
    tid = client.post("/api/courses", json=_course_body(seeded["trainer"].id), headers=h).json()["id"]
    # Add an enrollment + assessment so deletion must clean dependents.
    client.post(f"/api/trainings/{tid}/enrollments", json={"user_ids": [seeded["employee"].id]}, headers=h)
    client.post(
        "/api/assessments",
        json={"training_id": tid, "title": "Q", "questions": [{"question_text": "x", "question_type": "short", "correct_answer": "y"}]},
        headers=h,
    )
    r = client.delete(f"/api/trainings/{tid}", headers=h)
    assert r.status_code == 200
    assert client.get(f"/api/trainings/{tid}", headers=h).status_code == 404
    # Sessions for the deleted course are gone too.
    assert client.get(f"/api/sessions?training_id={tid}", headers=h).json() == []
