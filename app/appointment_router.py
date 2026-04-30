from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AppointmentCreate, AppointmentResponse
from app.auth import get_current_user
from app.models import User
from app import appointment_service as svc

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def book(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clients (and doctors) can book an appointment with a doctor."""
    return await svc.book_appointment(db, data, client_id=current_user.id)


@router.get("/", response_model=list[AppointmentResponse])
async def my_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Doctors see their incoming bookings. Clients see their own bookings."""
    return await svc.get_my_appointments(db, current_user.id, current_user.role)
