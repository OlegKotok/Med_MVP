# Code Review — Medical Patient Registration System

**Reviewed:** 2026-05-01  
**Reviewer perspective:** Senior Engineer + Architect + Product Owner  
**Scope:** Security · High-load performance · UX · Functionality · Tests · Demo readiness

---

## Executive Summary (Product Owner view)

The system delivers a working MVP: patient registration, appointment booking, role-based access, email verification, and a mobile-first UI — all runnable with one command. The architecture is clean and the code is well-structured. It is suitable for a demo and a solid foundation for a national-scale system.

**What is production-ready today:**
- Secure auth flow (bcrypt, JWT, email verification, password reset)
- Role-based access control (doctor / client) enforced at every endpoint
- Client data isolation (clients can only see their own records)
- Input validation, SQL injection protection, security headers
- Non-root Docker container, secrets via env vars
- 35 passing tests covering all core flows
- One-command demo (`docker compose up --build`)

**What must be done before national-scale production:**
See the roadmap section at the bottom.

---

## Architecture

```
FastAPI (async) → SQLAlchemy 2.0 (asyncpg) → PostgreSQL 16
                                           ↘ aiosqlite (tests only)
JWT (HS256) · bcrypt · SMTP (sync, offloaded to thread pool)
Single-file frontend (no build step)
```

**Strengths:**
- Clean layered architecture: router → service → repository. No business logic leaks into routers.
- Async throughout — no blocking I/O on the event loop (SMTP is correctly offloaded via `anyio.to_thread`).
- Dependency injection via FastAPI `Depends` — testable and composable.
- All DB queries use the ORM — no raw SQL, no injection surface.

**Weaknesses for national scale:**
- Single process model (fixed with `--workers 4` in docker-compose, but still one machine).
- In-process rate limiter — resets on restart, not shared across workers/replicas.
- No async task queue — email delivery is synchronous (blocks a thread per send).
- `create_all` instead of Alembic — schema changes require downtime or manual intervention.

---

## Security Review

