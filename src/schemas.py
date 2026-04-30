from pydantic import BaseModel, ConfigDict
from datetime import date, datetime

# Schema for creating a patient.
# Why? To define the API contract for incoming requests.
class PatientCreate(BaseModel):
    full_name: str
    birth_date: date

# Schema for patient response.
# Why? To ensure only relevant data is sent back and for documentation.
class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # Allows Pydantic to read SQLAlchemy objects

    id: int
    full_name: str
    birth_date: date
    created_at: datetime
