"""
MedicineRowWidget — a single editable medicine entry row.
Provides:
- Medicine name (with autocomplete from catalog)
- Form/Strength (e.g. Tab 500mg, Syp)
- Dosage (free text, e.g. 1-0-1, 1 tsp)
- Duration (e.g. 5 days, 1 month)
- Instructions (e.g. After food, Before bed)
- Remove button
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MedicineRowWidget(QFrame):
    remove_requested = Signal(object)  # self

    def __init__(self, medicine_suggestions: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("medicine_row_card")
        self._suggestions = medicine_suggestions or []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Row 1: Name, Strength/Form, and Delete button
        r1 = QHBoxLayout()
        r1.setSpacing(10)

        # Medicine Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Medicine Name (e.g. Paracetamol 650mg)")
        self._name_edit.setMinimumWidth(260)
        if self._suggestions:
            completer = QCompleter(self._suggestions, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self._name_edit.setCompleter(completer)

        # Strength / Form
        self._form_combo = QComboBox()
        self._form_combo.setEditable(True)
        self._form_combo.setFixedWidth(130)
        self._form_combo.addItems([
            "Tablet", "Capsule", "Syrup", "Injection",
            "Drops", "Ointment", "Cream", "Inhaler", "Sachet", "Lotion"
        ])

        # Remove button
        del_btn = QPushButton("✕ Remove")
        del_btn.setObjectName("danger_btn")
        del_btn.setFixedHeight(32)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        r1.addWidget(QLabel("Medicine:"))
        r1.addWidget(self._name_edit, stretch=2)
        r1.addWidget(QLabel("Form:"))
        r1.addWidget(self._form_combo)
        r1.addWidget(del_btn)
        layout.addLayout(r1)

        # Row 2: Dosage, Duration, Unit, Instructions
        r2 = QHBoxLayout()
        r2.setSpacing(10)

        # Dosage (free text, e.g. 1-0-1)
        self._dosage_edit = QLineEdit()
        self._dosage_edit.setPlaceholderText("e.g. 1-0-1 or 1 tsp")
        self._dosage_edit.setFixedWidth(140)

        # Duration
        self._duration_edit = QLineEdit()
        self._duration_edit.setPlaceholderText("e.g. 5 days")
        self._duration_edit.setFixedWidth(110)

        # Measure / Unit
        self._unit_combo = QComboBox()
        self._unit_combo.setEditable(True)
        self._unit_combo.setFixedWidth(110)
        self._unit_combo.addItems(["Tablets", "Days", "Capsules", "Bottle", "Strip", "Puffs"])

        # Instructions
        self._instructions_combo = QComboBox()
        self._instructions_combo.setEditable(True)
        self._instructions_combo.addItems([
            "After food",
            "Before food",
            "With food",
            "At bedtime",
            "Empty stomach (Morning)",
            "As needed (SOS)",
            "Every 8 hours",
        ])

        r2.addWidget(QLabel("Dosage:"))
        r2.addWidget(self._dosage_edit)
        r2.addWidget(QLabel("Duration:"))
        r2.addWidget(self._duration_edit)
        r2.addWidget(self._unit_combo)
        r2.addWidget(QLabel("Instructions:"))
        r2.addWidget(self._instructions_combo, stretch=1)
        layout.addLayout(r2)

    def set_data(self, data: dict):
        self._name_edit.setText(data.get("medicine_name", ""))
        form = data.get("strength_form", "")
        if form:
            idx = self._form_combo.findText(form)
            if idx >= 0:
                self._form_combo.setCurrentIndex(idx)
            else:
                self._form_combo.setEditText(form)

        self._dosage_edit.setText(data.get("dosage", ""))
        self._duration_edit.setText(data.get("duration", ""))

        unit = data.get("measure_unit", "")
        if unit:
            uidx = self._unit_combo.findText(unit)
            if uidx >= 0:
                self._unit_combo.setCurrentIndex(uidx)
            else:
                self._unit_combo.setEditText(unit)

        instr = data.get("instructions", "")
        if instr:
            iidx = self._instructions_combo.findText(instr)
            if iidx >= 0:
                self._instructions_combo.setCurrentIndex(iidx)
            else:
                self._instructions_combo.setEditText(instr)

    def get_data(self) -> dict:
        return {
            "medicine_name": self._name_edit.text().strip(),
            "strength_form": self._form_combo.currentText().strip(),
            "dosage": self._dosage_edit.text().strip(),
            "duration": self._duration_edit.text().strip(),
            "measure_unit": self._unit_combo.currentText().strip(),
            "instructions": self._instructions_combo.currentText().strip(),
        }

    def is_empty(self) -> bool:
        return not bool(self._name_edit.text().strip())
