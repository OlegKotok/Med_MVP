from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# pool_size: persistent connections per worker process.
# max_overflow: extra connections allowed under burst load.
# pool_pre_ping: validates connections before use (handles DB restarts).
# For national-scale: use PgBouncer in transaction mode in front of Postgres.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # recycle connections after 1 hour to avoid stale connections
)

# expire_on_commit=False prevents lazy-load errors after commit in async context
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
