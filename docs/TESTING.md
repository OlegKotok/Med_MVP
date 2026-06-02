# Testing

## How to run

```bash
# Activate the virtual environment
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Install dependencies (first time only)
pip install -r requirements.txt
pip install pytest==8.3.5 pytest-asyncio==0.25.3 httpx==0.28.1 aiosqlite==0.21.0 greenlet==3.2.2

# Run all tests
DATABASE_URL=sqlite+aiosqlite:///:memory: pytest tests/ -v
```

The `DATABASE_URL` env var must be set so `app.config.Settings` can initialise without a `.env` file.

## Test cases

| Test | What it covers |
|------|---------------|
| `test_create_patient_success` | `POST /patients/` returns 201 and an `id` field |
| `test_create_patient_missing_full_name` | `POST /patients/` without `full_name` returns 422 (Pydantic validation) |
| `test_get_patient_found` | `GET /patients/{id}` returns 200 and the correct patient |
| `test_get_patient_not_found` | `GET /patients/{id}` with an unknown UUID returns 404 |
| `test_list_patients` | `GET /patients/` returns a list containing all created patients |

## Test dependencies

- **pytest** — test runner
- **pytest-asyncio** — async test support (`asyncio_mode = auto` in `pytest.ini`)
- **httpx** — async HTTP client used with FastAPI's `ASGITransport`
- **aiosqlite** — async SQLite driver for in-memory test database
- **greenlet** — required by SQLAlchemy async internals (not bundled on Python 3.14)

## Known limitations

- **PostgreSQL UUID dialect** — `app/models.py` uses `sqlalchemy.dialects.postgresql.UUID`. The conftest patches its `impl` to `String(36)` so SQLite accepts it. This means UUID values are stored as plain strings in tests, not native UUIDs.
- **`server_default` timestamps** — SQLite's `func.now()` returns a text timestamp rather than a timezone-aware datetime. Tests do not assert on `created_at` format to avoid false failures.
- **No migration testing** — tests call `Base.metadata.create_all` directly; Alembic migration paths are not exercised.
- **Single-process only** — the in-memory SQLite database is not shared across processes, so tests cannot be parallelised with `pytest-xdist`.
