import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User


async def create_user(db: AsyncSession, email: str, hashed_password: str, role: str, code: str) -> User:
    user = User(email=email, hashed_password=hashed_password, role=role, verification_code=code)
    db.add(user)
    await db.flush()
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def mark_verified(db: AsyncSession, user: User) -> None:
    user.is_verified = True
    user.verification_code = None  # single-use; clear after verification
