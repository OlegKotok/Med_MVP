from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .schemas import PatientCreate, PatientResponse
from .repository import PatientRepository, AuditRepository
from .service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])

# Dependency injection for the service.
# Why? Decouples the router from the service implementation and makes testing easier.
async def get_patient_service(db: AsyncSession = Depends(get_db)) -> PatientService:
    patient_repo = PatientRepository(db)
    audit_repo = AuditRepository(db)
    return PatientService(patient_repo, audit_repo, db)

@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    service: PatientService = Depends(get_patient_service)
):
    # Endpoint to register a new patient.
    # Why? Entry point for the patient registration feature.
    return await service.register_patient(patient_data)
