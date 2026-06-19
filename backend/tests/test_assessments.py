from conftest import auth_headers


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def employee_h(client):
    return auth_headers(client, "employee@test.com", "Employee@123")


def _make_assessment(client, headers, training_id):
    return client.post(
        "/api/assessments",
        json={
            "training_id": training_id,
            "title": "Quiz",
            "passing_marks": 2,
            "questions": [
                {"question_text": "2+2?", "question_type": "mcq", "options": ["3", "4"], "correct_answer": "4", "marks": 1, "order_index": 0},
                {"question_text": "Capital of France?", "question_type": "short", "correct_answer": "Paris", "marks": 1, "order_index": 1},
                {"question_text": "len fn?", "question_type": "short", "correct_answer": "len", "marks": 1, "order_index": 2},
            ],
        },
        headers=headers,
    )


def _setup(client, seeded):
    """Trainer training with assessment; employee enrolled. Returns (tid, aid)."""
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "Course"}, headers=th).json()["id"]
    client.post(f"/api/trainings/{tid}/enrollments", json={"user_ids": [seeded["employee"].id]}, headers=th)
    aid = _make_assessment(client, th, tid).json()["id"]
    return tid, aid


def test_create_assessment_computes_total_marks(client, seeded):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "C"}, headers=th).json()["id"]
    r = _make_assessment(client, th, tid)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_marks"] == 3
    assert body["question_count"] == 3


def test_employee_cannot_create_assessment(client, seeded):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "C"}, headers=th).json()["id"]
    r = _make_assessment(client, employee_h(client), tid)
    assert r.status_code == 403


def test_questions_hide_answer_key(client, seeded):
    _, aid = _setup(client, seeded)
    r = client.get(f"/api/assessments/{aid}/questions", headers=employee_h(client))
    assert r.status_code == 200
    assert all("correct_answer" not in q for q in r.json())


def test_submit_autograde_pass(client, seeded):
    _, aid = _setup(client, seeded)
    r = client.post(
        f"/api/assessments/{aid}/submit",
        json={"answers": {}, "time_taken_seconds": 120},
        headers=employee_h(client),
    )
    # Need question ids to answer; fetch them first.
    qs = client.get(f"/api/assessments/{aid}/questions", headers=employee_h(client)).json()
    answers = {str(qs[0]["id"]): "4", str(qs[1]["id"]): "paris", str(qs[2]["id"]): "LEN"}
    r = client.post(
        f"/api/assessments/{aid}/submit",
        json={"answers": answers, "time_taken_seconds": 90},
        headers=employee_h(client),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["score"] == 3 and body["max_score"] == 3
    assert body["result"] == "pass"


def test_submit_fail_below_passing(client, seeded):
    _, aid = _setup(client, seeded)
    qs = client.get(f"/api/assessments/{aid}/questions", headers=employee_h(client)).json()
    answers = {str(qs[0]["id"]): "3", str(qs[1]["id"]): "wrong", str(qs[2]["id"]): "nope"}
    r = client.post(f"/api/assessments/{aid}/submit", json={"answers": answers}, headers=employee_h(client))
    assert r.status_code == 201
    assert r.json()["score"] == 0 and r.json()["result"] == "fail"


def test_submit_requires_enrollment(client, seeded):
    # admin creates assessment on own training; employee NOT enrolled.
    ah = admin_h(client)
    tid = client.post("/api/trainings", json={"title": "Locked"}, headers=ah).json()["id"]
    aid = _make_assessment(client, ah, tid).json()["id"]
    r = client.post(f"/api/assessments/{aid}/submit", json={"answers": {}}, headers=employee_h(client))
    assert r.status_code == 403


def test_admin_deletes_assessment_with_results(client, seeded):
    _, aid = _setup(client, seeded)
    # Create a result so we exercise the dependent-row cleanup.
    qs = client.get(f"/api/assessments/{aid}/questions", headers=employee_h(client)).json()
    client.post(f"/api/assessments/{aid}/submit", json={"answers": {str(qs[0]["id"]): "4"}}, headers=employee_h(client))
    r = client.delete(f"/api/assessments/{aid}", headers=admin_h(client))
    assert r.status_code == 200
    assert client.get(f"/api/assessments/{aid}", headers=admin_h(client)).status_code == 404


def test_employee_cannot_delete_assessment(client, seeded):
    _, aid = _setup(client, seeded)
    assert client.delete(f"/api/assessments/{aid}", headers=employee_h(client)).status_code == 403


def test_results_visible_to_staff_and_self(client, seeded):
    _, aid = _setup(client, seeded)
    qs = client.get(f"/api/assessments/{aid}/questions", headers=employee_h(client)).json()
    client.post(
        f"/api/assessments/{aid}/submit",
        json={"answers": {str(qs[0]["id"]): "4"}},
        headers=employee_h(client),
    )
    # Staff sees results for the assessment.
    r = client.get(f"/api/assessments/{aid}/results", headers=trainer_h(client))
    assert r.status_code == 200 and len(r.json()) == 1
    # Employee sees own results.
    r = client.get("/api/assessments/me/results", headers=employee_h(client))
    assert r.status_code == 200 and len(r.json()) == 1
    # Employee cannot see the staff results endpoint.
    assert client.get(f"/api/assessments/{aid}/results", headers=employee_h(client)).status_code == 403
