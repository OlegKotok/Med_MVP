import uuid
import logging
import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app import appointment_repository as repo
from app import auth_repository as user_repo
from app.email_sender import send_appointment_notification
from app.models import Appointment
from app.schemas import AppointmentCreate, AppointmentResponse
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _enrich(appt: Appointment, client_name: str | None, client_email: str | None) -> AppointmentResponse:
    return AppointmentResponse(
        id=appt.id,
        client_id=appt.client_id,
        doctor_id=appt.doctor_id,
        scheduled_at=appt.scheduled_at,
        notes=appt.notes,
        status=appt.status,
        created_at=appt.created_at,
        client_name=client_name,
        client_email=client_email,
    )


async def book_appointment(
    db: AsyncSession, data: AppointmentCreate, client_id: uuid.UUID
) -> AppointmentResponse:
    doctor = await user_repo.get_user_by_id(db, data.doctor_id)
    if not doctor or doctor.role != "doctor" or not doctor.is_verified:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if await repo.doctor_slot_taken(db, data.doctor_id, data.scheduled_at):
        raise HTTPException(status_code=409, detail="Doctor already has an appointment at this time")

    appt = await repo.create_appointment(db, data, client_id)
    await db.commit()
    await db.refresh(appt)

    client = await user_repo.get_user_by_id(db, client_id)
    try:
        await anyio.to_thread.run_sync(
            send_appointment_notification,
            doctor.email,
            client.full_name if client else "Unknown",
            client.email if client else "unknown",
            str(appt.scheduled_at),
            appt.notes or "",
        )
    except Exception:
        logger.exception("Failed to send appointment notification for appointment_id=%s", appt.id)

    return _enrich(appt, client.full_name if client else None, client.email if client else None)


async def get_my_appointments(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: str,
    limit: int = 50,
    offset: int = 0,
) -> list[AppointmentResponse]:
    if role == "doctor":
        appts = await repo.get_appointments_for_doctor_paginated(db, user_id, limit=limit, offset=offset)
    else:
        appts = await repo.get_appointments_for_client_paginated(db, user_id, limit=limit, offset=offset)

    # Resolve unique client IDs in one pass
    client_ids = {a.client_id for a in appts}
    clients = {cid: await user_repo.get_user_by_id(db, cid) for cid in client_ids}

    return [
        _enrich(a, clients[a.client_id].full_name if clients.get(a.client_id) else None,
                   clients[a.client_id].email if clients.get(a.client_id) else None)
        for a in appts
    ]


async def update_status(
    db: AsyncSession, appt_id: uuid.UUID, new_status: str, doctor_id: uuid.UUID
) -> AppointmentResponse:
    appt = await repo.get_by_id(db, appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Not your appointment")
    appt.status = new_status
    await db.commit()
    await db.refresh(appt)
    client = await user_repo.get_user_by_id(db, appt.client_id)
    return _enrich(appt, client.full_name if client else None, client.email if client else None)
