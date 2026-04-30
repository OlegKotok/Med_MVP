from datetime import date, datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func
from .database import Base

# Patient model. Represents the 'patients' table.
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[date] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

# AuditLog model. Represents the 'audit_logs' table.
# Why? To satisfy the requirement for basic audit logging.
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'CREATE_PATIENT'
    target_id: Mapped[int] = mapped_column(nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'patient'
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
