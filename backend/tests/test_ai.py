from conftest import auth_headers


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def employee_h(client):
    return auth_headers(client, "employee@test.com", "Employee@123")


def _trainer_training(client, seeded, enroll_employee=True):
    th = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "AI Course"}, headers=th).json()["id"]
    if enroll_employee:
        client.post(
            f"/api/trainings/{tid}/enrollments",
            json={"user_ids": [seeded["employee"].id]},
            headers=th,
        )
    return tid


def test_generate_assessment_persists_questions(client, seeded):
    tid = _trainer_training(client, seeded)
    r = client.post(
        "/api/ai/generate-assessment",
        json={
            "training_id": tid,
            "material_text": "Python basics: variables, loops, functions.",
            "num_questions": 4,
            "types": ["mcq", "short"],
        },
        headers=trainer_h(client),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["question_count"] == 4
    assert body["total_marks"] == 4
    # Questions actually persisted and fetchable.
    qs = client.get(f"/api/assessments/{body['id']}/questions", headers=trainer_h(client)).json()
    assert len(qs) == 4


def test_generate_assessment_forbidden_for_employee(client, seeded):
    tid = _trainer_training(client, seeded)
    r = client.post(
        "/api/ai/generate-assessment",
        json={"training_id": tid, "material_text": "x", "num_questions": 2},
        headers=employee_h(client),
    )
    assert r.status_code == 403


def test_analyze_performance_shape(client, seeded):
    r = client.post(
        "/api/ai/analyze-performance",
        json={"user_id": seeded["employee"].id},
        headers=admin_h(client),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {
        "user_id",
        "summary",
        "attendance_pct",
        "avg_score",
        "completed_trainings",
        "learning_gaps",
        "skill_areas",
        "recommendations",
    }
    assert isinstance(body["learning_gaps"], list)
    assert isinstance(body["recommendations"], list)
    assert body["summary"]


def test_employee_can_view_only_self(client, seeded):
    # Self: allowed.
    assert client.post(
        "/api/ai/analyze-performance",
        json={"user_id": seeded["employee"].id},
        headers=employee_h(client),
    ).status_code == 200
    # Someone else: forbidden.
    assert client.post(
        "/api/ai/analyze-performance",
        json={"user_id": seeded["admin"].id},
        headers=employee_h(client),
    ).status_code == 403


def test_trainer_can_view_own_trainee(client, seeded):
    _trainer_training(client, seeded, enroll_employee=True)
    r = client.post(
        "/api/ai/analyze-performance",
        json={"user_id": seeded["employee"].id},
        headers=trainer_h(client),
    )
    assert r.status_code == 200


def test_trainer_cannot_view_non_trainee(client, seeded):
    # Employee not enrolled in any of the trainer's trainings.
    r = client.post(
        "/api/ai/analyze-performance",
        json={"user_id": seeded["employee"].id},
        headers=trainer_h(client),
    )
    assert r.status_code == 403
