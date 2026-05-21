from fastapi import APIRouter, Depends, status

from app.dependencies import get_patient_service
from app.schemas import PatientCreate, PatientRead
from app.service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    service: PatientService = Depends(get_patient_service),
) -> PatientRead:
    return await service.create_patient(patient_data)
