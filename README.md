# Medical Patient Registration — MVP Demo

A production-minded async REST API + mobile-first web UI for patient registration and appointment booking.

**Stack:** FastAPI · SQLAlchemy 2.0 · PostgreSQL · JWT auth · bcrypt · zero-dependency frontend

---

## One-command demo start

```bash
./run-demo.sh
```

Run it from the project root. The script auto-creates `.env` from `.env.example` if needed and starts the full stack.

Open **http://localhost:8000** — that's it.

The `.env` file is pre-filled with demo values. Verification codes are printed to the Docker log (no mail server needed):

```bash
docker compose logs api   # look here for verification codes in demo mode
```

---

## How to use the demo

1. Open http://localhost:8000
2. Click **Register** → enter full name, email, password, and role (`client` or `doctor`)
3. Click **Verify** → paste the 6-digit code from the Docker log
4. Click **Log in** → you're in

**As a client:**
- Register a patient record
- Browse available doctors (`GET /auth/doctors`)
- Book an appointment — the doctor receives an email notification (logged to console in demo mode)
- View your own appointments

**As a doctor:**
- View all registered patients
- View incoming appointment bookings

---

## Authentication flow

```
POST /auth/register      { full_name, email, password, role: "doctor"|"client" }
  → sends 6-digit code to email (valid 15 min)

POST /auth/verify        { email, code }
  → activates the account

POST /auth/login         { email, password }
  → returns { access_token, token_type: "bearer" }

POST /auth/forgot-password  { email }
  → sends reset code (always returns 200 — no email enumeration)

POST /auth/reset-password   { email, code, new_password }
  → updates password
```

All `/patients` and `/appointments` endpoints require:
```
Authorization: Bearer <access_token>
```

---

## API reference

### Auth (public)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register account |
| `POST` | `/auth/verify` | Verify email with 6-digit code |
| `POST` | `/auth/login` | Login → JWT |
| `POST` | `/auth/forgot-password` | Request password reset code |
| `POST` | `/auth/reset-password` | Set new password with reset code |
| `GET` | `/auth/doctors` | List verified doctors (public) |

### Patients (JWT required)

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| `GET` | `/patients/` | doctor | List all patients (paginated) |
| `POST` | `/patients/` | doctor, client | Register a patient |
| `GET` | `/patients/{id}` | doctor (any), client (own) | Get patient by ID |

### Appointments (JWT required)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/appointments/` | Book appointment with a doctor |
| `GET` | `/appointments/` | My appointments (doctor: incoming; client: own), paginated via `limit`/`offset` |
| `PATCH` | `/appointments/{id}/status` | Doctor confirms/cancels assigned appointment |

Interactive docs: **http://localhost:8000/docs**

---

## Roles

| Role | Can do |
|------|--------|
| `doctor` | List all patients · Read any patient · View incoming appointments |
| `client` | Register a patient · Read own patient record · Book appointments · View own appointments |

---

## Running tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest==8.3.5 pytest-asyncio==0.25.3 httpx==0.28.1 aiosqlite==0.21.0 greenlet==3.2.2

pytest tests/ -v
```
**35 tests** — no Postgres required (in-memory SQLite). Covers:
- Registration, email sending (mocked), duplicate/weak-password rejection
- Verification code (correct, wrong, expired)
- Login (success, wrong password, unverified account)
- Password reset full flow + wrong code
- Doctor listing (public, excludes clients)
- Patient CRUD + role enforcement + client data isolation
- Appointment booking + doctor email notification (mocked)
- Appointment booking permission (client-only)
- Appointment double-booking conflict rejection (`409`)
- Appointment status updates (assigned doctor only)
- Past-time appointment rejection
- Unauthenticated access rejection

---

## Project structure

```
app/
  config.py               — env vars (DATABASE_URL, JWT_SECRET, SMTP)
  database.py             — async SQLAlchemy engine + session
  models.py               — User, Patient, Appointment, AuditLog
  schemas.py              — Pydantic request/response schemas
  auth.py                 — JWT decode, get_current_user, require_role()
  auth_router.py          — /auth/* endpoints
  auth_service.py         — register, verify, login, forgot/reset password
  auth_repository.py      — user DB queries
  appointment_router.py   — /appointments/* endpoints
  appointment_service.py  — booking logic + doctor notification
  appointment_repository.py — appointment DB queries
  email_sender.py         — SMTP or console-log fallback
  router.py               — /patients/* endpoints
  service.py              — patient business logic + audit log
  repository.py           — patient DB queries
  main.py                 — app factory, middleware, exception handlers
frontend/
  index.html              — single-file mobile-first UI (login/register/verify/app)
tests/
  conftest.py             — async test client, register_and_login helper
  test_patients.py        — 35 tests
.env                      — pre-filled demo config (one-command start)
docker-compose.yml
Dockerfile
run-demo.sh               — one-command local demo launcher
```

---

## Environment variables

All variables are pre-filled in `.env` for demo use. Change before real production.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(set)* | PostgreSQL async URL |
| `JWT_SECRET` | `demo-secret-…` | **Change this** for production |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime |
| `SMTP_HOST` | *(empty)* | Leave empty → codes logged to console |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | *(empty)* | SMTP username |
| `SMTP_PASSWORD` | *(empty)* | SMTP password |
| `SMTP_FROM` | `noreply@example.com` | From address |
| `POSTGRES_USER` | `medical` | DB username (docker-compose) |
| `POSTGRES_PASSWORD` | `medical_demo_pass` | **Change this** for production |
| `POSTGRES_DB` | `medical` | DB name |

---

## Security notes

- Passwords hashed with **bcrypt** — never stored plain
- Verification and reset codes expire after **15 minutes**
- JWT tokens signed with HS256, configurable expiry
- Clients can only access **their own** patient records
- Only **clients** can book appointments
- Appointment status can be changed only by the **assigned doctor**
- Double-booking guard rejects conflicting doctor slot requests
- DB errors return a sanitized `{"detail": "Database error"}` — no internals leaked
- Security headers on every response (`X-Content-Type-Options`, `X-Frame-Options`, etc.)
- Docker container runs as **non-root** (`appuser`)
- `.env` is excluded from the Docker image via `.dockerignore`
- Indexed DB fields for common high-load queries (`role`, `is_verified`, `owner_id`, appointment lookup fields)

## Production hardening recommendations (next phase)
1. Add rate limiting and bot protection on `/auth/register`, `/auth/login`, `/auth/forgot-password`.
2. Add refresh tokens and token revocation/session management.
3. Replace `create_all` with Alembic migrations for controlled schema evolution.
4. Add structured logging + metrics + tracing (Prometheus/OpenTelemetry) and health/readiness endpoints.
5. Add async task queue (Celery/RQ/Arq) for email and notification retries.
6. Enforce TLS termination + secure cookie/session strategy if browser auth moves away from local storage.
7. Add audit log extension for appointment status transitions and auth-sensitive events.
