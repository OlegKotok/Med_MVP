from app.models import AuditLog, Patient
from app.schemas import PatientCreate


class PatientRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, patient_data: PatientCreate) -> Patient:
        patient = Patient(**patient_data.model_dump())
        self.session.add(patient)
        await self.session.flush()
        return patient


class AuditRepository:
    def __init__(self, session):
        self.session = session

    async def record_patient_created(self, patient: Patient) -> AuditLog:
        entry = AuditLog(
            patient_id=patient.id,
            action="patient_created",
            details={"full_name": patient.full_name, "birth_date": patient.birth_date.isoformat()},
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
