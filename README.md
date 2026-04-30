# Medical Patient Registration

A minimal async REST API + web UI for registering and listing patients.
Built with FastAPI, SQLAlchemy 2.0, PostgreSQL, and a zero-dependency mobile-first frontend.

---

## Quick Start (Docker)

**Requirements:** Docker + Docker Compose

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd Medical_System

# 2. Create your environment file
cp .env.example .env
```

Edit `.env` and set real values:

```env
POSTGRES_USER=medical
POSTGRES_PASSWORD=your-strong-password
POSTGRES_DB=medical
DATABASE_URL=postgresql+asyncpg://medical:your-strong-password@db:5432/medical
JWT_SECRET=your-long-random-secret   # python -c "import secrets; print(secrets.token_hex(32))"
```

```bash
# 3. Start everything
docker compose up --build
```

The app is now running at **http://localhost:8000**

Open it in any browser — desktop, tablet, or phone.

---

## Running Locally (without Docker)

**Requirements:** Python 3.12+, a running PostgreSQL instance

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # fill in DATABASE_URL and JWT_SECRET

uvicorn app.main:app --reload
```

App runs at **http://localhost:8000**

---

## Authentication Flow

All `/patients` endpoints require a valid JWT in the `Authorization: Bearer <token>` header.

```
1. Register    POST /auth/register   { email, password, role: "doctor"|"client" }
2. Verify      POST /auth/verify     { email, code }   ← code sent to your email
3. Login       POST /auth/login      { email, password }  →  { access_token }
4. Use token   Authorization: Bearer <access_token>
```

In demo mode (no SMTP configured), the verification code is printed to the server console log.

---

## Roles

| Role | Permissions |
|------|-------------|
| `doctor` | List all patients, read any patient, create patients |
| `client` | Create a patient record, read their own record only |

---

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | — | Register with email + password |
| `POST` | `/auth/verify` | — | Verify email with 6-digit code |
| `POST` | `/auth/login` | — | Login, receive JWT |
| `GET` | `/patients/` | doctor | List patients (paginated) |
| `POST` | `/patients/` | doctor, client | Register a new patient |
| `GET` | `/patients/{id}` | doctor (any), client (own) | Get a patient by UUID |

Interactive docs: **http://localhost:8000/docs**

### Example: full flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dr@clinic.com", "password": "secret123", "role": "doctor"}'

# 2. Verify (get code from server log in demo mode)
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "dr@clinic.com", "code": "123456"}'

# 3. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "dr@clinic.com", "password": "secret123"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}

# 4. Use the token
curl http://localhost:8000/patients/ \
  -H "Authorization: Bearer eyJ..."
```

### Pagination

```bash
GET /patients/?limit=20&offset=0
GET /patients/?limit=20&offset=20
```

---

## Running Tests

```bash
source .venv/bin/activate
pip install pytest==8.3.5 pytest-asyncio==0.25.3 httpx==0.28.1 aiosqlite==0.21.0 greenlet==3.2.2

pytest tests/ -v
```

Tests use an in-memory SQLite database — no Postgres required.

---

## Project Structure

```
app/
  config.py          — env vars (DATABASE_URL, JWT_SECRET, SMTP settings)
  database.py        — async SQLAlchemy engine + session factory
  models.py          — User, Patient, AuditLog ORM models
  schemas.py         — Pydantic request/response schemas
  auth.py            — JWT decode, get_current_user, require_role()
  auth_router.py     — POST /auth/register, /auth/verify, /auth/login
  auth_service.py    — register, verify, login, password hashing, JWT signing
  auth_repository.py — user DB queries
  email_sender.py    — sends verification code (console log or real SMTP)
  repository.py      — patient DB queries
  service.py         — patient business logic + audit log
  router.py          — patient HTTP endpoints
  main.py            — app factory, middleware, exception handlers
frontend/
  index.html         — single-file mobile-first UI
tests/
  conftest.py        — async test client + register_and_login helper
  test_patients.py   — 17 tests covering auth, roles, validation, pagination
```

---

## Security Notes

- **JWT** — sign with a long random `JWT_SECRET`. Tokens expire after `JWT_EXPIRE_MINUTES` (default 60).
- **Passwords** — hashed with bcrypt. Never stored in plain text.
- **Email verification** — accounts cannot log in until the email is verified.
- **Role isolation** — clients can only access their own patient record.
- **Secrets** — never commit `.env`. Excluded from Docker image via `.dockerignore`.
- **TLS** — in production, place nginx or Caddy in front of uvicorn to terminate HTTPS.
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control: no-store` on every response.
- **Non-root container** — Docker image runs as `appuser`, not root.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://user:pass@host/db` |
| `JWT_SECRET` | ✅ | Secret for signing JWTs — use a long random string |
| `JWT_EXPIRE_MINUTES` | — | Token lifetime in minutes (default: 60) |
| `SMTP_HOST` | — | SMTP server hostname. Leave empty for demo/console mode |
| `SMTP_PORT` | — | SMTP port (default: 587) |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
| `SMTP_FROM` | — | From address (default: noreply@example.com) |
| `POSTGRES_USER` | Docker only | PostgreSQL username |
| `POSTGRES_PASSWORD` | Docker only | PostgreSQL password |
| `POSTGRES_DB` | Docker only | PostgreSQL database name |
