"""
PrescriptionFormView — Consultation & Prescription Builder.
Supports:
- Patient selection & display
- Clinical consultation entry (complaints, vitals, diagnosis, investigations, follow-up)
- Dynamic medicine rows (add/remove, dosage, instructions, catalog autocomplete)
- Save Draft
- Review & Finalize Prescription
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinic_app.models.patient import Patient
from clinic_app.models.prescription import Prescription
from clinic_app.services import patient_service, prescription_service
from clinic_app.services.prescription_service import PrescriptionServiceError
from clinic_app.ui.medicine_row_widget import MedicineRowWidget
from clinic_app.ui.message_bar import MessageBar
from clinic_app.ui.prescription_preview_dialog import PrescriptionPreviewDialog
from clinic_app.ui.prescription_review_dialog import PrescriptionReviewDialog


def _form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("form_label")
    return lbl


def _section_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("section_header")
    return lbl


def _separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    return sep


class PrescriptionFormView(QWidget):
    prescription_saved = Signal(object)  # Prescription

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_patient: Optional[Patient] = None
        self._current_prescription_id: Optional[int] = None
        self._medicine_rows: list[MedicineRowWidget] = []
        self._medicine_suggestions: list[str] = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(18)

        # Header
        self._title_lbl = QLabel("New Prescription")
        self._title_lbl.setObjectName("page_title")
        self._sub_lbl = QLabel("Record consultation details and prescribe medicines.")
        self._sub_lbl.setObjectName("page_subtitle")
        self._layout.addWidget(self._title_lbl)
        self._layout.addWidget(self._sub_lbl)

        # Message bar slot
        self._msg_slot = QVBoxLayout()
        self._layout.addLayout(self._msg_slot)

        # ---- Section 1: Patient Selection & Details ------------------------
        self._layout.addWidget(_section_header("1. Patient Selection"))
        self._layout.addWidget(_separator())

        p_row = QHBoxLayout()
        p_row.setSpacing(12)

        self._patient_combo = QComboBox()
        self._patient_combo.setMinimumWidth(350)
        self._patient_combo.currentIndexChanged.connect(self._on_patient_dropdown_changed)

        refresh_pts_btn = QPushButton("🔄 Refresh Patients")
        refresh_pts_btn.setObjectName("secondary_btn")
        refresh_pts_btn.clicked.connect(self._reload_patients_dropdown)

        p_row.addWidget(QLabel("Select Patient: ✱"))
        p_row.addWidget(self._patient_combo, stretch=1)
        p_row.addWidget(refresh_pts_btn)
        self._layout.addLayout(p_row)

        # Patient Info Card
        self._patient_badge = QFrame()
        self._patient_badge.setObjectName("card")
        pb_layout = QHBoxLayout(self._patient_badge)
        pb_layout.setContentsMargins(16, 12, 16, 12)
        self._patient_info_lbl = QLabel("No patient selected.")
        self._patient_info_lbl.setStyleSheet("color: #4A5074; font-size: 13px;")
        pb_layout.addWidget(self._patient_info_lbl)
        self._layout.addWidget(self._patient_badge)

        # ---- Section 2: Vitals & Clinical Examination ---------------------
        self._layout.addSpacing(6)
        self._layout.addWidget(_section_header("2. Vitals & Clinical Examination"))
        self._layout.addWidget(_separator())

        vitals_grid = QGridLayout()
        vitals_grid.setSpacing(12)

        self._temp_edit = QLineEdit()
        self._temp_edit.setPlaceholderText("e.g. 98.6 °F")
        self._bp_edit = QLineEdit()
        self._bp_edit.setPlaceholderText("e.g. 120/80 mmHg")
        self._pulse_edit = QLineEdit()
        self._pulse_edit.setPlaceholderText("e.g. 72 bpm")
        self._weight_edit = QLineEdit()
        self._weight_edit.setPlaceholderText("e.g. 68 kg")

        vitals_grid.addWidget(_form_label("Temperature:"), 0, 0)
        vitals_grid.addWidget(self._temp_edit, 0, 1)
        vitals_grid.addWidget(_form_label("Blood Pressure:"), 0, 2)
        vitals_grid.addWidget(self._bp_edit, 0, 3)

        vitals_grid.addWidget(_form_label("Pulse Rate:"), 1, 0)
        vitals_grid.addWidget(self._pulse_edit, 1, 1)
        vitals_grid.addWidget(_form_label("Weight:"), 1, 2)
        vitals_grid.addWidget(self._weight_edit, 1, 3)

        self._layout.addLayout(vitals_grid)

        # Clinical Notes
        notes_grid = QGridLayout()
        notes_grid.setSpacing(12)

        self._complaints_edit = QTextEdit()
        self._complaints_edit.setPlaceholderText("Chief complaints (e.g. Fever for 3 days, cough, headache)...")
        self._complaints_edit.setFixedHeight(65)

        self._diagnosis_edit = QTextEdit()
        self._diagnosis_edit.setPlaceholderText("Provisional / Final diagnosis (e.g. Acute Viral Bronchitis)...")
        self._diagnosis_edit.setFixedHeight(65)

        self._observations_edit = QTextEdit()
        self._observations_edit.setPlaceholderText("Clinical observations / Examination notes...")
        self._observations_edit.setFixedHeight(65)

        self._investigations_edit = QTextEdit()
        self._investigations_edit.setPlaceholderText("Suggested investigations / Lab tests (e.g. CBC, Chest X-Ray)...")
        self._investigations_edit.setFixedHeight(65)

        notes_grid.addWidget(_form_label("Chief Complaints:"), 0, 0)
        notes_grid.addWidget(self._complaints_edit, 0, 1)
        notes_grid.addWidget(_form_label("Diagnosis: ✱"), 0, 2)
        notes_grid.addWidget(self._diagnosis_edit, 0, 3)

        notes_grid.addWidget(_form_label("Observations:"), 1, 0)
        notes_grid.addWidget(self._observations_edit, 1, 1)
        notes_grid.addWidget(_form_label("Investigations:"), 1, 2)
        notes_grid.addWidget(self._investigations_edit, 1, 3)

        self._layout.addLayout(notes_grid)

        # ---- Section 3: Prescribed Medicines (Rx) -------------------------
        self._layout.addSpacing(6)
        rx_header_row = QHBoxLayout()
        rx_header_row.addWidget(_section_header("3. Prescribed Medicines (Rx)"))
        rx_header_row.addStretch()

        add_med_btn = QPushButton("➕ Add Medicine")
        add_med_btn.setObjectName("secondary_btn")
        add_med_btn.clicked.connect(self._add_medicine_row)
        rx_header_row.addWidget(add_med_btn)
        self._layout.addLayout(rx_header_row)
        self._layout.addWidget(_separator())

        self._meds_container = QVBoxLayout()
        self._meds_container.setSpacing(10)
        self._layout.addLayout(self._meds_container)

        # Empty medicines helper label
        self._no_meds_lbl = QLabel("No medicines added yet. Click '+ Add Medicine' above to add rows.")
        self._no_meds_lbl.setObjectName("page_subtitle")
        self._no_meds_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._no_meds_lbl)

        # ---- Section 4: Follow-up & Remarks -------------------------------
        self._layout.addSpacing(6)
        self._layout.addWidget(_section_header("4. Remarks & Follow-up"))
        self._layout.addWidget(_separator())

        plan_row = QHBoxLayout()
        plan_row.setSpacing(16)

        self._remarks_edit = QLineEdit()
        self._remarks_edit.setPlaceholderText("Special instructions / dietary advice (e.g. Drink warm fluids)...")

        self._follow_up_combo = QComboBox()
        self._follow_up_combo.setEditable(True)
        self._follow_up_combo.addItems([
            "After 3 days",
            "After 5 days",
            "After 1 week",
            "After 2 weeks",
            "After 1 month",
            "As needed (SOS)",
        ])

        plan_row.addWidget(_form_label("Remarks / Advice:"))
        plan_row.addWidget(self._remarks_edit, stretch=2)
        plan_row.addWidget(_form_label("Follow-up:"))
        plan_row.addWidget(self._follow_up_combo, stretch=1)
        self._layout.addLayout(plan_row)

        # ---- Actions Bar --------------------------------------------------
        self._layout.addSpacing(10)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)

        self._clear_btn = QPushButton("Clear Form")
        self._clear_btn.setObjectName("secondary_btn")
        self._clear_btn.clicked.connect(self.reset_form)

        self._draft_btn = QPushButton("💾 Save as Draft")
        self._draft_btn.setObjectName("secondary_btn")
        self._draft_btn.clicked.connect(self._save_draft)

        self._preview_btn = QPushButton("👁 Preview Layout")
        self._preview_btn.setObjectName("secondary_btn")
        self._preview_btn.clicked.connect(self._preview_current_prescription)

        self._finalize_btn = QPushButton("✔ Review & Finalize Prescription")
        self._finalize_btn.setObjectName("primary_btn")
        self._finalize_btn.setMinimumWidth(240)
        self._finalize_btn.clicked.connect(self._finalize_prescription)

        actions_row.addWidget(self._clear_btn)
        actions_row.addStretch()
        actions_row.addWidget(self._draft_btn)
        actions_row.addWidget(self._preview_btn)
        actions_row.addWidget(self._finalize_btn)
        self._layout.addLayout(actions_row)

        self._layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def on_section_activated(self):
        """Called when this section is shown."""
        self._reload_medicine_suggestions()
        self._reload_patients_dropdown()
        if not self._medicine_rows:
            self._add_medicine_row()

    def set_patient_for_prescription(self, patient: Patient):
        """Pre-select a specific patient when navigated from Patient list/profile."""
        self.reset_form()
        self._selected_patient = patient
        self._reload_patients_dropdown(select_patient_id=patient.id)
        self._update_patient_badge()
        if not self._medicine_rows:
            self._add_medicine_row()

    def _reload_medicine_suggestions(self):
        try:
            self._medicine_suggestions = prescription_service.get_medicine_suggestions()
        except Exception:
            self._medicine_suggestions = []

    def _reload_patients_dropdown(self, select_patient_id: Optional[int] = None):
        target_id = select_patient_id or (self._selected_patient.id if self._selected_patient else None)
        self._patient_combo.blockSignals(True)
        self._patient_combo.clear()
        self._patient_combo.addItem("-- Select Patient --", None)

        try:
            pts = patient_service.get_all_patients()
            target_index = 0
            for idx, p in enumerate(pts, start=1):
                label = f"{p.patient_code} — {p.full_name} ({p.phone or 'No phone'})"
                self._patient_combo.addItem(label, p.id)
                if target_id and p.id == target_id:
                    target_index = idx
                    self._selected_patient = p

            self._patient_combo.setCurrentIndex(target_index)
        except Exception:
            pass
        finally:
            self._patient_combo.blockSignals(False)

        self._update_patient_badge()

    def _on_patient_dropdown_changed(self, index: int):
        pid = self._patient_combo.currentData()
        if pid:
            self._selected_patient = patient_service.get_patient_by_id(pid)
        else:
            self._selected_patient = None
        self._update_patient_badge()

    def _update_patient_badge(self):
        p = self._selected_patient
        if p:
            self._patient_info_lbl.setText(
                f"<b>{p.full_name}</b> | Patient ID: <span style='color:#3B5BDB;'>{p.patient_code}</span> | "
                f"Gender: {p.gender} | Age/DOB: {p.display_age()} | Phone: {p.phone or '—'}"
            )
        else:
            self._patient_info_lbl.setText("No patient selected. Please select a patient above.")

    def _add_medicine_row(self, data: Optional[dict] = None):
        row = MedicineRowWidget(medicine_suggestions=self._medicine_suggestions)
        row.remove_requested.connect(self._remove_medicine_row)
        if data:
            row.set_data(data)
        self._medicine_rows.append(row)
        self._meds_container.addWidget(row)
        self._no_meds_lbl.setVisible(False)

    def _remove_medicine_row(self, row_widget: MedicineRowWidget):
        if row_widget in self._medicine_rows:
            self._medicine_rows.remove(row_widget)
            self._meds_container.removeWidget(row_widget)
            row_widget.deleteLater()
        if not self._medicine_rows:
            self._no_meds_lbl.setVisible(True)

    def _collect_data(self) -> tuple[dict, list[dict]]:
        c_data = {
            "chief_complaints": self._complaints_edit.toPlainText().strip(),
            "diagnosis": self._diagnosis_edit.toPlainText().strip(),
            "observations": self._observations_edit.toPlainText().strip(),
            "investigations": self._investigations_edit.toPlainText().strip(),
            "temperature": self._temp_edit.text().strip(),
            "blood_pressure": self._bp_edit.text().strip(),
            "pulse": self._pulse_edit.text().strip(),
            "weight": self._weight_edit.text().strip(),
            "remarks": self._remarks_edit.text().strip(),
            "follow_up_date": self._follow_up_combo.currentText().strip(),
        }
        meds = []
        for r in self._medicine_rows:
            if not r.is_empty():
                meds.append(r.get_data())
        return c_data, meds

    def _save_draft(self):
        self._clear_messages()
        if not self._selected_patient:
            self._show_error("Please select a patient before saving a draft.")
            return

        c_data, meds = self._collect_data()
        try:
            presc = prescription_service.save_consultation_and_prescription(
                patient_id=self._selected_patient.id,
                consultation_data=c_data,
                medicines_data=meds,
                is_finalized=False,
                prescription_id=self._current_prescription_id,
            )
            self._current_prescription_id = presc.id
            self._show_success(f"Prescription saved as Draft: {presc.prescription_code}")
            self.prescription_saved.emit(presc)
        except PrescriptionServiceError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error("Failed to save draft. Please check the entered data.")

    def _preview_current_prescription(self):
        """Preview current entered data using the exact clinic template."""
        self._clear_messages()
        if not self._selected_patient:
            self._show_error("Please select a patient to preview the prescription layout.")
            return

        c_data, meds = self._collect_data()
        # Create a temporary draft object in DB so it can be previewed
        try:
            presc = prescription_service.save_consultation_and_prescription(
                patient_id=self._selected_patient.id,
                consultation_data=c_data,
                medicines_data=meds,
                is_finalized=False,
                prescription_id=self._current_prescription_id,
            )
            self._current_prescription_id = presc.id
            dialog = PrescriptionPreviewDialog(presc, self)
            dialog.exec()
        except Exception as e:
            self._show_error(f"Could not open preview: {str(e)}")

    def _finalize_prescription(self):
        self._clear_messages()
        if not self._selected_patient:
            self._show_error("Please select a patient before finalizing.")
            return

        c_data, meds = self._collect_data()

        if not c_data.get("diagnosis") and not meds:
            self._show_error("Please enter a Diagnosis or at least one Medicine before finalizing.")
            return

        p = self._selected_patient
        patient_info = {
            "name": p.full_name,
            "code": p.patient_code,
            "meta": f"{p.gender}, {p.display_age()}",
        }

        # Show review dialog
        dialog = PrescriptionReviewDialog(patient_info, c_data, meds, self)
        if dialog.exec() == PrescriptionReviewDialog.DialogCode.Accepted:
            try:
                presc = prescription_service.save_consultation_and_prescription(
                    patient_id=p.id,
                    consultation_data=c_data,
                    medicines_data=meds,
                    is_finalized=True,
                    prescription_id=self._current_prescription_id,
                )
                self._show_success(
                    f"✔ Prescription finalized successfully! Code: {presc.prescription_code}. "
                    "Record is now locked and ready for printing."
                )
                self.prescription_saved.emit(presc)
                self.reset_form()

                # Automatically open the Print / PDF preview dialog!
                preview_dlg = PrescriptionPreviewDialog(presc, self)
                preview_dlg.exec()
            except PrescriptionServiceError as e:
                self._show_error(str(e))
            except Exception:
                self._show_error("Failed to finalize prescription. Please try again.")

    def reset_form(self):
        self._clear_messages()
        self._current_prescription_id = None
        self._selected_patient = None
        self._patient_combo.setCurrentIndex(0)
        self._temp_edit.clear()
        self._bp_edit.clear()
        self._pulse_edit.clear()
        self._weight_edit.clear()
        self._complaints_edit.clear()
        self._diagnosis_edit.clear()
        self._observations_edit.clear()
        self._investigations_edit.clear()
        self._remarks_edit.clear()
        self._follow_up_combo.setCurrentIndex(0)

        for r in list(self._medicine_rows):
            self._remove_medicine_row(r)
        self._medicine_rows.clear()
        self._no_meds_lbl.setVisible(True)

    def _show_success(self, msg: str):
        self._clear_messages()
        bar = MessageBar(msg, MessageBar.SUCCESS)
        bar.auto_hide(6000)
        self._msg_slot.addWidget(bar)

    def _show_error(self, msg: str):
        self._clear_messages()
        bar = MessageBar(msg, MessageBar.ERROR)
        self._msg_slot.addWidget(bar)

    def _clear_messages(self):
        while self._msg_slot.count():
            item = self._msg_slot.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
