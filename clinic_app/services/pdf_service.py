"""
PDF Service — generates professional printable prescriptions
using PySide6 QTextDocument and QPdfWriter.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize, QPagedPaintDevice, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from clinic_app.models.clinic_profile import DEFAULT_CLINIC_PROFILE, ClinicProfile
from clinic_app.models.prescription import Prescription


def _get_logo_base64() -> str:
    """Return base64 data URI of the clinic logo if found, else empty string."""
    logo_path = Path(__file__).parent.parent / "resources" / "images" / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    return ""


def render_prescription_html(
    prescription: Prescription,
    clinic: ClinicProfile = DEFAULT_CLINIC_PROFILE,
) -> str:
    """
    Render prescription data into the exact HTML template.
    Uses lightweight mustache-style substitution without external deps.
    """
    tmpl_path = Path(__file__).parent.parent / "templates" / "prescription.html"
    html = tmpl_path.read_text(encoding="utf-8")

    patient = prescription.patient
    consultation = prescription.consultation
    logo_uri = _get_logo_base64()

    # Clinic details
    html = html.replace("{{clinic.name}}", clinic.name)
    html = html.replace("{{clinic.address}}", clinic.address)
    html = html.replace("{{clinic.phones}}", clinic.phones)
    html = html.replace("{{clinic.timings}}", clinic.timings)
    html = html.replace("{{clinic.closed_days}}", clinic.closed_days)

    html = html.replace("{{clinic.doctor_left.name}}", clinic.doctor_left.name)
    html = html.replace("{{clinic.doctor_left.qualifications}}", clinic.doctor_left.qualifications)
    html = html.replace("{{clinic.doctor_left.regn_no}}", clinic.doctor_left.regn_no)

    html = html.replace("{{clinic.doctor_right.name}}", clinic.doctor_right.name)
    html = html.replace("{{clinic.doctor_right.qualifications}}", clinic.doctor_right.qualifications)
    html = html.replace("{{clinic.doctor_right.regn_no}}", clinic.doctor_right.regn_no)

    # Logo block
    if logo_uri:
        html = html.replace("{{#logo_uri}}", "").replace("{{/logo_uri}}", "")
        html = html.replace("{{logo_uri}}", logo_uri)
    else:
        # Strip logo block
        import re
        html = re.sub(r"\{\{#logo_uri\}\}.*?\{\{/logo_uri\}\}", "", html, flags=re.DOTALL)

    # Patient details
    html = html.replace("{{patient.patient_code}}", patient.patient_code if patient else "—")
    html = html.replace("{{patient.full_name}}", patient.full_name if patient else "—")
    age_gen = f"{patient.display_age()} / {patient.gender}" if patient else "—"
    html = html.replace("{{patient.age_gender}}", age_gen)
    html = html.replace("{{patient.phone}}", (patient.phone or "—") if patient else "—")

    # Prescription & Consultation
    html = html.replace("{{prescription.prescription_code}}", prescription.prescription_code)
    c_date = consultation.consultation_date.strftime("%d-%m-%Y") if consultation and consultation.consultation_date else "—"
    html = html.replace("{{consultation.formatted_date}}", c_date)

    # Vitals string
    vitals_parts = []
    if consultation.temperature:
        vitals_parts.append(f"Temp: {consultation.temperature}")
    if consultation.blood_pressure:
        vitals_parts.append(f"BP: {consultation.blood_pressure}")
    if consultation.pulse:
        vitals_parts.append(f"Pulse: {consultation.pulse}")
    if consultation.weight:
        vitals_parts.append(f"Wt: {consultation.weight}")
    vitals_line = "  |  ".join(vitals_parts)

    def _replace_section(tag: str, val: Optional[str]):
        nonlocal html
        import re
        start_tag = f"{{{{#{tag}}}}}"
        end_tag = f"{{{{/{tag}}}}}"
        pattern = re.escape(start_tag) + r"(.*?)" + re.escape(end_tag)
        if val and val.strip():
            # Replace placeholder inside block and remove tags
            match = re.search(pattern, html, flags=re.DOTALL)
            if match:
                inner = match.group(1).replace(f"{{{{{tag}}}}}", val.strip())
                html = html[:match.start()] + inner + html[match.end():]
        else:
            # Remove entire block
            html = re.sub(pattern, "", html, flags=re.DOTALL)

    _replace_section("consultation.vitals_line", vitals_line)
    _replace_section("consultation.chief_complaints", consultation.chief_complaints)
    _replace_section("consultation.diagnosis", consultation.diagnosis)
    _replace_section("consultation.observations", consultation.observations)
    _replace_section("consultation.investigations", consultation.investigations)
    _replace_section("consultation.remarks", consultation.remarks)
    _replace_section("consultation.follow_up_date", consultation.follow_up_date)

    # Medicines table loop
    import re
    meds_pattern = r"\{\{#medicines\}\}(.*?)\{\{/medicines\}\}"
    med_match = re.search(meds_pattern, html, flags=re.DOTALL)
    if med_match:
        row_template = med_match.group(1)
        rendered_rows = []
        for idx, item in enumerate(prescription.items, start=1):
            r = row_template.replace("{{index}}", str(idx))
            r = r.replace("{{medicine_name}}", item.medicine_name)
            if item.strength_form:
                r = r.replace("{{#strength_form}}", "").replace("{{/strength_form}}", "")
                r = r.replace("{{strength_form}}", item.strength_form)
            else:
                r = re.sub(r"\{\{#strength_form\}\}.*?\{\{/strength_form\}\}", "", r, flags=re.DOTALL)

            r = r.replace("{{dosage}}", item.dosage or "—")
            dur = f"{item.duration or ''} {item.measure_unit or ''}".strip()
            r = r.replace("{{duration_unit}}", dur or "—")
            r = r.replace("{{instructions}}", item.instructions or "—")
            rendered_rows.append(r)

        html = html[:med_match.start()] + "\n".join(rendered_rows) + html[med_match.end():]

    return html


def export_prescription_pdf(
    prescription: Prescription,
    output_path: str | Path,
    clinic: ClinicProfile = DEFAULT_CLINIC_PROFILE,
) -> str:
    """
    Render prescription HTML and print directly to an A4 PDF document.
    Returns the absolute path to the generated PDF.
    """
    html = render_prescription_html(prescription, clinic)
    doc = QTextDocument()
    doc.setHtml(html)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(output_path))
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)

    # Set document size to match printer page rect in points
    rect = printer.pageLayout().paintRectPixels(printer.resolution())
    doc.setPageSize(QSizeF(rect.width(), rect.height()))

    doc.print_(printer)
    return str(Path(output_path).resolve())


def print_prescription_dialog(
    prescription: Prescription,
    parent=None,
    clinic: ClinicProfile = DEFAULT_CLINIC_PROFILE,
) -> bool:
    """
    Open standard Windows Print Dialog to send prescription to a physical printer or PDF printer.
    """
    from PySide6.QtPrintSupport import QPrintDialog

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)

    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle("Print Prescription")
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        html = render_prescription_html(prescription, clinic)
        doc = QTextDocument()
        doc.setHtml(html)
        rect = printer.pageLayout().paintRectPixels(printer.resolution())
        doc.setPageSize(QSizeF(rect.width(), rect.height()))
        doc.print_(printer)
        return True
    return False
