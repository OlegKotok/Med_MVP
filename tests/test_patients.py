import pytest
from sqlalchemy import select
from src.models import Patient, AuditLog

@pytest.mark.asyncio
async def test_create_patient_success(client, db_session):
    # Test successful patient creation
    payload = {
        "full_name": "John Doe",
        "birth_date": "1990-01-01"
    }
    response = await client.post("/patients/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert "id" in data
    
    # Verify patient in DB
    result = await db_session.execute(select(Patient).filter_by(full_name="John Doe"))
    patient = result.scalar_one_or_none()
    assert patient is not None
    assert str(patient.birth_date) == "1990-01-01"

@pytest.mark.asyncio
async def test_create_patient_audit_log(client, db_session):
    # Test that an audit log entry is created
    payload = {
        "full_name": "Jane Smith",
        "birth_date": "1985-05-05"
    }
    await client.post("/patients/", json=payload)
    
    # Verify audit log in DB
    result = await db_session.execute(select(AuditLog).filter_by(action="CREATE_PATIENT"))
    audit = result.scalars().all()
    assert len(audit) > 0
    assert audit[-1].target_type == "patient"

@pytest.mark.asyncio
async def test_create_patient_invalid_data(client):
    # Test validation error for missing fields
    payload = {"full_name": "John"} # missing birth_date
    response = await client.post("/patients/", json=payload)
    assert response.status_code == 422
