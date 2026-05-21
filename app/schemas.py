from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    birth_date: date

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, value: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("full_name must not be blank")
        return clean_value


class PatientRead(BaseModel):
    id: int
    full_name: str
    birth_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
