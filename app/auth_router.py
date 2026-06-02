from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    RegisterRequest, VerifyRequest, LoginRequest, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest, DoctorResponse,
)
from app import auth_service as svc

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await svc.register(db, data)


@router.post("/verify")
async def verify(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    return await svc.verify(db, data.email, data.code)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await svc.login(db, data)


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await svc.forgot_password(db, data)


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await svc.reset_password(db, data)


@router.post("/resend-verification")
async def resend_verification(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await svc.resend_verification(db, data.email)


@router.get("/doctors", response_model=list[DoctorResponse])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    """Public endpoint — clients use this to pick a doctor when booking."""
    return await svc.list_doctors(db)
