# Medical Patient Registration — MVP Demo

A production-minded async REST API + mobile-first web UI for patient registration and appointment booking.

**Stack:** FastAPI · SQLAlchemy 2.0 · PostgreSQL · JWT auth · bcrypt · zero-dependency frontend

---

## One-command demo

```bash
docker compose up --build
```

Open **http://localhost:8000** — that's it.

Verification codes are printed to the Docker log (no mail server needed in demo mode):

```bash
docker compose logs api   # look here for verification codes
```

> The `.env` file is pre-filled with demo values. If it doesn't exist, copy `.env.example`:
> ```bash
> cp .env.example .env
> docker compose up --build
> ```

### Reset / clean start

If you see `InvalidPasswordError` on startup (stale Postgres volume from a previous run), wipe the DB volume and restart:

```bash
docker compose down -v   # stops containers AND removes the pgdata volume
docker compose up --build
```

> ⚠️ `-v` permanently deletes all data in the database. Use only for a clean demo reset.

---

## How to use the demo

1. Open http://localhost:8000
2. Click **Register** → enter full name, email, password, and role (`client` or `doctor`)
3. Run `docker compose logs api` → copy the 6-digit code
4. Click **Verify** → paste the code
5. Click **Log in** → you're in

**As a client:**
- Register a patient record
- Browse available doctors (`GET /auth/doctors`)
- Book an appointment — the doctor receives an email notification (logged to console in demo mode)
- View your own appointments

**As a doctor:**
- View all registered patients
- View incoming appointment bookings
- Confirm or cancel appointments

---

## Real email (ukr.net / Gmail)

To send real emails instead of logging to console, set these in `.env`:

**ukr.net (port 465, SSL):**
```env
SMTP_HOST=smtp.ukr.net
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USER=your-address@ukr.net
SMTP_PASSWORD=your-password
SMTP_FROM=your-address@ukr.net
```

**Gmail (port 587, STARTTLS):**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_SSL=false
SMTP_USER=your-address@gmail.com
SMTP_PASSWORD=your-app-password   # generate in Google Account → Security → App passwords
SMTP_FROM=your-address@gmail.com
```

Then restart: `docker compose up --build`

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
| `GET` | `/health` | Liveness probe (Docker healthcheck / load balancer) |

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
| `doctor` | List all patients · Read any patient · View incoming appointments · Confirm/cancel appointments |
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

> **Note on 403 vs 401:** Unauthenticated requests return `403` (not `401`). This is FastAPI's `HTTPBearer` behavior — it returns 403 when no `Authorization` header is present. The tests correctly assert `403`.

---

## Project structure

```
app/
  config.py               — env vars (DATABASE_URL, JWT_SECRET, SMTP, rate limiting)
  database.py             — async SQLAlchemy engine + connection pool config
  models.py               — User, Patient, Appointment, AuditLog
  schemas.py              — Pydantic request/response schemas
  auth.py                 — JWT decode, get_current_user, require_role()
  auth_router.py          — /auth/* endpoints
  auth_service.py         — register, verify, login, forgot/reset password
  auth_repository.py      — user DB queries
  appointment_router.py   — /appointments/* endpoints
  appointment_service.py  — booking logic + doctor notification
  appointment_repository.py — appointment DB queries
  email_sender.py         — SMTP (SSL + STARTTLS) or console-log fallback
  router.py               — /patients/* endpoints
  service.py              — patient business logic + audit log
  repository.py           — patient DB queries
  main.py                 — app factory, middleware, rate limiter, health endpoint
frontend/
  index.html              — single-file mobile-first UI
tests/
  conftest.py             — async test client, register_and_login helper
  test_patients.py        — 35 tests
.env                      — pre-filled demo config
.env.example              — template with all options documented
docker-compose.yml        — postgres + api with healthchecks and restart policy
Dockerfile
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(set)* | PostgreSQL async URL |
| `JWT_SECRET` | `demo-secret-…` | **Change this** for production |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime |
| `SMTP_HOST` | *(empty)* | Leave empty → codes logged to console |
| `SMTP_PORT` | `587` | SMTP port (465 for SSL, 587 for STARTTLS) |
| `SMTP_USE_SSL` | `false` | `true` for port 465 (ukr.net, Gmail SSL) |
| `SMTP_USER` | *(empty)* | SMTP username |
| `SMTP_PASSWORD` | *(empty)* | SMTP password |
| `SMTP_FROM` | `noreply@example.com` | From address |
| `RATE_LIMIT_AUTH` | `10` | Max auth requests/IP/minute. `0` = disabled |
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
- Rate limiting on auth endpoints (10 req/IP/min, configurable)
- DB errors return a sanitized `{"detail": "Database error"}` — no internals leaked
- Security headers on every response (`X-Content-Type-Options`, `X-Frame-Options`, etc.)
- Docker container runs as **non-root** (`appuser`)
- `.env` is excluded from the Docker image via `.dockerignore`
- Indexed DB fields for common high-load queries

---

## Production hardening (next phase)

1. **Alembic migrations** — replace `create_all` for zero-downtime schema evolution
2. **Redis rate limiting** — replace in-process limiter with `slowapi` + Redis (shared across workers)
3. **TLS termination** — nginx/Caddy in front of uvicorn; never expose uvicorn directly
4. **Async email queue** — Arq or Celery for reliable email delivery with retries
5. **Refresh tokens** — `POST /auth/refresh` with longer-lived refresh token
6. **PgBouncer** — connection pooler in transaction mode for national-scale DB load
7. **Read replicas** — separate read/write DB connections for list endpoints
8. **Structured logging + metrics** — JSON logs, Prometheus/OpenTelemetry, Grafana dashboards
9. **Patient search** — full-text search by name/DOB for doctors
10. **Admin role** — user management, audit log viewer, system health dashboard

See [REVIEW.md](REVIEW.md) for the full engineering review.
