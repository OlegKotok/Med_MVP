# Medical Patient Registration Backend

Minimal, production-minded FastAPI MVP for patient registration.

## Features

- `POST /patients` creates a patient with `full_name` and `birth_date`
- Basic audit log entry is written when a patient is created
- Async FastAPI + SQLAlchemy 2.0
- PostgreSQL runtime database
- Pytest coverage for creation, validation, audit logging, and health check
- Simple frontend page at `/`

## File Structure

```text
app/
  main.py              FastAPI app factory, routes, and static frontend mount
  config.py            Environment-based settings
  database.py          Async SQLAlchemy engine, session dependency, demo table creation
  models.py            Patient and AuditLog ORM models
  schemas.py           Pydantic request/response models
  repository.py        Database writes for patients and audit entries
  service.py           Transaction-level patient creation workflow
  dependencies.py      FastAPI dependency wiring
  routers/patients.py  Patient API endpoint
  static/              Simple frontend page
tests/
  conftest.py          Test app and database setup
  test_patients.py     API and audit-log tests
Dockerfile             API container
docker-compose.yml     API + PostgreSQL demo
```

## Why Each File Exists

- `app/main.py`: creates the application in one place and exposes `app` for Uvicorn.
- `app/config.py`: keeps runtime settings out of business code.
- `app/database.py`: centralizes database engine/session setup for dependency injection.
- `app/models.py`: defines the database shape used by SQLAlchemy.
- `app/schemas.py`: validates input and controls the public API response.
- `app/repository.py`: keeps database writes small and easy to test.
- `app/service.py`: owns the patient creation use case and commits patient + audit together.
- `app/dependencies.py`: wires repositories and service into FastAPI without global service objects.
- `app/routers/patients.py`: keeps HTTP concerns separate from business logic.
- `app/static/*`: provides a simple browser form for the MVP.
- `tests/*`: verifies the requested behavior without requiring PostgreSQL locally.

## Running

Run the full MVP demo with one Docker command:

```bash
docker compose up --build
```

Open `http://localhost:8000` for the frontend or call the API directly:

```bash
curl -X POST http://localhost:8000/patients \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Ada Lovelace","birth_date":"1815-12-10"}'
```

## Tests

```bash
.venv/bin/python -m pytest -q
```

The tests cover the patient API, validation, audit log creation, health check, and static frontend files.
