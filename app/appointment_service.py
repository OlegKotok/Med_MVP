import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app import appointment_repository as repo
from app import auth_repository as user_repo
from app.email_sender import send_appointment_notification
from app.models import Appointment
from app.schemas import AppointmentCreate
from fastapi import HTTPException


async def book_appointment(
    db: AsyncSession, data: AppointmentCreate, client_id: uuid.UUID
) -> Appointment:
    # Verify the chosen doctor exists and is actually a doctor
    doctor = await user_repo.get_user_by_id(db, data.doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    appt = await repo.create_appointment(db, data, client_id)
    await db.commit()
    await db.refresh(appt)

    # Notify doctor by email — outside transaction, failure doesn't roll back booking
    client = await user_repo.get_user_by_id(db, client_id)
    send_appointment_notification(
        doctor_email=doctor.email,
        client_email=client.email if client else "unknown",
        scheduled_at=str(appt.scheduled_at),
        notes=appt.notes or "",
    )
    return appt


async def get_my_appointments(db: AsyncSession, user_id: uuid.UUID, role: str) -> list[Appointment]:
    if role == "doctor":
        return await repo.get_appointments_for_doctor(db, user_id)
    return await repo.get_appointments_for_client(db, user_id)
