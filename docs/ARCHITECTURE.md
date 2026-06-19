# Architecture

TAPMS is a layered full-stack application.

## Backend (FastAPI)

- **Layering:** `routers` (thin HTTP handlers) → `services` (business logic +
  object-level RBAC) → `models` (SQLAlchemy 2 ORM). `schemas` hold Pydantic v2
  `Create`/`Update`/`Out` models; ORM objects are never returned directly.
- **Identity:** a single merged `users` table holds every person with a `role`
  discriminator (see `docs/decisions.md` D1). All FKs (enrollments, attendance,
  results) point at `users.id`.
- **Auth:** JWT access (15 min) + refresh (7 days) tokens, type-checked on
  decode. `require_roles(*roles)` enforces route-level RBAC; services enforce
  object-level rules (e.g. a trainer may only act on trainings they own).
- **Auditing:** every write route records an `audit_logs` row in the same
  transaction.
- **Database:** SQLAlchemy keeps the app dialect-agnostic. SQLite is the default
  (zero-install); MySQL is a one-line `DATABASE_URL` change. Enums render as
  portable `VARCHAR + CHECK`. Alembic owns the schema; migrations run on
  container start.
- **AI:** `ai/groq_client.py` exposes a `GroqService` Protocol with a real
  (`langchain-groq`) and a deterministic mock implementation, chosen by
  `MOCK_AI`. `assessment_chain.py` is a LangChain prompt→validate→retry pipeline;
  `performance_graph.py` is a LangGraph state machine
  (gather → aggregate → summarize → recommend).

## Frontend (React + Vite)

- TanStack Query owns server state; zustand owns auth (with persistence). An
  axios interceptor injects the bearer token and performs a single silent
  refresh on 401.
- `AppLayout` renders a role-filtered sidebar; `ProtectedRoute`/`RoleGuard`
  gate routes and UI by role. Dashboards and charts read live `/reports` data.

## Deployment

- Multi-stage Docker images (Python wheels for the API; nginx serving the built
  SPA and proxying `/api`). `docker-compose.yml` runs MySQL + backend + frontend.

## Possible future improvements

- Refresh-token rotation/revocation store.
- Manual grading UI for scenario/coding questions.
- Real LMS/HRMS integration clients in place of the stub.
- Background workers for notifications and sync.
