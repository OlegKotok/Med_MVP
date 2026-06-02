import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import PatientCreate, PatientResponse
from app.auth import get_current_user, require_doctor, require_any
from app.models import User
from app import service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=list[PatientResponse], dependencies=[Depends(require_doctor)])
async def list_patients(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Doctors only — list all patients."""
    return await service.list_patients(db, limit=limit, offset=offset)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any),
):
    """Doctors can fetch any patient. Clients can only fetch their own record."""
    patient = await service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role == "client" and patient.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return patient


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any),
):
    """Both roles can register a patient. The current user is recorded as owner."""
    return await service.create_patient(db, data, owner_id=current_user.id)
