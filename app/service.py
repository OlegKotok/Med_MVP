import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app import repository as repo
from app.schemas import PatientCreate
from app.models import Patient


async def create_patient(
    db: AsyncSession, data: PatientCreate, owner_id: Optional[uuid.UUID] = None
) -> Patient:
    patient = await repo.create_patient(db, data, owner_id=owner_id)
    await repo.create_audit_log(db, "patient_created", patient.id, performed_by=owner_id)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient(db: AsyncSession, patient_id: uuid.UUID) -> Optional[Patient]:
    return await repo.get_patient(db, patient_id)


async def list_patients(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[Patient]:
    return await repo.list_patients(db, limit=limit, offset=offset)
