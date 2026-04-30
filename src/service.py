from sqlalchemy.ext.asyncio import AsyncSession
from .repository import PatientRepository, AuditRepository
from .schemas import PatientCreate
from .models import Patient

class PatientService:
    """Coordinates business logic for patients."""
    def __init__(self, patient_repo: PatientRepository, audit_repo: AuditRepository, db: AsyncSession):
        self.patient_repo = patient_repo
        self.audit_repo = audit_repo
        self.db = db

    async def register_patient(self, patient_data: PatientCreate) -> Patient:
        # We use a transaction to ensure both patient creation and audit logging succeed or fail together.
        # Why? To maintain data integrity between business data and audit logs.
        async with self.db.begin():
            patient = await self.patient_repo.create(patient_data)
            
            await self.audit_repo.log_action(
                action="CREATE_PATIENT",
                target_id=patient.id,
                target_type="patient"
            )
            
            return patient
