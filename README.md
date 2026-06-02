# 🏥 Med_MVP — Modern Patient Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)

**Med_MVP** is a production-minded, high-performance Medical Patient Management MVP. It demonstrates a clean, layered architecture for a patient registration and appointment booking system, built with a focus on security, scalability, and developer experience.

> 🚀 **LLM-Driven Development**: This project serves as a benchmark and demonstration of high-quality software engineering achieved through strategic LLM prompting and AI-assisted workflows.

---

## ✨ Key Features

- **🔐 Secure Authentication**: Full JWT-based flow with bcrypt hashing, email verification, and password reset.
- **👥 Role-Based Access (RBAC)**: Distinct workflows and permissions for **Doctors** and **Clients**.
- **📅 Appointment Management**: Real-time booking with double-booking prevention and doctor notifications.
- **🛡️ Security-First**: In-process rate limiting, security headers, non-root Docker containers, and sanitized error handling.
- **📱 Responsive UI**: Mobile-first, zero-dependency frontend for immediate interaction.
- **🧪 Test-Driven**: 35+ comprehensive tests covering auth, business logic, and edge cases.

---

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python)
- **Database**: [PostgreSQL 16](https://www.postgresql.org/) with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Asyncpg)
- **Auth**: [JWT](https://jwt.io/), [Passlib](https://passlib.readthedocs.io/) (bcrypt)
- **Infrastructure**: [Docker Compose](https://docs.docker.com/compose/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)

---

## 🚀 One-Command Demo

Experience the full system in seconds:

```bash
docker compose up --build
```

1. Open **[http://localhost:8000](http://localhost:8000)**.
2. Check logs for the 6-digit verification code: `docker compose logs api`.
3. Explore the API docs at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 📖 Documentation & Architecture

This project is meticulously documented to show the entire development lifecycle:

- [**🏗️ Architecture Decision Records**](docs/ARCHITECTURE.md) — Layered design and tech choices.
- [**🔍 Engineering Review**](docs/REVIEW.md) — Security, performance, and scaling roadmap.
- [**✅ Testing Strategy**](docs/TESTING.md) — TDD approach and coverage details.
- [**🛠️ Development Guide**](docs/DEVELOPMENT.md) — Setup for local development.
- [**📋 Project Task & Requirements**](docs/REQUIREMENTS.md) — Original scope and implementation status.
- [**🤖 AI Prompt**](docs/PROMPT.md) — The instructions used to generate this codebase.

---

## 🧪 Running Tests

Ensure system integrity with a single command:

```bash
# Using local environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

*Note: Tests use in-memory SQLite for speed and isolation.*

---

## 🛤️ Production Roadmap

To transition from MVP to national-scale production, the following are planned:
1. **Alembic Migrations** for zero-downtime schema updates.
2. **Redis-backed Rate Limiting** for horizontal scaling.
3. **Async Task Queue (Arq/Celery)** for reliable email delivery.
4. **TLS Termination** via Nginx/Caddy.
5. **Monitoring** with Prometheus and Grafana.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---
*Created by [Your Name/Github Handle] as a demonstration of modern backend excellence.*
