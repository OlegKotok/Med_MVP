from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import RegisterRequest, VerifyRequest, LoginRequest, TokenResponse
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
