import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth_repository as repo
from app.config import settings
from app.email_sender import send_verification_email
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, TokenResponse

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash(password: str) -> str:
    return _pwd.hash(password)


def _verify(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _make_code() -> str:
    """6-digit numeric code — simple, readable, hard to guess in context."""
    return "".join(random.choices(string.digits, k=6))


def _make_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "role": user.role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


async def register(db: AsyncSession, data: RegisterRequest) -> dict:
    existing = await repo.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    code = _make_code()
    await repo.create_user(db, data.email, _hash(data.password), data.role, code)
    await db.commit()

    # Send outside the transaction — email failure should not roll back the user row
    send_verification_email(data.email, code)
    return {"detail": "Verification code sent to your email"}


async def verify(db: AsyncSession, email: str, code: str) -> dict:
    user = await repo.get_user_by_email(db, email)
    if not user or user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    await repo.mark_verified(db, user)
    await db.commit()
    return {"detail": "Email verified. You can now log in."}


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await repo.get_user_by_email(db, data.email)
    if not user or not _verify(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return TokenResponse(access_token=_make_token(user))
