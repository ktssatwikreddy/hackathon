# TAPMS API

FastAPI serves interactive OpenAPI docs at **`http://localhost:8000/docs`** and
the raw schema at `/openapi.json`. Every router is tagged and every endpoint has
a one-line summary. All non-auth routes require a Bearer access token.

## Auth flow

1. `POST /api/auth/login` `{email, password}` → `{access_token, refresh_token, user}`
2. Send `Authorization: Bearer <access_token>` on subsequent requests.
3. On expiry, `POST /api/auth/refresh` `{refresh_token}` → `{access_token}`.
4. `GET /api/auth/me` returns the current user.

## Endpoint map

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login` · `/auth/refresh` · `/auth/logout` · `/auth/forgot-password` · `/auth/reset-password` · `GET /auth/me` |
| Departments | `GET/POST /departments` · `PATCH/DELETE /departments/{id}` (admin writes) |
| Users | `GET/POST /users` · `GET/PATCH/DELETE /users/{id}` · list filters `?role=&department_id=&search=&page=&size=` |
| Courses | `POST /courses` (admin: create training + scheduled sessions in one call) |
| QR attendance | `POST /sessions/{id}/end` · `POST/GET/DELETE /sessions/{id}/qr` (staff) · `POST /attendance/checkin` (student, body `{token}`) |
| Trainings | `GET/POST /trainings` · `GET/PATCH/DELETE /trainings/{id}` · enrollments: `GET`/bulk `POST /trainings/{id}/enrollments`, `DELETE /trainings/{id}/enrollments/{uid}` |
| Sessions | `GET /sessions?training_id=&from=&to=` · `POST` · `PATCH/DELETE /sessions/{id}` |
| Attendance | `POST /attendance/bulk` · `GET /attendance?session_id=` · `GET /attendance/me` |
| Assessments | `GET/POST /assessments` · `PATCH /assessments/{id}` · `GET/POST /assessments/{id}/questions` · `POST /assessments/{id}/submit` · `GET /assessments/{id}/results` · `GET /assessments/me/results` |
| AI | `POST /ai/generate-assessment` · `POST /ai/analyze-performance` |
| Reports | `GET /reports/org` · `/reports/trainer/{id}` · `/reports/employee/{id}` |
| Notifications | `GET /notifications` · `POST /notifications/{id}/read` · `POST /notifications/read-all` |
| Integrations | `POST /integrations/lms/sync` (stub) |
| Health | `GET /api/health` |

## RBAC summary

- **Super admin:** everything.
- **Trainer:** creates trainings (becomes their owner); manages sessions,
  enrollments, attendance, and assessments **only for trainings they own**; can
  view AI insights for their own trainees.
- **Employee:** views own trainings/attendance/results, takes assessments they
  are enrolled in, and views their own AI insight.

Route-level checks use `require_roles(*roles)`; object-level checks (e.g.
trainer-owns-training) live in the service layer.
