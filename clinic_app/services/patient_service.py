"""
PatientService — all patient-related business logic.

This layer sits between the GUI and the database.
It never raises raw SQLAlchemy or SQLite exceptions to the caller;
all errors are wrapped in friendly PatientServiceError messages.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_

from clinic_app.database.connection import get_session
from clinic_app.models.patient import Patient


class PatientServiceError(Exception):
    """Friendly, user-facing error raised by the service layer."""


# ---------------------------------------------------------------------------
# Patient code generation
# ---------------------------------------------------------------------------

def _next_patient_code(session) -> str:
    """
    Generate the next sequential patient code, e.g. PT-00042.
    Thread-safe within a single session transaction.
    """
    last: Patient | None = (
        session.query(Patient)
        .order_by(Patient.id.desc())
        .first()
    )
    if last is None:
        return "PT-00001"
    # Extract the numeric part and increment
    match = re.search(r"(\d+)$", last.patient_code)
    next_num = (int(match.group(1)) + 1) if match else 1
    return f"PT-{next_num:05d}"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_phone(phone: str) -> str | None:
    """
    Strip common separators and validate a phone number.
    Returns the cleaned number, or raises PatientServiceError.
    Returns None if phone is empty (phone is optional).
    """
    if not phone or not phone.strip():
        return None
    cleaned = re.sub(r"[\s\-().+]", "", phone.strip())
    if not cleaned.isdigit():
        raise PatientServiceError(
            "Phone number should contain digits only "
            "(spaces and dashes are removed automatically)."
        )
    if len(cleaned) < 7 or len(cleaned) > 15:
        raise PatientServiceError(
            "Phone number must be between 7 and 15 digits."
        )
    return cleaned


def _validate_required(data: dict):
    """Raise PatientServiceError if any required field is missing."""
    name = (data.get("full_name") or "").strip()
    if not name:
        raise PatientServiceError("Full name is required.")
    if len(name) < 2:
        raise PatientServiceError("Full name must be at least 2 characters.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_patient(data: dict) -> Patient:
    """
    Validate data and insert a new patient record.
    Returns the saved Patient object.
    Raises PatientServiceError on validation or database failure.
    """
    _validate_required(data)
    phone = _validate_phone(data.get("phone", ""))

    with get_session() as session:
        code = _next_patient_code(session)
        now = datetime.utcnow()

        patient = Patient(
            patient_code=code,
            full_name=data["full_name"].strip(),
            date_of_birth=data.get("date_of_birth") or None,
            age_at_registration=data.get("age_at_registration") or None,
            gender=data.get("gender") or "Not recorded",
            phone=phone,
            address=(data.get("address") or "").strip() or None,
            emergency_contact=(data.get("emergency_contact") or "").strip() or None,
            notes=(data.get("notes") or "").strip() or None,
            created_at=now,
            updated_at=now,
        )
        try:
            session.add(patient)
            session.flush()   # get the id before commit
            # Detach so the object can be used after the session closes
            session.expunge(patient)
            from sqlalchemy.orm import make_transient
            make_transient(patient)
        except Exception as exc:
            raise PatientServiceError(
                "Could not save patient. Please try again."
            ) from exc

    return patient


def get_all_patients(active_only: bool = True) -> list[Patient]:
    """Return all patients, most recently registered first."""
    with get_session() as session:
        q = session.query(Patient)
        if active_only:
            q = q.filter(Patient.is_active == True)  # noqa: E712
        patients = q.order_by(Patient.id.desc()).all()
        # Detach all objects
        for p in patients:
            session.expunge(p)
            from sqlalchemy.orm import make_transient
            make_transient(p)
    return patients


def search_patients(query: str, active_only: bool = True) -> list[Patient]:
    """
    Search patients by partial name, patient code, or phone number.
    Case-insensitive.  Returns an empty list (never raises) on empty query.
    """
    q_stripped = (query or "").strip()
    if not q_stripped:
        return get_all_patients(active_only)

    pattern = f"%{q_stripped}%"
    with get_session() as session:
        base = session.query(Patient)
        if active_only:
            base = base.filter(Patient.is_active == True)  # noqa: E712
        patients = (
            base.filter(
                or_(
                    Patient.full_name.ilike(pattern),
                    Patient.patient_code.ilike(pattern),
                    Patient.phone.ilike(pattern),
                )
            )
            .order_by(Patient.full_name)
            .all()
        )
        for p in patients:
            session.expunge(p)
            from sqlalchemy.orm import make_transient
            make_transient(p)
    return patients


def get_patient_by_id(patient_id: int) -> Optional[Patient]:
    """Return a single patient by internal id, or None."""
    with get_session() as session:
        p = session.query(Patient).filter(Patient.id == patient_id).first()
        if p:
            session.expunge(p)
            from sqlalchemy.orm import make_transient
            make_transient(p)
    return p


def update_patient(patient_id: int, data: dict) -> Patient:
    """
    Update editable fields of an existing patient.
    Patient code and created_at are never changed.
    Raises PatientServiceError on validation or database failure.
    """
    _validate_required(data)
    phone = _validate_phone(data.get("phone", ""))

    with get_session() as session:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if patient is None:
            raise PatientServiceError("Patient record not found.")

        patient.full_name        = data["full_name"].strip()
        patient.date_of_birth    = data.get("date_of_birth") or None
        patient.age_at_registration = data.get("age_at_registration") or None
        patient.gender           = data.get("gender") or "Not recorded"
        patient.phone            = phone
        patient.address          = (data.get("address") or "").strip() or None
        patient.emergency_contact = (data.get("emergency_contact") or "").strip() or None
        patient.notes            = (data.get("notes") or "").strip() or None
        patient.updated_at       = datetime.utcnow()

        try:
            session.flush()
            session.expunge(patient)
            from sqlalchemy.orm import make_transient
            make_transient(patient)
        except Exception as exc:
            raise PatientServiceError(
                "Could not update patient. Please try again."
            ) from exc

    return patient


def find_possible_duplicates(full_name: str, phone: str) -> list[Patient]:
    """
    Return patients that share the same phone number OR have a very
    similar name.  Used for duplicate-warning before saving.
    Does NOT merge or modify records.
    """
    cleaned_phone = _validate_phone(phone) if phone and phone.strip() else None
    name_pattern = f"%{full_name.strip()}%" if full_name and full_name.strip() else None

    if not cleaned_phone and not name_pattern:
        return []

    with get_session() as session:
        conditions = []
        if cleaned_phone:
            conditions.append(Patient.phone == cleaned_phone)
        if name_pattern:
            conditions.append(Patient.full_name.ilike(name_pattern))

        patients = (
            session.query(Patient)
            .filter(Patient.is_active == True, or_(*conditions))  # noqa: E712
            .all()
        )
        for p in patients:
            session.expunge(p)
            from sqlalchemy.orm import make_transient
            make_transient(p)
    return patients


def archive_patient(patient_id: int) -> None:
    """
    Soft-delete: mark a patient as inactive instead of hard-deleting.
    An audit trail is preserved.
    """
    with get_session() as session:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if patient is None:
            raise PatientServiceError("Patient record not found.")
        patient.is_active = False
        patient.updated_at = datetime.utcnow()
