# Medical Patient Registration Backend — Plan

## 1. Goal

Build a minimal async REST API for patient registration using FastAPI, SQLAlchemy 2.0, and PostgreSQL.
The system records patient data and maintains a tamper-evident audit log of all write operations.
No authentication, no RBAC, no extras — just the core registration flow.

---

## 2. Roles

| Role | Responsibility |
|-----------|----------------|
| Architect | Defines structure, data model, API contract, and architecture decisions (this document) |
| Developer | Implements all layers: router, service, repository, models, migrations |
| Reviewer | Validates code against this plan; checks for overengineering, missing error handling |
| Tester | Writes and runs integration tests against a real PostgreSQL instance |

---

## 3. File Structure

```
app/
├── main.py                  # FastAPI app factory, lifespan
├── database.py              # Async engine + session factory
├── dependencies.py          # get_db() dependency
├── models/
│   ├── patient.py           # Patient ORM model
│   └── audit_log.py         # AuditLog ORM model
├── schemas/
│   ├── patient.py           # Pydantic request/response schemas
│   └── audit_log.py         # Pydantic audit schema (optional)
├── repositories/
│   ├── patient.py           # DB queries for Patient
│   └── audit_log.py         # DB queries for AuditLog
├── services/
│   └── patient.py           # Business logic, calls repo + audit
├── routers/
│   └── patient.py           # HTTP endpoints
tests/
│   └── test_patient.py      # Integration tests
alembic/                     # Migrations
alembic.ini
docker-compose.yml
requirements.txt
.env
```

---

## 4. Architecture Decisions

- **async SQLAlchemy 2.0 + asyncpg** — native async driver; no sync blocking in event loop
- **Router → Service → Repository** — clear separation; routers handle HTTP, services handle logic, repos handle SQL
- **Dependency injection via `Depends(get_db)`** — session lifecycle managed per-request, no globals
- **Alembic for migrations** — schema changes are versioned and reproducible
- **Pydantic v2 schemas separate from ORM models** — decouples API contract from DB schema
- **Audit log written in the same transaction as the mutation** — guarantees consistency; no orphaned logs
- **Single `.env` file for config** — `DATABASE_URL` and nothing else needed at this scope
- **No base repository class / no generics** — YAGNI; two concrete repos are simpler than an abstraction

---

## 5. Data Model

### `patients`

| Field | Type | Notes |
|------------|-------------|-------------------------------|
| id | UUID | PK, default `gen_random_uuid()` |
| full_name | VARCHAR(255)| NOT NULL |
| birth_date | DATE | NOT NULL |
| created_at | TIMESTAMPTZ | default `now()`, NOT NULL |

### `audit_logs`

| Field | Type | Notes |
|------------|-------------|-------------------------------|
| id | UUID | PK, default `gen_random_uuid()` |
| entity | VARCHAR(64) | e.g. `"patient"` |
| entity_id | UUID | FK to the affected record |
| action | VARCHAR(32) | `"create"` / `"update"` / `"delete"` |
| payload | JSONB | Snapshot of data at time of action |
| created_at | TIMESTAMPTZ | default `now()`, NOT NULL |

---

## 6. API Contract

| Method | Path | Request Body | Response |
|--------|------|--------------|----------|
| `POST` | `/patients` | `{ full_name, birth_date }` | `201` Patient object |
| `GET` | `/patients` | — | `200` List of patients |
| `GET` | `/patients/{id}` | — | `200` Patient object / `404` |
| `PUT` | `/patients/{id}` | `{ full_name?, birth_date? }` | `200` Updated patient / `404` |
| `DELETE` | `/patients/{id}` | — | `204` No content / `404` |

**Patient response schema:**
```json
{
  "id": "uuid",
  "full_name": "string",
  "birth_date": "YYYY-MM-DD",
  "created_at": "ISO8601"
}
```

---

## 7. Audit Log Design

**What gets logged:** every `POST`, `PUT`, `DELETE` on `/patients`.

**When:** inside the same DB transaction as the mutation (service layer calls `audit_repo.create()` before commit).

**Schema** (see Data Model above). `payload` stores the patient dict after the mutation (post-state).

Example audit record for a create:
```json
{
  "entity": "patient",
  "entity_id": "a1b2c3...",
  "action": "create",
  "payload": { "full_name": "Jane Doe", "birth_date": "1990-05-12" }
}
```

---

## 8. Dev Steps

1. `docker-compose.yml` — PostgreSQL service + app service skeleton
2. `requirements.txt` — `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic`, `python-dotenv`
3. `database.py` — async engine, `AsyncSession` factory
4. `models/patient.py` + `models/audit_log.py` — ORM models
5. Alembic init + first migration (`create tables`)
6. `schemas/patient.py` — `PatientCreate`, `PatientUpdate`, `PatientOut`
7. `repositories/patient.py` + `repositories/audit_log.py` — CRUD queries
8. `services/patient.py` — orchestrates repo calls + audit writes in one transaction
9. `routers/patient.py` — 5 endpoints wired to service
10. `main.py` — mount router, configure lifespan (create engine)
11. `tests/test_patient.py` — happy-path integration tests for all 5 endpoints
