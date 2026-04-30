# Code Review — Medical Patient Registration Backend

**Reviewed:** 2026-04-30 (v3 — post auth implementation)
**Scope:** Security, correctness, production-readiness

---

## Overall Assessment

The codebase now has a complete authentication and authorisation layer: email registration with a 6-digit verification code, JWT-based login, and role-based access control (doctor / client). All previously identified HIGH and MEDIUM issues are resolved. The system is suitable as a production demo. Remaining items are improvements for a real multi-user deployment, not blockers.

---

## Auth Flow

```
POST /auth/register  →  creates unverified user, sends 6-digit code to email
POST /auth/verify    →  marks user verified (code is single-use, cleared after use)
POST /auth/login     →  returns JWT (only if verified); 403 if not verified
```

JWT payload: `{ sub: user_id, role: "doctor"|"client", exp: ... }`

---

## Role Rules

| Action | doctor | client |
|--------|--------|--------|
| `GET /patients/` | ✅ | ❌ 403 |
| `GET /patients/{id}` | ✅ any | ✅ own record only |
| `POST /patients/` | ✅ | ✅ |

---

## Per-File Status

| File | Status | Notes |
|------|--------|-------|
| `app/config.py` | ✅ | `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, SMTP settings. `SettingsConfigDict`. |
| `app/auth.py` | ✅ | `get_current_user` decodes JWT. `require_role()` factory for role guards. Clean `Depends` pattern. |
| `app/auth_router.py` | ✅ | 3 endpoints: register, verify, login. No business logic in router. |
| `app/auth_service.py` | ✅ | Password hashing (bcrypt), JWT signing (HS256), code generation, email dispatch. |
| `app/auth_repository.py` | ✅ | `create_user`, `get_user_by_email`, `get_user_by_id`, `mark_verified`. |
| `app/email_sender.py` | ✅ | Console log in demo mode (no SMTP_HOST). Real SMTP when configured. |
| `app/models.py` | ✅ | `User` + `Patient` + `AuditLog`. `owner_id` on Patient. `performed_by` on AuditLog. `Optional[X]` used (not `X\|None`) for Python 3.14 / SQLAlchemy 2.0.41 compat. |
| `app/schemas.py` | ✅ | Auth schemas + patient schemas in one file. `birth_date` validator. `EmailStr` validated. |
| `app/repository.py` | ✅ | `owner_id` and `performed_by` passed through. Pagination via LIMIT/OFFSET. |
| `app/service.py` | ✅ | Atomic commit: patient + audit log. |
| `app/router.py` | ✅ | Route ordering correct. Role guards via `dependencies=[]` and per-endpoint `Depends`. |
| `app/main.py` | ✅ | Security headers. Global `SQLAlchemyError` handler. Both routers mounted. |
| `requirements.txt` | ✅ | All versions pinned. `sqlalchemy==2.0.41` (Python 3.14 fix). `bcrypt==4.0.1` (passlib compat). |
| `docker-compose.yml` | ✅ | Env-var credentials. `pg_isready` healthcheck. `service_healthy` condition. |
| `Dockerfile` | ✅ | Non-root `appuser`. |
| `.dockerignore` | ✅ | Excludes `.env`, `__pycache__`, `.git`, tests. |

---

## Security Checklist

| Check | Result | Detail |
|-------|--------|--------|
| Authentication | ✅ | JWT Bearer on all `/patients` endpoints |
| Email verification | ✅ | 6-digit code, single-use, cleared after verification |
| Password hashing | ✅ | bcrypt via passlib |
| Role-based access | ✅ | doctor / client enforced per endpoint |
| Client data isolation | ✅ | Client can only read their own patient record |
| Input validation | ✅ | Email format, password min length, birth_date range |
| SQL injection | ✅ | ORM only, no raw SQL |
| Error information leakage | ✅ | SQLAlchemy errors return `{"detail": "Database error"}` |
| Secrets in source | ✅ | All credentials via env vars |
| Security headers | ✅ | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control` |
| XSS in frontend | ✅ | `escHtml()` on all user data rendered to DOM |
| Non-root container | ✅ | `appuser` in Dockerfile |
| TLS / HTTPS | ⚠️ | Terminate at reverse proxy (nginx/Caddy) — not configured here |
| Rate limiting | ⚠️ | No rate limiting on `/auth/register` or `/auth/login` |
| JWT secret strength | ⚠️ | Default `"change-me-in-production"` — must be overridden via env |
| Token revocation | ⚠️ | JWTs are stateless; no blacklist. Logout = client discards token |
| Verification code expiry | ⚠️ | Code has no time-based expiry — only invalidated on use |
| DB migrations | ⚠️ | `create_all` used; replace with Alembic for production schema evolution |

---

## Dependency Notes

Three version pins were required to work around Python 3.14 compatibility issues in third-party libraries:

| Package | Version | Reason |
|---------|---------|--------|
| `sqlalchemy` | 2.0.41 | 2.0.40 crashes on `Optional[X]` in `Mapped` annotations under Python 3.14 |
| `bcrypt` | 4.0.1 | bcrypt 5.x raises `ValueError` on passwords >72 bytes; passlib 1.7.4 is not compatible with bcrypt 5.x |
| `email-validator` | 2.2.0 | Required by Pydantic `EmailStr`; not installed by default |

---

## What to Improve Next

1. **Add time-based expiry to verification codes** — store `code_expires_at` on the User and reject expired codes.
2. **Rate-limit auth endpoints** — protect `/auth/register` and `/auth/login` from brute-force and spam.
3. **TLS** — terminate HTTPS at nginx/Caddy; never expose uvicorn directly.
4. **Alembic migrations** — replace `create_all` so schema changes can be applied without data loss.
5. **Token refresh** — add a `POST /auth/refresh` endpoint with a longer-lived refresh token for better UX.
