"""
PatientFormPage — reusable add / edit patient form.

Used both for new patient registration and editing existing records.
Emits:
    saved(patient)      — after a successful save
    cancelled()         — when the user clicks Cancel
"""

from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from clinic_app.models.patient import Patient
from clinic_app.services import patient_service
from clinic_app.services.patient_service import PatientServiceError
from clinic_app.ui.message_bar import MessageBar


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Duplicate warning dialog (inline widget, not a QDialog)
# ---------------------------------------------------------------------------

class _DuplicateWarning(QFrame):
    """
    Shown inline in the form when possible duplicates are detected.
    Signals:
        open_existing(int)  — user wants to open the matched patient (by id)
        proceed()           — user wants to save the new record anyway
        dismissed()         — user dismissed the warning
    """
    open_existing  = Signal(int)
    proceed        = Signal()
    dismissed      = Signal()

    def __init__(self, matches: list[Patient], parent=None):
        super().__init__(parent)
        self.setObjectName("msg_warning")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        icon_row = QHBoxLayout()
        icon_row.addWidget(QLabel("⚠️  Possible duplicate patient found"))
        icon_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setObjectName("secondary_btn")
        close_btn.clicked.connect(self.dismissed)
        close_btn.clicked.connect(self.hide)
        icon_row.addWidget(close_btn)
        layout.addLayout(icon_row)

        for m in matches[:3]:
            row = QHBoxLayout()
            info = QLabel(
                f"<b>{m.patient_code}</b> — {m.full_name}  "
                f"| {m.phone or '—'}  | Registered {m.created_at.strftime('%d %b %Y') if m.created_at else '—'}"
            )
            info.setWordWrap(True)
            open_btn = QPushButton("Open this patient")
            open_btn.setObjectName("secondary_btn")
            open_btn.setFixedWidth(140)
            open_btn.clicked.connect(lambda _, pid=m.id: self.open_existing.emit(pid))
            row.addWidget(info, stretch=1)
            row.addWidget(open_btn)
            layout.addLayout(row)

        proceed_btn = QPushButton("No, create a new record anyway →")
        proceed_btn.setObjectName("danger_btn")
        proceed_btn.clicked.connect(self.proceed)
        proceed_btn.clicked.connect(self.hide)
        layout.addWidget(proceed_btn)


# ---------------------------------------------------------------------------
# Main form widget
# ---------------------------------------------------------------------------

