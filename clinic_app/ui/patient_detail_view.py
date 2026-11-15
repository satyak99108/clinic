"""
PatientDetailView — read-only patient profile page.

Displays all patient information and provides action buttons:
  • Edit Details
  • New Consultation / Prescription  (placeholder; enabled in Phase 3)
  • Back to patient list

Emits:
    edit_requested(patient)        — user clicked Edit
    back_requested()               — user clicked Back
    new_prescription_requested(patient)  — user clicked New Prescription
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from clinic_app.models.patient import Patient
from clinic_app.services import prescription_service


def _info_row(label: str, value: str) -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setObjectName("form_label")
    lbl.setFixedWidth(160)

    val = QLabel(value or "—")
    val.setWordWrap(True)
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    row.addWidget(lbl)
    row.addWidget(val, stretch=1)
    return row


class PatientDetailView(QWidget):
    edit_requested            = Signal(object)   # Patient
    back_requested            = Signal()
    new_prescription_requested = Signal(object)  # Patient (Phase 3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._patient: Patient | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    def load_patient(self, patient: Patient):
        """Populate the view with the given patient's data."""
        self._patient = patient
        self._refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(20)

        # Placeholder until load_patient() is called
        self._layout.addWidget(QLabel("No patient loaded."))

        scroll.setWidget(self._content)
        outer.addWidget(scroll)

    def _refresh(self):
        p = self._patient
        if p is None:
            return

        # Clear old content
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear sub-layouts
                sub = item.layout()
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        layout = self._layout

        # ---- Header row -------------------------------------------
        header = QHBoxLayout()

        back_btn = QPushButton("← Back to Patients")
        back_btn.setObjectName("secondary_btn")
        back_btn.clicked.connect(self.back_requested)

        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

        # ---- Patient badge ----------------------------------------
        badge = QFrame()
        badge.setObjectName("card")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(24, 20, 24, 20)
        badge_layout.setSpacing(20)

        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 48px;")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedWidth(72)

        name_col = QVBoxLayout()
        name_col.setSpacing(4)

        name_lbl = QLabel(p.full_name)
        name_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #1C2340;")

        code_lbl = QLabel(p.patient_code)
        code_lbl.setStyleSheet(
            "font-size: 13px; color: #3B5BDB; font-weight: bold; "
            "background: #EEF2FF; border-radius: 6px; padding: 2px 8px;"
        )
        code_lbl.setFixedWidth(100)

        reg_lbl = QLabel(
            f"Registered: {p.created_at.strftime('%d %b %Y') if p.created_at else '—'}"
        )
        reg_lbl.setObjectName("page_subtitle")

        name_col.addWidget(name_lbl)
        name_col.addWidget(code_lbl)
        name_col.addWidget(reg_lbl)

        # Action buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        edit_btn = QPushButton("✏️  Edit Details")
        edit_btn.setObjectName("primary_btn")
        edit_btn.setMinimumWidth(160)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._patient))

        presc_btn = QPushButton("📝  New Prescription")
        presc_btn.setObjectName("secondary_btn")
        presc_btn.setMinimumWidth(160)
        presc_btn.setToolTip("Available in Phase 3")
        presc_btn.clicked.connect(
            lambda: self.new_prescription_requested.emit(self._patient)
        )

        btn_col.addWidget(edit_btn)
        btn_col.addWidget(presc_btn)

        badge_layout.addWidget(avatar)
        badge_layout.addLayout(name_col, stretch=1)
        badge_layout.addLayout(btn_col)

        layout.addWidget(badge)

        # ---- Patient information card ----------------------------------
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 20, 24, 20)
        info_layout.setSpacing(14)

        info_title = QLabel("Patient Information")
        info_title.setObjectName("section_header")
        info_layout.addWidget(info_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        info_layout.addWidget(sep)

        rows = [
            ("Gender",           p.gender),
            ("Age / Date of Birth", p.display_age()),
            ("Phone",            p.phone or "—"),
            ("Address",          p.address or "—"),
            ("Emergency Contact", p.emergency_contact or "—"),
        ]
        for label, value in rows:
            info_layout.addLayout(_info_row(label, value))

        if p.notes:
            sep2 = QFrame()
            sep2.setFrameShape(QFrame.Shape.HLine)
            info_layout.addWidget(sep2)
            info_layout.addLayout(_info_row("Notes", p.notes))

        updated = p.updated_at.strftime('%d %b %Y, %H:%M') if p.updated_at else "—"
        info_layout.addLayout(_info_row("Last Updated", updated))

        layout.addWidget(info_card)

        # ---- Consultation history ------------------------------------
        hist_card = QFrame()
        hist_card.setObjectName("card")
        hist_layout = QVBoxLayout(hist_card)
        hist_layout.setContentsMargins(24, 20, 24, 20)
        hist_layout.setSpacing(12)

        hist_title = QLabel("Consultation & Prescription History")
        hist_title.setObjectName("section_header")
        hist_layout.addWidget(hist_title)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        hist_layout.addWidget(sep3)

        consultations = prescription_service.get_patient_consultations(p.id)
        if not consultations:
            empty = QLabel(
                "No consultations recorded yet.\n"
                "Use New Prescription to start the first consultation for this patient."
            )
            empty.setObjectName("page_subtitle")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 16, 0, 16)
            hist_layout.addWidget(empty)
        else:
            for c in consultations:
                c_box = QFrame()
                c_box.setStyleSheet("background-color: #F7F8FC; border-radius: 8px; padding: 12px;")
                c_box_layout = QVBoxLayout(c_box)
                c_box_layout.setSpacing(6)

                date_str = c.consultation_date.strftime("%d %b %Y, %I:%M %p") if c.consultation_date else "—"
                header_lbl = QLabel(f"<b>Date:</b> {date_str}  |  <b>Diagnosis:</b> {c.diagnosis or 'Not recorded'}")
                header_lbl.setStyleSheet("font-size: 13px; color: #1C2340;")
                c_box_layout.addWidget(header_lbl)

                if c.chief_complaints:
                    c_box_layout.addWidget(QLabel(f"<b>Complaints:</b> {c.chief_complaints}"))

                # Prescriptions under this consultation
                if c.prescriptions:
                    for rx in c.prescriptions:
                        status_color = "#2F9E44" if rx.status == "Finalized" else "#E67700"
                        rx_lbl = QLabel(
                            f"<b>Rx Code:</b> {rx.prescription_code} "
                            f"<span style='color:{status_color}; font-weight:bold;'>[{rx.status}]</span> "
                            f"({len(rx.items)} medicine{'s' if len(rx.items) != 1 else ''})"
                        )
                        c_box_layout.addWidget(rx_lbl)

                        if rx.items:
                            med_summary = ", ".join([f"{item.medicine_name} ({item.dosage or '—'})" for item in rx.items])
                            m_lbl = QLabel(f"<b>Medicines:</b> {med_summary}")
                            m_lbl.setWordWrap(True)
                            c_box_layout.addWidget(m_lbl)

                hist_layout.addWidget(c_box)

        layout.addWidget(hist_card)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
