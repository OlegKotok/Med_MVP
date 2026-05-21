from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repository import AuditRepository, PatientRepository
from app.service import PatientService


async def get_patient_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[PatientService, None]:
    patient_repository = PatientRepository(session)
    audit_repository = AuditRepository(session)
    yield PatientService(session, patient_repository, audit_repository)
