from conftest import auth_headers


def admin_h(client):
    return auth_headers(client, "admin@test.com", "Admin@123")


def trainer_h(client):
    return auth_headers(client, "trainer@test.com", "Trainer@123")


def employee_h(client):
    return auth_headers(client, "employee@test.com", "Employee@123")


# --- Departments ---

def test_department_crud_admin(client, seeded):
    h = admin_h(client)
    r = client.post("/api/departments", json={"name": "QA", "description": "Quality"}, headers=h)
    assert r.status_code == 201, r.text
    dept_id = r.json()["id"]

    r = client.patch(f"/api/departments/{dept_id}", json={"description": "QA team"}, headers=h)
    assert r.status_code == 200
    assert r.json()["description"] == "QA team"

    r = client.get("/api/departments", headers=h)
    assert r.status_code == 200 and any(d["id"] == dept_id for d in r.json())

    r = client.delete(f"/api/departments/{dept_id}", headers=h)
    assert r.status_code == 200


def test_department_duplicate_name_409(client, seeded):
    h = admin_h(client)
    client.post("/api/departments", json={"name": "Dup"}, headers=h)
    r = client.post("/api/departments", json={"name": "Dup"}, headers=h)
    assert r.status_code == 409


def test_department_write_forbidden_for_employee(client, seeded):
    r = client.post("/api/departments", json={"name": "X"}, headers=employee_h(client))
    assert r.status_code == 403


def test_department_requires_auth(client, seeded):
    assert client.get("/api/departments").status_code == 401


# --- Users ---

def test_user_create_and_pagination(client, seeded):
    h = admin_h(client)
    r = client.post(
        "/api/users",
        json={
            "employee_code": "NEW1",
            "name": "New Person",
            "email": "new@test.com",
            "password": "Passw0rd!",
            "role": "employee",
        },
        headers=h,
    )
    assert r.status_code == 201, r.text

    r = client.get("/api/users?page=1&size=2", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"items", "total", "page", "size", "pages"}
    assert body["size"] == 2 and len(body["items"]) <= 2

    r = client.get("/api/users?role=trainer", headers=h)
    assert all(u["role"] == "trainer" for u in r.json()["items"])

    r = client.get("/api/users?search=New", headers=h)
    assert any(u["email"] == "new@test.com" for u in r.json()["items"])


def test_user_duplicate_email_409(client, seeded):
    h = admin_h(client)
    r = client.post(
        "/api/users",
        json={"employee_code": "Z9", "name": "Dup", "email": "admin@test.com", "password": "x12345"},
        headers=h,
    )
    assert r.status_code == 409


def test_user_create_forbidden_for_trainer(client, seeded):
    r = client.post(
        "/api/users",
        json={"employee_code": "T2", "name": "x", "email": "x@test.com", "password": "x12345"},
        headers=trainer_h(client),
    )
    assert r.status_code == 403


# --- Trainings ---

def test_trainer_creates_training_is_owner(client, seeded):
    r = client.post(
        "/api/trainings",
        json={"title": "Intro", "trainer_id": 9999},  # should be ignored/forced to self
        headers=trainer_h(client),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["trainer_id"] == seeded["trainer"].id
    assert body["created_by"] == seeded["trainer"].id


def test_employee_cannot_create_training(client, seeded):
    r = client.post("/api/trainings", json={"title": "Nope"}, headers=employee_h(client))
    assert r.status_code == 403


def test_trainer_cannot_reassign_trainer(client, seeded):
    h = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "T"}, headers=h).json()["id"]
    r = client.patch(f"/api/trainings/{tid}", json={"trainer_id": seeded["admin"].id}, headers=h)
    assert r.status_code == 403


def test_admin_can_assign_trainer(client, seeded):
    h = admin_h(client)
    r = client.post(
        "/api/trainings",
        json={"title": "Assigned", "trainer_id": seeded["trainer"].id},
        headers=h,
    )
    assert r.status_code == 201
    assert r.json()["trainer_id"] == seeded["trainer"].id


# --- Enrollments ---

def test_bulk_enroll_and_remove(client, seeded):
    h = admin_h(client)
    tid = client.post("/api/trainings", json={"title": "Enroll Me"}, headers=h).json()["id"]
    r = client.post(
        f"/api/trainings/{tid}/enrollments",
        json={"user_ids": [seeded["employee"].id, seeded["employee"].id]},  # dup ignored
        headers=h,
    )
    assert r.status_code == 201
    assert len(r.json()) == 1  # de-duped

    r = client.get(f"/api/trainings/{tid}/enrollments", headers=h)
    assert len(r.json()) == 1

    r = client.delete(f"/api/trainings/{tid}/enrollments/{seeded['employee'].id}", headers=h)
    assert r.status_code == 200


# --- Sessions ---

def test_trainer_creates_session_on_own_training(client, seeded):
    h = trainer_h(client)
    tid = client.post("/api/trainings", json={"title": "Owned"}, headers=h).json()["id"]
    r = client.post(
        "/api/sessions",
        json={"training_id": tid, "title": "S1", "session_date": "2026-01-10", "mode": "online"},
        headers=h,
    )
    assert r.status_code == 201, r.text


def test_trainer_cannot_create_session_on_others_training(client, seeded):
    # Admin owns this training; the trainer is not its owner.
    admin = admin_h(client)
    tid = client.post("/api/trainings", json={"title": "Admins"}, headers=admin).json()["id"]
    r = client.post(
        "/api/sessions",
        json={"training_id": tid, "title": "S", "session_date": "2026-01-10"},
        headers=trainer_h(client),
    )
    assert r.status_code == 403