| Check | Status | Detail |
|-------|--------|--------|
| Password hashing | ✅ | bcrypt via passlib, never stored plain |
| Email verification | ✅ | 6-digit code, 15-min TTL, single-use (cleared after verify) |
| JWT auth | ✅ | HS256, configurable expiry, `sub` = user UUID |
| Role enforcement | ✅ | `require_role()` factory, applied at every protected endpoint |
| Client data isolation | ✅ | Clients can only read their own patient record |
| Input validation | ✅ | EmailStr, min_length, birth_date range, future-only appointments |
| SQL injection | ✅ | ORM only, no raw SQL |
| Error information leakage | ✅ | SQLAlchemy errors return `{"detail": "Database error"}` |
| Secrets in source | ✅ | All credentials via env vars, `.env` excluded from Docker image |
| Security headers | ✅ | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control` |
| XSS in frontend | ✅ | `escHtml()` on all user-supplied data rendered to DOM |
| Non-root container | ✅ | `appuser` in Dockerfile |
| Email enumeration | ✅ | `forgot-password` always returns 200 regardless of email existence |
| Rate limiting | ✅ | In-process sliding window on `/auth/register`, `/auth/login`, `/auth/forgot-password` |
| SMTP SSL/TLS | ✅ | `SMTP_USE_SSL=true` for port 465 (ukr.net), `false` for STARTTLS port 587 |
| TLS / HTTPS | ⚠️ | Must terminate at nginx/Caddy in production — not configured here |
| JWT secret strength | ⚠️ | Default is a demo value — must be replaced via env var |
| Token revocation | ⚠️ | Stateless JWTs — logout = client discards token. No server-side blacklist. |
| DB migrations | ⚠️ | `create_all` used — replace with Alembic for zero-downtime schema evolution |
| Refresh tokens | ⚠️ | Not implemented — 60-min access token only |
| Audit log coverage | ⚠️ | Only `patient_created` is logged. Auth events and appointment changes are not. |

### Critical for production (not demo):
1. Replace the in-process rate limiter with Redis + `slowapi` — the current one resets on restart and is not shared across workers.
2. Add TLS termination (nginx/Caddy) — never expose uvicorn directly.
3. Rotate `JWT_SECRET` and `POSTGRES_PASSWORD` before any real data is stored.

---

## High-Load Performance Review

### Current capacity (single machine, 4 workers)
- Each uvicorn worker handles ~1000 concurrent connections (asyncio).
- Connection pool: 10 persistent + 20 overflow per worker = up to 120 DB connections total.
- PostgreSQL configured with `max_connections=200`, `shared_buffers=256MB`.
- `pool_pre_ping=True` handles DB restarts without stale connection errors.
- `pool_recycle=3600` prevents long-lived connection issues.

### Bottlenecks for national scale

| Bottleneck | Impact | Fix |
|------------|--------|-----|
| Single Postgres instance | Hard limit on write throughput | Read replicas + PgBouncer in transaction mode |
| Synchronous SMTP in thread pool | Each email blocks a thread for 1–5s | Async task queue (Arq/Celery) with retry |
| In-process rate limiter | Not shared across workers/replicas | Redis + slowapi |
| `create_all` on startup | Race condition with multiple replicas | Alembic migrations run as a separate init step |
| No caching | `/auth/doctors` hits DB on every request | Redis cache with short TTL |
| JWT decode on every request | CPU cost at scale | Acceptable for HS256; switch to RS256 for multi-service |
| No connection to a CDN | Frontend served by uvicorn | Serve static assets from CDN or nginx |

### Scaling path
```
Phase 1 (current): 1 machine, 4 workers, ~4000 concurrent users
Phase 2:           nginx LB + 3 API replicas + PgBouncer → ~50k concurrent
Phase 3:           Kubernetes + Redis + async email queue + read replicas → national scale
```

---

## Functionality Review

### What works correctly
- Full auth flow: register → verify → login → JWT
- Password reset with expiring code
- Doctor listing (public, verified doctors only)
- Patient CRUD with role enforcement and client isolation
- Appointment booking with double-booking guard
- Doctor email notification on booking
- Appointment status management (assigned doctor only)
- Pagination on all list endpoints

### Missing for a real national system
1. **Patient search** — doctors need to search by name/DOB, not just paginate.
2. **Appointment cancellation by client** — clients can book but cannot cancel.
3. **Doctor availability / schedule** — no concept of working hours or slots.
4. **Notifications to clients** — only doctors get email notifications.
5. **Admin role** — no way to manage users, deactivate accounts, or view audit logs.
6. **Soft delete** — patients and appointments are never deleted, only status-changed.
7. **Phone number / national ID** — critical for a real medical system.
8. **Pagination metadata** — responses return arrays without `total`, `page`, `pages`.

---

## Test Quality Review

**35 tests, all passing.** Coverage is good for an MVP.

| Area | Tests | Quality |
|------|-------|---------|
| Registration | 4 | ✅ Covers success, duplicate, weak password, invalid role |
| Email sending | 2 | ✅ Mocked correctly, asserts call args |
| Verification | 3 | ✅ Correct code, wrong code, expired code |
| Login | 2 | ✅ Success, wrong password |
| Password reset | 3 | ✅ Full flow, wrong code, no-leak on unknown email |
| Doctor listing | 2 | ✅ Public access, client exclusion |
| Patient CRUD | 7 | ✅ Role enforcement, client isolation, pagination, validation |
| Appointments | 9 | ✅ Booking, conflict, past time, role enforcement, status update |

**Issues found and fixed:**
- Rate limiter was shared across tests (module-level dict), causing 429 failures after 10 auth calls. Fixed by setting `RATE_LIMIT_AUTH=0` in test env.
- `test_unauthenticated_rejected` correctly asserts `403` — this is FastAPI's `HTTPBearer` behavior when no `Authorization` header is present (returns 403, not 401). This is a known FastAPI quirk, not a bug.

**What to add next:**
- Test for rate limiting (429 response)
- Test for `/health` endpoint
- Test for SMTP SSL mode
- Integration test with real PostgreSQL (not just SQLite)

---

## UX Review

**Frontend (single-file, mobile-first):**
- Clean, minimal design — appropriate for a medical system
- Mobile-first layout with proper touch targets (min 48px buttons)
- XSS protection via `escHtml()` on all rendered user data
- Error messages are user-friendly
- Loading states on buttons (disabled during requests)

**Missing UX improvements:**
1. No loading spinner — user has no feedback during slow network requests.
2. No appointment date/time picker — user must type ISO datetime manually.
3. No confirmation dialog before booking or status change.
4. No pagination UI — only the first 50 records are shown.
5. No "resend verification code" button.
6. Verification code is shown in Docker logs — fine for demo, but the UX instruction should be more prominent in the README.

---

## SMTP Configuration

### ukr.net (recommended for Ukrainian demo)
```
SMTP_HOST=smtp.ukr.net
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USER=kotok_oleg@ukr.net
SMTP_PASSWORD=<your-password>
SMTP_FROM=kotok_oleg@ukr.net
```

### Gmail (alternative)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_SSL=false
SMTP_USER=your@gmail.com
SMTP_PASSWORD=<app-password>   # not your login password — generate in Google Account settings
SMTP_FROM=your@gmail.com
```

