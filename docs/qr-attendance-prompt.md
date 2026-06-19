# Build: QR-Code Attendance + Course Scheduling (TAPMS extension)

You are a senior full-stack engineer. Extend the **existing, working TAPMS app**
(FastAPI + SQLite + React 18) with QR-based attendance and admin course
scheduling. This document is the single source of truth. Build in phases, with
working, tested code at every checkpoint. If anything is ambiguous, pick the
simplest interpretation that satisfies the spec and log it in
`docs/decisions.md`.

---

## 0. Context — what already exists (do not rebuild)

The repo is a complete TAPMS app. Read these before starting:

- **Backend** (`backend/app/`): FastAPI, SQLAlchemy 2, Pydantic v2, JWT auth,
  Alembic. A single merged `users` table (roles `super_admin|trainer|employee`).
  Models in `models/`, thin routers in `routers/`, logic in `services/`,
  Pydantic schemas in `schemas/`. RBAC via `core/deps.py::require_roles` (route
  level) + service-layer object checks (e.g. `training_service.assert_training_access`).
- Relevant existing models: `Training` (the "course": has `trainer_id`,
  `department_id`, `status`), `TrainingSession` (`training_id`, `title`,
  `session_date`, `start_time`, `end_time`, `location`, `mode`,
  `meeting_link`), `Enrollment` (`user_id`, `training_id`), `Attendance`
  (`session_id`, `user_id`, `status`, `marked_by`, `notes`, UNIQUE(session_id,user_id)).
- JWT helpers in `core/security.py` (`_create_token`, `decode_token`, token
  `type` claim). Audit via `core/audit.py::audit_log`.
- Seed in `app/seed.py`; tests in `tests/` (currently 51 passing — keep them green).
- **Frontend** (`frontend/src/`): React 18, MUI 5, React Router 6, TanStack
  Query (`hooks.ts`), zustand auth (`store/auth.ts`), axios client with refresh
  (`api/client.ts`), resource calls in `api/resources.ts`, role-filtered sidebar
  in `layouts/AppLayout.tsx`, routes in `routes/router.tsx`.

**Terminology:** in this spec a "course" IS the existing `Training`. Do not add
a parallel table — extend `Training`/`TrainingSession`.

---

## 1. New scope (exactly this — no extra features)

1. **Admin course scheduling.** A super admin creates a course in one flow:
   name (+ description/category/department), assigns a trainer from the list of
   available trainers, sets the **total number of sessions**, and the
   **schedule** (date + start/end time + location/mode per session). This
   creates one `Training` plus its `TrainingSession` rows in a single request.
2. **Trainer "End Session" → QR generation.** A trainer logs in, sees the
   courses they are assigned to, opens a course's sessions, and clicks **End
   Session** on a session to generate a time-limited QR code for attendance.
3. **Student self-check-in by scanning.** The QR encodes a URL on our platform.
   The student opens it with their phone camera, logs in (if not already), and
   their attendance for that session is marked **present**. Re-scanning is
   harmless (idempotent).

---

## 2. Constraints (hard)

- **Build on the existing code.** Reuse models, services, schemas, RBAC, JWT,
  and the frontend stack. Do not introduce a new auth system or DB.
- **SQLite stays the default; `MOCK_AI=true` stays the default.** No new
  mandatory external services.
- **Do not break existing tests.** `cd backend && pytest` must stay green; add
  new tests for every new feature (happy path + an auth/permission failure +
  an expiry/edge case).
- **Type everything** (no bare `Any`/`any` except JSON boundaries). Thin routers,
  logic in services. Every write route calls `audit_log(...)`.
- **Conventional commits, one logical commit per phase.** After each phase, post
  a short checkpoint: files changed, how to verify, decisions logged.
- **No secrets in committed files.** Never put a real API key in `.env.example`.

---

## 3. Data model changes

Add via a new Alembic migration (do not edit the initial one). Keep enums
portable (`native_enum=False`, store the value) like `models/types.py`.

1. **`Training.total_sessions`** — `int | None` (nullable). The intended number
   of sessions when the course was scheduled (actual sessions live in
   `training_sessions`). Optional; informational.
2. **`TrainingSession.status`** — enum `scheduled|ended|cancelled`, default
   `scheduled`. "End Session" sets it to `ended`.
