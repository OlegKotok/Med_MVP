# Architecture Decisions

## Overview

The system is designed using a simplified layered architecture:

- API (FastAPI routes)
- Service layer (business logic)
- Repository layer (database access)

## Why this approach?

- Keeps code readable and maintainable
- Avoids overengineering
- Easy to extend

## Async

Async is used to support scalability and efficient I/O operations.

## Data Integrity

A basic audit log is implemented to track changes in patient data.

## Trade-offs

- No complex patterns (DDD, CQRS) to keep solution simple
- Focus on clarity over abstraction