from sqlalchemy.ext.asyncio import AsyncSession
from .models import Patient, AuditLog
from .schemas import PatientCreate

class PatientRepository:
    """Handles all database operations for Patients."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, patient_data: PatientCreate) -> Patient:
        # Create a new patient record. Why? To persist patient data.
        patient = Patient(**patient_data.model_dump())
        self.db.add(patient)
        await self.db.flush() # Flush to get the ID without committing yet
        return patient

class AuditRepository:
    """Handles all database operations for Audit Logs."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(self, action: str, target_id: int, target_type: str):
        # Record an action in the audit log. Why? For security and tracking.
        log = AuditLog(action=action, target_id=target_id, target_type=target_type)
        self.db.add(log)
        await self.db.flush()
