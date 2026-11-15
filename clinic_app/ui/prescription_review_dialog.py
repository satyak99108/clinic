"""
PrescriptionReviewDialog — Modal confirmation dialog before finalizing.
Allows doctor to review all consultation notes, vitals, and prescribed medicines.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PrescriptionReviewDialog(QDialog):
    def __init__(
        self,
        patient_info: dict,
        consultation_data: dict,
        medicines: list[dict],
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Review Prescription Before Finalizing")
        self.resize(750, 650)
        self.setModal(True)

        self._patient_info = patient_info
        self._consultation = consultation_data
        self._medicines = medicines

        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        title = QLabel("Prescription Summary Review")
        title.setObjectName("page_title")
        subtitle = QLabel("Please verify clinical notes and prescribed medicines before finalizing.")
        subtitle.setObjectName("page_subtitle")
        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        # Scroll area for review details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Patient & Date Card
        p_card = QFrame()
        p_card.setObjectName("card")
        p_layout = QVBoxLayout(p_card)
        p_layout.setContentsMargins(16, 12, 16, 12)

        p_name = self._patient_info.get("name", "Unknown")
        p_code = self._patient_info.get("code", "")
        p_meta = self._patient_info.get("meta", "")
        p_lbl = QLabel(f"<b>Patient:</b> {p_name} ({p_code}) | {p_meta}")
        p_lbl.setStyleSheet("font-size: 14px; color: #1C2340;")
        p_layout.addWidget(p_lbl)
        layout.addWidget(p_card)

        # Vitals & Clinical notes
        c_card = QFrame()
        c_card.setObjectName("card")
        c_layout = QVBoxLayout(c_card)
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(8)

        vitals = []
        if self._consultation.get("temperature"):
            vitals.append(f"Temp: {self._consultation['temperature']}")
        if self._consultation.get("blood_pressure"):
            vitals.append(f"BP: {self._consultation['blood_pressure']}")
        if self._consultation.get("pulse"):
            vitals.append(f"Pulse: {self._consultation['pulse']}")
        if self._consultation.get("weight"):
            vitals.append(f"Weight: {self._consultation['weight']}")

        if vitals:
            c_layout.addWidget(QLabel(f"<b>Vitals:</b> {' | '.join(vitals)}"))

        if self._consultation.get("chief_complaints"):
            c_layout.addWidget(QLabel(f"<b>Chief Complaints:</b> {self._consultation['chief_complaints']}"))
        if self._consultation.get("diagnosis"):
            c_layout.addWidget(QLabel(f"<b>Diagnosis:</b> {self._consultation['diagnosis']}"))
        if self._consultation.get("observations"):
            c_layout.addWidget(QLabel(f"<b>Observations:</b> {self._consultation['observations']}"))
        if self._consultation.get("investigations"):
            c_layout.addWidget(QLabel(f"<b>Investigations:</b> {self._consultation['investigations']}"))
        if self._consultation.get("follow_up_date"):
            c_layout.addWidget(QLabel(f"<b>Follow-up Date:</b> {self._consultation['follow_up_date']}"))
        if self._consultation.get("remarks"):
            c_layout.addWidget(QLabel(f"<b>Remarks:</b> {self._consultation['remarks']}"))

        layout.addWidget(c_card)

        # Medicines Table
        m_title = QLabel(f"Prescribed Medicines ({len(self._medicines)} item{'s' if len(self._medicines) != 1 else ''}):")
        m_title.setObjectName("section_header")
        layout.addWidget(m_title)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["#", "Medicine", "Dosage", "Duration", "Instructions"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(self._medicines))

        for idx, m in enumerate(self._medicines):
            table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            name = m.get("medicine_name", "")
            form = m.get("strength_form", "")
            full_name = f"{name} ({form})" if form else name
            table.setItem(idx, 1, QTableWidgetItem(full_name))
            table.setItem(idx, 2, QTableWidgetItem(m.get("dosage", "—")))
            dur = m.get("duration", "")
            unit = m.get("measure_unit", "")
            table.setItem(idx, 3, QTableWidgetItem(f"{dur} {unit}".strip() or "—"))
            table.setItem(idx, 4, QTableWidgetItem(m.get("instructions", "—")))

        table.setMinimumHeight(180)
        layout.addWidget(table)

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

        # Warning text
        warn_lbl = QLabel(
            "⚠️ Note: Once finalized, this prescription becomes a locked clinical record. "
            "Please confirm you wish to issue it."
        )
        warn_lbl.setStyleSheet("color: #E67700; font-size: 12px; font-weight: bold;")
        root_layout.addWidget(warn_lbl)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        cancel_btn = QPushButton("Go Back & Edit")
        cancel_btn.setObjectName("secondary_btn")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("✔ Confirm & Finalize Prescription")
        confirm_btn.setObjectName("primary_btn")
        confirm_btn.clicked.connect(self.accept)

        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()
        btn_box.addWidget(confirm_btn)
        root_layout.addLayout(btn_box)
