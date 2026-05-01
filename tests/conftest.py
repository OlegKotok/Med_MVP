import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")

# Patch postgresql.UUID → String(36) for SQLite compatibility
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String

_orig = PG_UUID.__init__
def _patch(self, *a, **kw):
    _orig(self, *a, **kw)
    self.impl = String(36)
PG_UUID.__init__ = _patch

import app.models  # noqa: F401
import app.auth_service as auth_service
from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
TEST_CODE = "123456"


@pytest.fixture(autouse=True)
def fixed_verification_code(monkeypatch):
    """Make every test use a predictable verification code."""
    monkeypatch.setattr(auth_service, "_make_code", lambda: TEST_CODE)


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_db] = override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


async def register_and_login(client: AsyncClient, email: str, role: str) -> str:
    """Register → verify → login → return Bearer token."""
    await client.post("/auth/register", json={
        "email": email, "password": "password123", "role": role, "full_name": "Test User",
    })
    await client.post("/auth/verify", json={"email": email, "code": TEST_CODE})
    resp = await client.post("/auth/login", json={"email": email, "password": "password123"})
    return resp.json()["access_token"]
