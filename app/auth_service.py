import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth_repository as repo
from app.config import settings
from app.email_sender import send_verification_email, send_password_reset_email
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
CODE_TTL_MINUTES = 15


def _hash(password: str) -> str:
    return _pwd.hash(password)


def _verify(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _make_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def _make_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": expire},
                      settings.JWT_SECRET, algorithm="HS256")


def _code_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES)


def _is_expired(dt: Optional[datetime]) -> bool:
    """Compare expiry against now. SQLite returns naive datetimes — treat as UTC."""
    if dt is None:
        return False
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return now > dt


async def register(db: AsyncSession, data: RegisterRequest) -> dict:
    if await repo.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    code = _make_code()
    await repo.create_user(db, data.email, data.full_name, _hash(data.password), data.role, code, _code_expiry())
    await db.commit()
    send_verification_email(data.email, code)
    return {"detail": "Verification code sent to your email"}


async def verify(db: AsyncSession, email: str, code: str) -> dict:
    user = await repo.get_user_by_email(db, email)
    if not user or user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid code")
    if _is_expired(user.code_expires_at):
        raise HTTPException(status_code=400, detail="Code expired")
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


async def forgot_password(db: AsyncSession, data: ForgotPasswordRequest) -> dict:
    user = await repo.get_user_by_email(db, data.email)
    if user and user.is_verified:
        code = _make_code()
        await repo.set_reset_code(db, user, code, _code_expiry())
        await db.commit()
        send_password_reset_email(data.email, code)
    return {"detail": "If that email is registered, a reset code has been sent"}


async def reset_password(db: AsyncSession, data: ResetPasswordRequest) -> dict:
    user = await repo.get_user_by_email(db, data.email)
    if not user or user.reset_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid code")
    if _is_expired(user.reset_code_expires_at):
        raise HTTPException(status_code=400, detail="Code expired")
    await repo.apply_password_reset(db, user, _hash(data.new_password))
    await db.commit()
    return {"detail": "Password updated. You can now log in."}


async def list_doctors(db: AsyncSession) -> list[User]:
    return await repo.list_doctors(db)
