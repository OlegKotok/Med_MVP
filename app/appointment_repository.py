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
    return await get_appointments_for_doctor_paginated(db, doctor_id, limit=50, offset=0)


async def get_appointments_for_doctor_paginated(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    limit: int,
    offset: int,
) -> list[Appointment]:
    result = await db.execute(
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.scheduled_at)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_appointments_for_client(db: AsyncSession, client_id: uuid.UUID) -> list[Appointment]:
    return await get_appointments_for_client_paginated(db, client_id, limit=50, offset=0)


async def get_appointments_for_client_paginated(
    db: AsyncSession,
    client_id: uuid.UUID,
    limit: int,
    offset: int,
) -> list[Appointment]:
    result = await db.execute(
        select(Appointment)
        .where(Appointment.client_id == client_id)
        .order_by(Appointment.scheduled_at)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, appt_id: uuid.UUID) -> Optional[Appointment]:
    result = await db.execute(select(Appointment).where(Appointment.id == appt_id))
    return result.scalar_one_or_none()


async def doctor_slot_taken(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    scheduled_at,
) -> bool:
    result = await db.execute(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at == scheduled_at,
            Appointment.status.in_(("pending", "confirmed")),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None
