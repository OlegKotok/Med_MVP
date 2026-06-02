import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Patient, AuditLog
from app.schemas import PatientCreate


async def create_patient(
    db: AsyncSession, data: PatientCreate, owner_id: Optional[uuid.UUID] = None
) -> Patient:
    patient = Patient(**data.model_dump(), owner_id=owner_id)
    db.add(patient)
    await db.flush()
    return patient


async def get_patient(db: AsyncSession, patient_id: uuid.UUID) -> Optional[Patient]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def list_patients(db: AsyncSession, limit: int, offset: int) -> list[Patient]:
    result = await db.execute(
        select(Patient).order_by(Patient.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def create_audit_log(
    db: AsyncSession,
    action: str,
    patient_id: uuid.UUID,
    performed_by: Optional[uuid.UUID] = None,
) -> None:
    db.add(AuditLog(action=action, patient_id=patient_id, performed_by=performed_by))
