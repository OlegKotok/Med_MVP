from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

# Using environment variable for flexibility, defaulting to postgres for ease of local setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/medical_db")

# Create async engine. Why? To handle database operations without blocking the event loop.
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory for creating new database sessions
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# Base class for SQLAlchemy models. Why? Provides the registry for all database tables.
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI. Why? Ensures each request gets its own session and cleans up after.
async def get_db():
    async with SessionLocal() as session:
        yield session
