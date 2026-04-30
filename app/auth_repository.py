import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User


async def create_user(
    db: AsyncSession, email: str, full_name: str, hashed_password: str, role: str,
    code: str, code_expires_at: datetime
) -> User:
    user = User(
        email=email, full_name=full_name, hashed_password=hashed_password, role=role,
        verification_code=code, code_expires_at=code_expires_at,
    )
    db.add(user)
    await db.flush()
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_doctors(db: AsyncSession) -> list[User]:
    """Return all verified doctors — used by clients to pick a doctor."""
    result = await db.execute(
        select(User).where(User.role == "doctor", User.is_verified == True)  # noqa: E712
    )
    return list(result.scalars().all())


async def mark_verified(db: AsyncSession, user: User) -> None:
    user.is_verified = True
    user.verification_code = None
    user.code_expires_at = None


async def set_reset_code(db: AsyncSession, user: User, code: str, expires_at: datetime) -> None:
    user.reset_code = code
    user.reset_code_expires_at = expires_at


async def apply_password_reset(db: AsyncSession, user: User, hashed_password: str) -> None:
    user.hashed_password = hashed_password
    user.reset_code = None
    user.reset_code_expires_at = None