3. **New table `attendance_tokens`** (audit/observability of issued QRs;
   the token value itself is a signed JWT, see §5):
   - `id`, `session_id` (FK), `jti` (unique), `created_by` (FK users),
     `expires_at` (datetime), `is_active` (bool, default true),
     `created_at`. Index on `session_id`.
   > Rationale: lets a trainer invalidate/rotate a session's active token and
   > lets check-in reject revoked tokens. If you prefer a pure-stateless JWT
   > with no table, document the trade-off in `decisions.md` — but then you
   > cannot revoke a leaked QR before expiry, so the table is preferred.

Update `app/seed.py` only if needed to keep the demo coherent (e.g. set
`total_sessions`). Keep it idempotent.

---

## 4. API surface (additions, all under `/api`)

```
# Admin course scheduling
POST   /courses                      # admin: create Training + N sessions in one call
       body: { title, description?, category?, department_id?, trainer_id,
               total_sessions, sessions: [ { title, session_date, start_time?,
               end_time?, location?, mode?, meeting_link? }, ... ] }
       -> returns the created course with its sessions

# Trainer QR lifecycle (object-level: trainer must own the session's training)
POST   /sessions/{id}/end            # mark session ended
POST   /sessions/{id}/qr             # generate (or rotate) the attendance QR for a session
       -> { token, checkin_url, qr_png_base64, expires_at }
GET    /sessions/{id}/qr             # fetch the current active QR (if any/not expired)
DELETE /sessions/{id}/qr             # revoke the active token

# Student self check-in
POST   /attendance/checkin           # body: { token }   (requires the student's Bearer auth)
       -> { status: "present", session_id, training_title, already_marked: bool }
```

- `/courses` and the bulk-session create should reuse `training_service` /
  `session_service` internals; validate `trainer_id` is actually a trainer.
- `/sessions/{id}/qr` (POST/GET/DELETE) and `/sessions/{id}/end`:
  `require_roles(super_admin, trainer)` + `assert_training_access`.
- `/attendance/checkin`: any authenticated user; logic enforces enrollment.
- FastAPI OpenAPI must stay complete and tagged.

---

## 5. QR + token security design (get this right)

- **Token = signed JWT** minted with the existing `core/security.py` helpers,
  `type="attendance"`, claims: `sub = session_id`, `jti` (random), `exp`
  (now + `ATTENDANCE_TOKEN_TTL_MINUTES`, default **15**). Persist `jti`,
  `session_id`, `expires_at`, `is_active` in `attendance_tokens`.
- **`checkin_url`** = `{FRONTEND_BASE_URL}/attend/{token}` (config-driven;
  default `http://localhost:5173`). This is what the QR encodes — the phone
  camera opens it directly; no in-app scanner needed.
- **QR image:** render server-side with `qrcode[pil]` (add to
  `requirements.txt`) and return a base64 PNG data URI, plus the raw
  `checkin_url`. (Frontend may also render it from the URL — your choice, but
  the backend must return something displayable.)
- **Check-in validation order** (`/attendance/checkin`):
  1. Decode token; reject if not `type=attendance`, malformed, or expired → 400/410.
  2. Look up `jti` in `attendance_tokens`; reject if missing/`is_active=false` → 410.
  3. Resolve `session_id`; 404 if gone.
  4. Verify the **caller is enrolled** in the session's training → 403 if not.
  5. Upsert `Attendance` (session_id, caller.id): if none, create
     `status=present, marked_by=caller.id, notes="self check-in via QR"`; if it
     already exists, return `already_marked=true` (idempotent **200**, not 409).
  6. `audit_log(action="qr_checkin", ...)`.
- **Rotation:** generating a new QR for a session deactivates the previous
  `jti` (sets `is_active=false`) so only one QR is live at a time.
- Add `ATTENDANCE_TOKEN_TTL_MINUTES` and `FRONTEND_BASE_URL` to `config.py`,
  `.env.example`, and the README env table.

---

## 6. Frontend additions

- **Admin — "Create Course" wizard** (new page, e.g. `pages/CourseCreate.tsx`,
  linked from Trainings or a sidebar item): fields for course meta + trainer
  dropdown (fetched from `/users?role=trainer`) + a dynamic schedule builder
  (set "number of sessions", render that many session rows with date/time/
  location/mode; allow add/remove). Submit → `POST /courses`. Use
  react-hook-form + zod and a TanStack Query mutation; invalidate trainings.
