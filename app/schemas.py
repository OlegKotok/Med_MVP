import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Literal["doctor", "client"]


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Patients ─────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    birth_date: date

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_valid(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("birth_date must be in the past")
        if v.year < 1900:
            raise ValueError("birth_date year must be 1900 or later")
        return v


class PatientResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    birth_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
