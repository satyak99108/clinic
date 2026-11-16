"""
Prescription and Consultation service layer.
Handles saving drafts, finalizing prescriptions, adding/removing medicines,
and medicine catalog autocomplete.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import joinedload

from clinic_app.database.connection import get_session
from clinic_app.models.consultation import Consultation
from clinic_app.models.medicine import MedicineCatalog
from clinic_app.models.prescription import Prescription, PrescriptionItem


class PrescriptionServiceError(Exception):
    """Friendly user-facing error message."""
    pass


def _next_prescription_code(session) -> str:
    """Generate next sequential prescription code, e.g. RX-2026-0001."""
    year = datetime.now().year
    prefix = f"RX-{year}-"
    last = (
        session.query(Prescription)
        .filter(Prescription.prescription_code.like(f"{prefix}%"))
        .order_by(Prescription.id.desc())
        .first()
    )
    if not last:
        return f"{prefix}0001"
    match = re.search(r"(\d+)$", last.prescription_code)
    num = (int(match.group(1)) + 1) if match else 1
    return f"{prefix}{num:04d}"


def get_medicine_suggestions(query: str = "") -> list[str]:
    """Retrieve medicine names for autocomplete suggestions."""
    with get_session() as session:
        q = session.query(MedicineCatalog.name)
        if query.strip():
            q = q.filter(MedicineCatalog.name.ilike(f"%{query.strip()}%"))
        results = q.order_by(MedicineCatalog.name).limit(50).all()
        return [r[0] for r in results]


def add_medicine_to_catalog(name: str, form: Optional[str] = None, strength: Optional[str] = None):
    """Add a medicine to the local catalogue if not already present."""
    name_clean = name.strip()
    if not name_clean:
        return
    with get_session() as session:
        existing = session.query(MedicineCatalog).filter(MedicineCatalog.name.ilike(name_clean)).first()
        if not existing:
            cat = MedicineCatalog(name=name_clean, form=form, default_strength=strength)
            session.add(cat)


def seed_initial_catalog():
    """Seed common medicines if catalogue is currently empty."""
    common_meds = [
        ("Paracetamol 650mg", "Tablet"),
        ("Paracetamol 500mg", "Tablet"),
        ("Amoxicillin 500mg", "Capsule"),
        ("Augmentin 625mg (Amox-Clav)", "Tablet"),
        ("Azithromycin 500mg", "Tablet"),
        ("Cefixime 200mg", "Tablet"),
        ("Ciprofloxacin 500mg", "Tablet"),
        ("Pantoprazole 40mg", "Tablet"),
        ("Omeprazole 20mg", "Capsule"),
        ("Rabeprazole 20mg", "Tablet"),
        ("Cetirizine 10mg", "Tablet"),
        ("Levocetirizine 5mg", "Tablet"),
        ("Montelukast + Levocetirizine", "Tablet"),
        ("Ibuprofen 400mg", "Tablet"),
        ("Aceclofenac + Paracetamol", "Tablet"),
        ("Diclofenac 50mg", "Tablet"),
        ("Tramadol 50mg", "Tablet"),
        ("Metformin 500mg", "Tablet"),
        ("Glimepiride 1mg", "Tablet"),
        ("Telmisartan 40mg", "Tablet"),
        ("Amlodipine 5mg", "Tablet"),
        ("Atorvastatin 10mg", "Tablet"),
        ("Multivitamin & Minerals", "Capsule"),
        ("B-Complex with Zinc", "Capsule"),
        ("Vitamin D3 60,000 IU", "Capsule"),
        ("Calcium + Vitamin D3", "Tablet"),
        ("Cough Syrup (Dextromethorphan)", "Syrup"),
        ("Ambroxol Cough Syrup", "Syrup"),
        ("Antacid Gel", "Syrup"),
        ("Oral Rehydration Salts (ORS)", "Sachet"),
    ]
    try:
        with get_session() as session:
            count = session.query(MedicineCatalog).count()
            if count == 0:
                for name, form in common_meds:
                    session.add(MedicineCatalog(name=name, form=form))
    except Exception:
        pass


def save_consultation_and_prescription(
    patient_id: int,
    consultation_data: dict,
    medicines_data: list[dict],
    is_finalized: bool = False,
    prescription_id: Optional[int] = None,
) -> Prescription:
    """
    Save or update a consultation and its associated prescription with medicine items.
    """
    if not patient_id:
        raise PrescriptionServiceError("Patient must be selected.")

    if is_finalized and not medicines_data and not consultation_data.get("diagnosis"):
        raise PrescriptionServiceError("A finalized prescription should contain at least a diagnosis or medicines.")

    with get_session() as session:
        # Check if updating an existing prescription
        presc: Optional[Prescription] = None
        consultation: Optional[Consultation] = None

        if prescription_id:
            presc = (
                session.query(Prescription)
                .options(joinedload(Prescription.consultation), joinedload(Prescription.items))
                .filter(Prescription.id == prescription_id)
                .first()
            )
            if not presc:
                raise PrescriptionServiceError("Prescription record not found.")
            if presc.status == "Finalized":
                raise PrescriptionServiceError("Finalized prescriptions cannot be modified. Create a new consultation instead.")
            consultation = presc.consultation

        if consultation is None:
            # Parse or set consultation date
            c_date_val = consultation_data.get("consultation_date")
            if isinstance(c_date_val, str):
                try:
                    c_date = datetime.fromisoformat(c_date_val)
                except ValueError:
                    c_date = datetime.now()
            elif isinstance(c_date_val, datetime):
                c_date = c_date_val
            else:
                c_date = datetime.now()

            consultation = Consultation(
                patient_id=patient_id,
                consultation_date=c_date,
            )
            session.add(consultation)
            session.flush()

        # Update consultation clinical fields
        consultation.chief_complaints = (consultation_data.get("chief_complaints") or "").strip() or None
        consultation.observations = (consultation_data.get("observations") or "").strip() or None
        consultation.temperature = (consultation_data.get("temperature") or "").strip() or None
        consultation.blood_pressure = (consultation_data.get("blood_pressure") or "").strip() or None
        consultation.pulse = (consultation_data.get("pulse") or "").strip() or None
        consultation.weight = (consultation_data.get("weight") or "").strip() or None
        consultation.investigations = (consultation_data.get("investigations") or "").strip() or None
        consultation.diagnosis = (consultation_data.get("diagnosis") or "").strip() or None
        consultation.remarks = (consultation_data.get("remarks") or "").strip() or None
        consultation.follow_up_date = (consultation_data.get("follow_up_date") or "").strip() or None

        if presc is None:
            presc_code = _next_prescription_code(session)
            presc = Prescription(
                prescription_code=presc_code,
                patient_id=patient_id,
                consultation_id=consultation.id,
                status="Finalized" if is_finalized else "Draft",
                finalized_at=datetime.now() if is_finalized else None,
            )
            session.add(presc)
            session.flush()
        else:
            presc.status = "Finalized" if is_finalized else "Draft"
            if is_finalized and not presc.finalized_at:
                presc.finalized_at = datetime.now()
            # Clear existing items
            presc.items.clear()
            session.flush()

        # Add medicine items
        for idx, m_data in enumerate(medicines_data):
            name = (m_data.get("medicine_name") or "").strip()
            if not name:
                continue  # skip empty rows

            item = PrescriptionItem(
                order_index=idx,
                medicine_name=name,
                strength_form=(m_data.get("strength_form") or "").strip() or None,
                dosage=(m_data.get("dosage") or "").strip() or None,
                duration=(m_data.get("duration") or "").strip() or None,
                measure_unit=(m_data.get("measure_unit") or "").strip() or None,
                instructions=(m_data.get("instructions") or "").strip() or None,
            )
            presc.items.append(item)
            # Add to catalog for future auto-complete if not present
            add_medicine_to_catalog(name, item.strength_form)

        session.flush()
        # Eagerly load everything before session closes
        final_obj = (
            session.query(Prescription)
            .options(
                joinedload(Prescription.consultation),
                joinedload(Prescription.items),
                joinedload(Prescription.patient),
            )
            .filter(Prescription.id == presc.id)
            .first()
        )
        session.expunge_all()
        return final_obj


def get_prescription_by_id(prescription_id: int) -> Optional[Prescription]:
    """Retrieve prescription with all items, consultation, and patient loaded."""
    with get_session() as session:
        presc = (
            session.query(Prescription)
            .options(
                joinedload(Prescription.consultation),
                joinedload(Prescription.items),
                joinedload(Prescription.patient),
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )
        if presc:
            session.expunge_all()
        return presc


def get_patient_consultations(patient_id: int) -> list[Consultation]:
    """Retrieve all consultations for a patient, latest first."""
    with get_session() as session:
        items = (
            session.query(Consultation)
            .options(
                joinedload(Consultation.prescriptions).joinedload(Prescription.items),
                joinedload(Consultation.prescriptions).joinedload(Prescription.patient),
            )
            .filter(Consultation.patient_id == patient_id)
            .order_by(Consultation.consultation_date.desc(), Consultation.id.desc())
            .all()
        )
        session.expunge_all()
        return items


def search_all_prescriptions(query: str = "", status_filter: str = "All") -> list[Prescription]:
    """
    Search all prescriptions by:
    - Patient Name
    - Patient Code (e.g. PT-00001)
    - Prescription Code (e.g. RX-2026-0001)
    - Date string (YYYY-MM-DD or partial)
    - Status ("All", "Finalized", "Draft")
    """
    from sqlalchemy import or_
    from clinic_app.models.patient import Patient

    with get_session() as session:
        base = (
            session.query(Prescription)
            .join(Prescription.patient)
            .join(Prescription.consultation)
            .options(
                joinedload(Prescription.patient),
                joinedload(Prescription.consultation),
                joinedload(Prescription.items),
            )
        )

        if status_filter and status_filter != "All":
            base = base.filter(Prescription.status == status_filter)

        q_clean = query.strip()
        if q_clean:
            pattern = f"%{q_clean}%"
            base = base.filter(
                or_(
                    Patient.full_name.ilike(pattern),
                    Patient.patient_code.ilike(pattern),
                    Prescription.prescription_code.ilike(pattern),
                    Consultation.diagnosis.ilike(pattern),
                )
            )

        results = base.order_by(Prescription.created_at.desc(), Prescription.id.desc()).all()
        session.expunge_all()
        return results
