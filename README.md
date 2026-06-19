# TAPMS — Training Attendance & Performance Management System

A full-stack app for centralized training management: attendance, assessments
(with AI generation), AI performance insights, role-based dashboards,
notifications, and reporting.

- **Backend:** FastAPI · SQLAlchemy 2 · Pydantic v2 · Alembic · JWT
- **Frontend:** React 18 · TypeScript · Vite · MUI 5 · TanStack Query · Recharts
- **Database:** SQLite by default (zero-install); switch to MySQL via one env var
- **AI:** Groq via LangChain + LangGraph, with a deterministic **mock fallback**
  so everything runs and demos **without an API key**

---

## Prerequisites

- Python 3.11+ and Node 18+ (for the no-Docker path), **or**
- Docker + Docker Compose (for the containerised path)

No database install is needed — SQLite ships with Python.

---

## Quickstart — no Docker (recommended for a fresh VM)

**Backend** (from `backend/`):

```bash
python -m venv venv
# Windows:  venv\Scripts\activate      |  macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # cp .env.example .env on macOS/Linux
python -m app.seed              # creates tapms.db + demo data, prints logins
uvicorn app.main:app --reload   # http://localhost:8000  (Swagger at /docs)
```

**Frontend** (from `frontend/`):

```bash
npm install
npm run dev                     # http://localhost:5173 (proxies /api to :8000)
```

Open **http://localhost:5173** and log in (see credentials below).

> From the repo root, `./start-backend-dev.ps1` and `./start-frontend.ps1` are
> convenience wrappers for Windows PowerShell.

---

## Quickstart — Docker (MySQL)

```bash
docker compose up --build
```

Brings up MySQL + backend + frontend. The backend runs Alembic migrations on
start and seeds demo data (because `SEED=true` by default). App at
**http://localhost:5173**, API at **http://localhost:8000**.

The only thing that changes the database is `DATABASE_URL` in
`docker-compose.yml` — comment it out to fall back to SQLite.

---

## Seeded login credentials

`python -m app.seed` (and the Docker first boot) print these:

| Role        | Email                    | Password      |
|-------------|--------------------------|---------------|
| Super Admin | `admin@tapms.com`        | `Admin@123`   |
| Trainer     | `trainer1@tapms.com`     | `Trainer@123` |
| Trainer     | `trainer2@tapms.com`     | `Trainer@123` |
| Employees   | `employee1..10@tapms.com`| `Employee@123`|

Each role sees a different sidebar and dashboard.

---

## Environment variables (`backend/.env`)

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./tapms.db` | Swap to `mysql+pymysql://user:pass@host:3306/tapms` for MySQL |
| `JWT_SECRET_KEY` | `change-me-before-production` | Change in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `MOCK_AI` | `true` | `true` = no API key needed; `false` requires `GROQ_API_KEY` |
| `GROQ_API_KEY` | _(empty)_ | Required only when `MOCK_AI=false` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model id |
| `ENVIRONMENT` | `local` | `local` auto-creates tables on boot |

**Using the real Groq backend:** set `MOCK_AI=false` and `GROQ_API_KEY=...` —
no code changes needed.

---

## Testing

```bash
cd backend && pytest          # 51 tests, in-memory SQLite
cd frontend && npm run build  # type-check + production build
```

---

## Project structure

```
backend/
  app/
    core/        config, db, security (JWT), deps (RBAC), audit
    models/      SQLAlchemy models (single merged users table)
    schemas/     Pydantic Create/Update/Out models
    routers/     thin route handlers, one per resource
    services/    business logic + object-level RBAC
    ai/          groq_client (real+mock), assessment_chain, performance_graph
    seed.py      demo data
  alembic/       migrations
  tests/         pytest suite
frontend/
  src/
    api/         axios client + resource calls
    hooks.ts     TanStack Query hooks
    store/       zustand auth store
    components/  StatCard, RoleGuard, ConfirmDialog, charts
    layouts/     AppLayout (role-filtered sidebar)
    pages/        login, dashboards, CRUD, assessments, AI insights, reports…
    routes/      router + ProtectedRoute
docs/            decisions.md, known-gaps.md, API.md, ARCHITECTURE.md
docker-compose.yml
```

---

## Troubleshooting

- **`/api/health` shows `database: unavailable`** — for SQLite this shouldn't
  happen; for MySQL, ensure the DB is up and `DATABASE_URL` is correct.
- **AI endpoints 503 / need a key** — ensure `MOCK_AI=true` (the default) to run
  without Groq.
- **Frontend can't reach the API** — the dev server proxies `/api` to
  `http://localhost:8000`; make sure the backend is running there.
- **Login fails for `*.local` emails** — the seeded domain is `tapms.com`
  (`email-validator` rejects the reserved `.local` TLD).

See `docs/decisions.md` for design rationale and `docs/known-gaps.md` for
intentional limitations.
