import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Appointment
from app.schemas import AppointmentCreate


async def create_appointment(
    db: AsyncSession, data: AppointmentCreate, client_id: uuid.UUID
) -> Appointment:
    appt = Appointment(
        client_id=client_id,
        doctor_id=data.doctor_id,
        scheduled_at=data.scheduled_at,
        notes=data.notes,
    )
    db.add(appt)
    await db.flush()
    return appt


async def get_appointments_for_doctor(db: AsyncSession, doctor_id: uuid.UUID) -> list[Appointment]:
    result = await db.execute(
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.scheduled_at)
    )
    return list(result.scalars().all())


async def get_appointments_for_client(db: AsyncSession, client_id: uuid.UUID) -> list[Appointment]:
    result = await db.execute(
        select(Appointment)
        .where(Appointment.client_id == client_id)
        .order_by(Appointment.scheduled_at)
    )
    return list(result.scalars().all())


async def get_appointment(db: AsyncSession, appt_id: uuid.UUID) -> Optional[Appointment]:
    result = await db.execute(select(Appointment).where(Appointment.id == appt_id))
    return result.scalar_one_or_none()
