"""
Patient ORM model.

Maps to the `patients` table in SQLite.
All database internals are hidden from the GUI layer.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from clinic_app.database.connection import Base


class Patient(Base):
    __tablename__ = "patients"

    # ---- Internal primary key (never shown to users) ------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ---- Human-readable patient code shown in the UI ------------------
    patient_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    # ---- Identity ----------------------------------------------------
    full_name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    date_of_birth: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # Stored as ISO-8601 date string: YYYY-MM-DD
    age_at_registration: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Fallback when exact DOB is not known
    gender: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Not recorded"
    )

    # ---- Contact ------------------------------------------------------
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    # ---- Misc ---------------------------------------------------------
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ---- Timestamps ---------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # ------------------------------------------------------------------
    def display_age(self) -> str:
        """Return a human-readable age or DOB string."""
        if self.date_of_birth:
            try:
                from datetime import date
                dob = date.fromisoformat(self.date_of_birth)
                today = date.today()
                age = (
                    today.year - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
                return f"{age} yrs  ({dob.strftime('%d %b %Y')})"
            except ValueError:
                return self.date_of_birth
        if self.age_at_registration is not None:
            return f"{self.age_at_registration} yrs (at registration)"
        return "—"

    def __repr__(self) -> str:
        return f"<Patient {self.patient_code} — {self.full_name}>"
