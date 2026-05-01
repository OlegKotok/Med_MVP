from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Single engine instance — reused across requests for connection pooling
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# expire_on_commit=False prevents lazy-load errors after commit in async context
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
