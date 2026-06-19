# Architecture Decisions

Running log of non-obvious choices made while building TAPMS. Each entry: the
decision, the alternatives, and why.

## D1 — Merge `users` and `employees` into a single `users` table
**Decision:** One `users` table holds every person (super admin, trainer,
employee) with a `role` discriminator and the employee profile fields
(`employee_code`, `phone`, `designation`, `joining_date`, `department_id`).
**Why:** The original spec had separate `users` and `employees` tables. Keeping
them split duplicates identity data and creates sync bugs (e.g. a trainer who is
also a learner would exist twice). It also breaks referential integrity: login
authenticates a `user`, but enrollments/attendance/results would point at a
separate `employee` row with no guaranteed link. A single table keeps every FK
(`enrollments.user_id`, `attendance.user_id`, `assessment_results.user_id`)
pointing at the same identity. Mandated by the spec (§4) and adopted here.

## D2 — SQLite by default, not MySQL
**Decision:** `DATABASE_URL=sqlite:///./tapms.db` is the default. The DB layer
(`app/core/database.py`) only adds `check_same_thread=False` for SQLite and is
otherwise dialect-agnostic. Swapping to MySQL/Postgres is a one-line `.env`
change (driver `pymysql` is already in requirements for the Phase 9 switch).
**Why:** Target environment is a fresh Linux VM with nothing pre-installed.
SQLite ships with Python — zero install, single file, instant demo. SQLAlchemy
keeps us portable.

## D3 — Portable enum columns (`native_enum=False`, store value)
**Decision:** Enums render as `VARCHAR + CHECK` and persist the enum *value*
(e.g. `"pass"`, not the member name `pass_`). See `app/models/types.py`.
**Why:** Native DB enums differ between SQLite and MySQL; `VARCHAR+CHECK`
behaves identically across both, smoothing the Phase 9 DB switch. Storing the
value (via `values_callable`) keeps the API contract stable regardless of Python
attribute naming.

## D4 — Pragmatic module layout (`routers/` + `schemas/` + `services/` + `models/`)
**Decision:** Instead of the spec's strict per-feature folders (each with its own
`routes.py`/`schemas.py`/`service.py`/`models.py`), use grouped packages:
`app/models/`, `app/routers/`, `app/schemas/`, `app/services/`.
**Why:** Functionally equivalent, fewer files, easier to navigate for a project
this size. The spec allows "the simplest interpretation that satisfies the
spec." All required routes, schema split (`Create`/`Update`/`Out`), and the
service layer still exist — just organised by layer rather than by feature.

## D5 — Local `create_all` on startup alongside Alembic
**Decision:** `app/main.py` runs `Base.metadata.create_all` on startup in the
`local` environment; Alembic migrations remain the source of truth and are used
for the Phase 9 container start.
**Why:** Lets a developer run `uvicorn` immediately after clone without first
running `alembic upgrade`. `create_all` is a no-op when tables already exist, so
it never conflicts with a migrated database.
