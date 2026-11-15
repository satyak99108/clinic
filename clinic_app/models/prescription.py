"""
Prescription and PrescriptionItem ORM models.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clinic_app.database.connection import Base

if TYPE_CHECKING:
    from clinic_app.models.consultation import Consultation
    from clinic_app.models.patient import Patient


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)

    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    consultation_id: Mapped[int] = mapped_column(Integer, ForeignKey("consultations.id"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")  # "Draft" or "Finalized"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", backref="prescriptions")
    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="prescriptions")
    items: Mapped[List["PrescriptionItem"]] = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan", order_by="PrescriptionItem.order_index")

    def __repr__(self) -> str:
        return f"<Prescription {self.prescription_code} status={self.status}>"


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(Integer, ForeignKey("prescriptions.id"), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    medicine_name: Mapped[str] = mapped_column(String(200), nullable=False)
    strength_form: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "Tab 500mg", "Syp 100ml"
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)         # free text, e.g. "1-0-1", "1 tsp"
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)       # e.g. "5 days", "2 weeks"
    measure_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)    # e.g. "Tablets", "Strip", "Bottle"
    instructions: Mapped[str | None] = mapped_column(String(255), nullable=True)   # e.g. "After food", "Before bedtime"

    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="items")

    def __repr__(self) -> str:
        return f"<PrescriptionItem {self.medicine_name} ({self.dosage})>"
