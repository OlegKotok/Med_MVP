# Architecture - Patient Registration System

## Principles
- **Simple Layering**: Router -> Service -> Repository.
- **Async First**: All I/O operations are asynchronous using FastAPI and SQLAlchemy 2.0.
- **Dependency Injection**: Used for decoupling components and easier testing.
- **Audit Logging**: Integrated into the service layer to ensure every patient creation is recorded.

## File Structure
- `database.py`: Handles SQLAlchemy engine and session creation. Centralizes connection logic.
- `models.py`: Defines database tables (`Patient`, `AuditLog`). Why separate? Keeps schema definition clean and central.
- `schemas.py`: Pydantic models for request validation and response serialization.
- `repository.py`: Encapsulates raw SQL/ORM logic. Why? To keep services clean of database-specific syntax.
- `service.py`: Contains business logic and orchestrates audit logging. Why? This is the core "brain" of the application.
- `router.py`: FastAPI routes. Why? Decouples API contract from business logic.
- `main.py`: Application factory and dependency wiring.

## Data Model
- **Patient**: `id`, `full_name`, `birth_date`, `created_at`.
- **AuditLog**: `id`, `action`, `target_id`, `target_type`, `timestamp`. (Simple audit trail).