class PatientFormPage(QWidget):
    saved     = Signal(object)   # Patient
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._edit_mode = False        # False = add, True = edit
        self._patient_id: int | None = None
        self._duplicate_check_done = False
        self._build_ui()

    # ------------------------------------------------------------------
    def load_for_add(self):
        """Reset the form to register a brand-new patient."""
        self._edit_mode = False
        self._patient_id = None
        self._duplicate_check_done = False
        self._page_title.setText("Register New Patient")
        self._page_sub.setText("Fill in the patient's details and click Save Patient.")
        self._save_btn.setText("💾  Save Patient")
        self._patient_id_lbl.setText("Will be generated automatically")
        self._clear_fields()
        if hasattr(self, "_dup_warning") and self._dup_warning:
            self._dup_warning.hide()

    def load_for_edit(self, patient: Patient):
        """Pre-populate the form for editing an existing patient."""
        self._edit_mode = True
        self._patient_id = patient.id
        self._duplicate_check_done = True
        self._page_title.setText("Edit Patient Details")
        self._page_sub.setText(
            f"Editing record for {patient.patient_code} — "
            "Patient ID and registration date cannot be changed."
        )
        self._save_btn.setText("💾  Save Changes")
        self._patient_id_lbl.setText(patient.patient_code)
        self._populate_fields(patient)
        if hasattr(self, "_dup_warning") and self._dup_warning:
            self._dup_warning.hide()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Page heading
        self._page_title = QLabel("Register New Patient")
        self._page_title.setObjectName("page_title")
        self._page_sub   = QLabel("")
        self._page_sub.setObjectName("page_subtitle")

        layout.addWidget(self._page_title)
        layout.addWidget(self._page_sub)

        # Duplicate warning placeholder
        self._dup_warning: _DuplicateWarning | None = None
        self._dup_slot = QVBoxLayout()
        layout.addLayout(self._dup_slot)

        # ---- Section: Patient Information --------------------------------
        layout.addWidget(_section_header("Patient Information"))
        layout.addWidget(_separator())

        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setColumnMinimumWidth(1, 20)

        # Patient ID (read-only)
        grid.addWidget(_form_label("Patient ID"), 0, 0)
        self._patient_id_lbl = QLabel("Will be generated automatically")
        self._patient_id_lbl.setObjectName("form_readonly")
        grid.addWidget(self._patient_id_lbl, 0, 1, 1, 3)

        # Full name
        grid.addWidget(_form_label("Full Name  ✱"), 1, 0)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Ramesh Kumar")
        self._name_edit.setMinimumWidth(300)
        grid.addWidget(self._name_edit, 1, 1, 1, 3)

        # Gender
        grid.addWidget(_form_label("Gender"), 2, 0)
        self._gender_combo = QComboBox()
        self._gender_combo.addItems(
            ["Male", "Female", "Other", "Prefer not to say / Not recorded"]
        )
        grid.addWidget(self._gender_combo, 2, 1)

        # DOB / Age
        grid.addWidget(_form_label("Date of Birth"), 3, 0)

        self._dob_unknown = QCheckBox("Date of birth not known — enter age instead")
        self._dob_edit = QDateEdit()
        self._dob_edit.setCalendarPopup(True)
        self._dob_edit.setDisplayFormat("dd MMM yyyy")
        self._dob_edit.setDate(date(2000, 1, 1))
        self._dob_edit.setMaximumDate(date.today())

        self._age_spin = QSpinBox()
        self._age_spin.setRange(0, 120)
        self._age_spin.setSuffix(" years")
        self._age_spin.setVisible(False)

        self._dob_unknown.toggled.connect(self._toggle_dob_age)

        dob_row = QHBoxLayout()
        dob_row.setSpacing(10)
        dob_row.addWidget(self._dob_edit)
        dob_row.addWidget(self._age_spin)
        dob_row.addWidget(self._dob_unknown)
        dob_row.addStretch()

        grid.addLayout(dob_row, 3, 1, 1, 3)
        layout.addLayout(grid)

        # ---- Section: Contact Details ------------------------------------
        layout.addSpacing(10)
        layout.addWidget(_section_header("Contact Details"))
        layout.addWidget(_separator())

        grid2 = QGridLayout()
        grid2.setSpacing(14)

        grid2.addWidget(_form_label("Phone Number"), 0, 0)
        self._phone_edit = QLineEdit()
        self._phone_edit.setPlaceholderText("e.g. 9876543210")
        grid2.addWidget(self._phone_edit, 0, 1)

        grid2.addWidget(_form_label("Address"), 1, 0)
        self._address_edit = QTextEdit()
        self._address_edit.setPlaceholderText("Street, City, State — PIN")
        self._address_edit.setFixedHeight(70)
        grid2.addWidget(self._address_edit, 1, 1)

        grid2.addWidget(_form_label("Emergency Contact"), 2, 0)
        self._emergency_edit = QLineEdit()
        self._emergency_edit.setPlaceholderText("Name and phone number")
        grid2.addWidget(self._emergency_edit, 2, 1)

        layout.addLayout(grid2)

        # ---- Section: Additional Notes -----------------------------------
        layout.addSpacing(10)
        layout.addWidget(_section_header("Additional Notes"))
        layout.addWidget(_separator())

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText(
            "Optional: known allergies, chronic conditions, etc."
        )
        self._notes_edit.setFixedHeight(80)
        layout.addWidget(self._notes_edit)

        # ---- Message bar (validation feedback) ---------------------------
        self._msg_slot = QVBoxLayout()
        layout.addLayout(self._msg_slot)

        # ---- Action buttons ----------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._cancel_btn = QPushButton("← Back")
        self._cancel_btn.setObjectName("secondary_btn")
        self._cancel_btn.clicked.connect(self.cancelled)

        self._save_btn = QPushButton("💾  Save Patient")
        self._save_btn.setObjectName("primary_btn")
        self._save_btn.setMinimumWidth(160)
        self._save_btn.clicked.connect(self._on_save_clicked)

        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    def _toggle_dob_age(self, unknown: bool):
        self._dob_edit.setVisible(not unknown)
        self._age_spin.setVisible(unknown)

    # ------------------------------------------------------------------
    def _clear_fields(self):
        self._name_edit.clear()
        self._gender_combo.setCurrentIndex(0)
        self._dob_unknown.setChecked(False)
        self._dob_edit.setDate(date(2000, 1, 1))
        self._age_spin.setValue(0)
        self._phone_edit.clear()
        self._address_edit.clear()
        self._emergency_edit.clear()
        self._notes_edit.clear()
        self._clear_messages()

    def _populate_fields(self, p: Patient):
        self._name_edit.setText(p.full_name)
        gender_map = {
            "Male": 0, "Female": 1, "Other": 2
        }
        idx = gender_map.get(p.gender, 3)
        self._gender_combo.setCurrentIndex(idx)

        if p.date_of_birth:
            self._dob_unknown.setChecked(False)
            try:
                self._dob_edit.setDate(date.fromisoformat(p.date_of_birth))
            except ValueError:
                pass
        elif p.age_at_registration is not None:
            self._dob_unknown.setChecked(True)
            self._age_spin.setValue(p.age_at_registration)
        else:
            self._dob_unknown.setChecked(False)

        self._phone_edit.setText(p.phone or "")
        self._address_edit.setPlainText(p.address or "")
        self._emergency_edit.setText(p.emergency_contact or "")
        self._notes_edit.setPlainText(p.notes or "")

    # ------------------------------------------------------------------
    def _collect_data(self) -> dict:
        dob = None
        age = None
        if self._dob_unknown.isChecked():
            age = self._age_spin.value() or None
        else:
            d = self._dob_edit.date().toPython()
            if d != date(2000, 1, 1):   # treat default as "not provided"
                dob = d.isoformat()

        return {
            "full_name":           self._name_edit.text(),
            "gender":              self._gender_combo.currentText(),
            "date_of_birth":       dob,
            "age_at_registration": age,
            "phone":               self._phone_edit.text(),
            "address":             self._address_edit.toPlainText(),
            "emergency_contact":   self._emergency_edit.text(),
            "notes":               self._notes_edit.toPlainText(),
        }

    # ------------------------------------------------------------------
    def _on_save_clicked(self):
        self._clear_messages()
        data = self._collect_data()

        # Duplicate check (only on new patient, first attempt)
        if not self._edit_mode and not self._duplicate_check_done:
            duplicates = patient_service.find_possible_duplicates(
                data.get("full_name", ""), data.get("phone", "")
            )
            if duplicates:
                self._show_duplicate_warning(duplicates)
                return   # wait for user decision

        self._do_save(data)

    def _do_save(self, data: dict):
        try:
            if self._edit_mode:
                patient = patient_service.update_patient(self._patient_id, data)
            else:
                patient = patient_service.create_patient(data)
        except PatientServiceError as exc:
            self._show_error(str(exc))
            return
        except Exception:
            self._show_error(
                "An unexpected error occurred. Please try again."
            )
            return

        self.saved.emit(patient)

    # ------------------------------------------------------------------
    def _show_duplicate_warning(self, matches: list[Patient]):
        # Remove old warning if any
        if self._dup_warning:
            self._dup_slot.removeWidget(self._dup_warning)
            self._dup_warning.deleteLater()

        self._dup_warning = _DuplicateWarning(matches)
        self._dup_warning.proceed.connect(self._on_duplicate_proceed)
        self._dup_warning.open_existing.connect(self._on_open_existing)
        self._dup_warning.dismissed.connect(lambda: setattr(self, "_dup_warning", None))
        self._dup_slot.addWidget(self._dup_warning)

    def _on_duplicate_proceed(self):
        self._duplicate_check_done = True
        self._do_save(self._collect_data())

    def _on_open_existing(self, patient_id: int):
        """Signal upward that user wants to view an existing patient."""
        # We emit cancelled and let PatientsView handle it; pass the id via property
        self._requested_patient_id = patient_id
        self.cancelled.emit()   # PatientsView intercepts this

    # ------------------------------------------------------------------
    def _show_error(self, msg: str):
        self._clear_messages()
        bar = MessageBar(msg, MessageBar.ERROR)
        self._msg_slot.addWidget(bar)

    def _clear_messages(self):
        while self._msg_slot.count():
            item = self._msg_slot.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
