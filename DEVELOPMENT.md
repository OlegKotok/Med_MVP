# Development Guide

## Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
Set the `DATABASE_URL` environment variable if you have a running Postgres instance.
Otherwise, it defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/medical_db`.

Run with uvicorn:
```bash
uvicorn src.main:app --reload
```

## Running Tests
Tests use an in-memory SQLite database for simplicity.
```bash
pytest
```

## Project Structure
- `src/`: Core application code.
- `tests/`: Test suite.
- `requirements.txt`: Project dependencies.
- `ARCHITECTURE.md`: Detailed architectural decisions.
- `TTD_PLAN.md`: Development roadmap.