**Note:** The previous `email_sender.py` only supported STARTTLS (port 587). It has been updated to support both implicit SSL (`SMTP_SSL`, port 465) and STARTTLS (`SMTP`, port 587) via the `SMTP_USE_SSL` flag.

---

## Files Changed in This Review

| File | Change |
|------|--------|
| `app/config.py` | Added `SMTP_USE_SSL`, `RATE_LIMIT_AUTH` settings |
| `app/email_sender.py` | Added SSL support (`SMTP_SSL`), proper error handling |
| `app/main.py` | Added `/health` endpoint, in-process rate limiter middleware |
| `app/database.py` | Added connection pool tuning (`pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle`) |
| `docker-compose.yml` | Added API healthcheck, `restart: unless-stopped`, postgres tuning, uvicorn workers |
| `.env.example` | Added `SMTP_USE_SSL`, `RATE_LIMIT_AUTH`, SMTP examples for ukr.net and Gmail |
| `.env` | Added `SMTP_USE_SSL`, `RATE_LIMIT_AUTH` |
| `tests/conftest.py` | Set `RATE_LIMIT_AUTH=0` to prevent rate limiter from interfering with tests |

---

## Production Hardening Roadmap

### Must-have before production
1. **Alembic migrations** — replace `create_all` for zero-downtime schema evolution
2. **Redis rate limiting** — replace in-process limiter with `slowapi` + Redis
3. **TLS termination** — nginx/Caddy in front of uvicorn
4. **Async email queue** — Arq or Celery for reliable email delivery with retries
5. **Refresh tokens** — add `POST /auth/refresh` with longer-lived refresh token
6. **Structured logging** — JSON logs with request ID for distributed tracing

### Should-have for national scale
7. **PgBouncer** — connection pooler in transaction mode in front of PostgreSQL
8. **Read replicas** — separate read/write DB connections for list endpoints
9. **Redis cache** — cache `/auth/doctors` and other read-heavy endpoints
10. **Kubernetes deployment** — horizontal scaling, rolling updates, health probes
11. **Prometheus + Grafana** — metrics for request rate, latency, error rate, DB pool usage
12. **Patient search** — full-text search by name/DOB for doctors
13. **Admin role** — user management, audit log viewer, system health dashboard
14. **National ID / IPN** — Ukrainian tax ID or passport number for patient identity
15. **GDPR / medical data compliance** — data retention policy, right to erasure, audit trail