- **Trainer — assigned courses + End Session/QR.** On the training detail
  Sessions tab (`pages/TrainingDetail.tsx`), for trainer-owned trainings add an
  **"End Session & Generate QR"** action per session. Show the returned QR in a
  dialog (image + visible expiry countdown), with **Regenerate** and **Revoke**
  buttons. Trainer's course list = existing Trainings filtered to theirs.
- **Student — check-in landing page** (`pages/Attend.tsx`, route
  `/attend/:token`, NOT inside the authenticated AppLayout shell):
  - If not logged in → redirect to `/login?next=/attend/:token`; after login,
    return here (extend Login to honor `next`).
  - Then call `POST /attendance/checkin { token }` and show a clear success
    ("Attendance marked for <session> ✓"), an "already marked" state, or a
    friendly error (expired/not enrolled).
- Keep MUI styling consistent with the existing theme. Mobile-friendly layout
  for `/attend` (students are on phones).

---

## 7. Phased plan (each phase: runnable + tested + committed)

### Phase 1 — Schema & migration
- Add `Training.total_sessions`, `TrainingSession.status`, `attendance_tokens`
  model + Alembic migration; config additions. Update seed if needed.
- **DoD:** `alembic upgrade head` works on a fresh SQLite DB; `pytest` green;
  `python -m app.seed` still populates.

### Phase 2 — Course scheduling API
- `POST /courses` (admin) creates a training + its sessions atomically;
  validates trainer. Reuse services.
- **DoD:** admin creates a course with 3 sessions in one call; non-admin gets
  403; new tests pass.

### Phase 3 — QR generation API
- `POST/GET/DELETE /sessions/{id}/qr`, `POST /sessions/{id}/end`; `qrcode[pil]`
  rendering; `attendance_tokens` persistence + rotation/revocation.
- **DoD:** trainer who owns the session gets a token+PNG+expiry; another trainer
  gets 403; revoke deactivates; tests cover all.

### Phase 4 — Student check-in API
- `POST /attendance/checkin` with the full validation order in §5; idempotent.
- **DoD:** enrolled student check-in marks present; re-scan returns
  already_marked; expired/revoked token rejected; non-enrolled 403; tests pass.

### Phase 5 — Frontend: admin course wizard
- **DoD:** admin builds and submits a multi-session course from the UI; it
  appears in Trainings; `npm run build` clean.

### Phase 6 — Frontend: trainer End Session + QR display
- **DoD:** trainer ends a session and sees a scannable QR with countdown;
  regenerate/revoke work.

### Phase 7 — Frontend: student `/attend/:token` + login redirect
- **DoD:** scanning the QR on a phone (or opening the URL) logs the student in
  if needed and marks attendance, with clear success/error screens.
  Full demo: admin schedules course → trainer ends session, shows QR → student
  scans → attendance appears in the trainer's session view and the student's
  "My Attendance".

### Phase 8 — Polish
- Update README (new env vars, the QR flow), `docs/decisions.md`,
  `docs/known-gaps.md`, `docs/API.md`. Ensure `pytest` green and `npm run build`
  clean with no warnings.

---

## 8. Acceptance criteria (what I'll check)

1. As **admin**, create a course with a trainer + N scheduled sessions from the
   UI in one flow.
2. As that **trainer**, log in, see the assigned course, open a session, click
   **End Session** → a QR appears (with an expiry).
3. Open the QR's URL on a phone/second browser → prompted to log in as a
   **student** → attendance marked **present** for that exact session.
4. The trainer's session attendance and the student's **My Attendance** both
   reflect it. Re-scanning says "already marked" (no error, no duplicate row).
5. An **expired or revoked** QR is rejected with a clear message; a **non-
   enrolled** user is refused.
6. `pytest` green (old + new). `npm run build` succeeds with no warnings.
7. App still runs with no Docker and with `MOCK_AI=true` (no new mandatory keys).

---

## 9. Things I do NOT want

- A second parallel "course" table — extend `Training`.
- Marking attendance without verifying enrollment and token validity.
- Long-lived or non-revocable QR tokens (default TTL 15 min, rotatable).
- Hard-coded URLs/secrets; put base URL + TTL in config/.env.
- Breaking the existing 51 tests or the no-Docker quickstart.
- A native in-app camera scanner (the phone camera opening the URL is the flow);
  you may add one later as an optional extra, documented in known-gaps.
```
