"""
New Prescription view — placeholder for Phase 1.
Full implementation in Phase 3.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class PrescriptionFormView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("New Prescription")
        title.setObjectName("page_title")
        layout.addWidget(title)

        sub = QLabel("Select a patient and enter consultation details.")
        sub.setObjectName("page_subtitle")
        layout.addWidget(sub)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(32, 40, 32, 40)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("📝")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")

        note = QLabel(
            "Prescription creation will be available in Phase 3.\n"
            "You will be able to record consultations and add multiple medicines."
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setObjectName("page_subtitle")
        note.setWordWrap(True)

        inner.addWidget(icon)
        inner.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()
