"""
Consultation ORM model.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clinic_app.database.connection import Base

if TYPE_CHECKING:
    from clinic_app.models.patient import Patient
    from clinic_app.models.prescription import Prescription


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    consultation_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    # Clinical fields
    chief_complaints: Mapped[str | None] = mapped_column(Text, nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vitals
    temperature: Mapped[str | None] = mapped_column(String(50), nullable=True)
    blood_pressure: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pulse: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weight: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Clinical findings & plan
    investigations: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # YYYY-MM-DD or readable text

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", backref="consultations")
    prescriptions: Mapped[List["Prescription"]] = relationship("Prescription", back_populates="consultation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Consultation id={self.id} patient_id={self.patient_id} date={self.consultation_date}>"
