import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate
from app.auth import get_current_user, require_doctor
from app.models import User
from app import appointment_service as svc

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def book(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await svc.book_appointment(db, data, client_id=current_user.id)


@router.get("/", response_model=list[AppointmentResponse])
async def my_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Doctors see incoming bookings. Clients see their own."""
    return await svc.get_my_appointments(db, current_user.id, current_user.role)


@router.patch("/{appt_id}/status", response_model=AppointmentResponse)
async def update_status(
    appt_id: uuid.UUID,
    data: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    """Doctor confirms or cancels an appointment."""
    return await svc.update_status(db, appt_id, data.status, current_user.id)
