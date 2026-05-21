from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient
from app.repository import AuditRepository, PatientRepository
from app.schemas import PatientCreate


class PatientService:
    def __init__(
        self,
        session: AsyncSession,
        patient_repository: PatientRepository,
        audit_repository: AuditRepository,
    ):
        self.session = session
        self.patient_repository = patient_repository
        self.audit_repository = audit_repository

    async def create_patient(self, patient_data: PatientCreate) -> Patient:
        patient = await self.patient_repository.create(patient_data)
        await self.audit_repository.record_patient_created(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient
