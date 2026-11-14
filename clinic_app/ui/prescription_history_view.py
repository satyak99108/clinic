"""
Prescription History view — placeholder for Phase 1.
Full implementation in Phase 5.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class PrescriptionHistoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Prescription History")
        title.setObjectName("page_title")
        layout.addWidget(title)

        sub = QLabel("Find and reopen past prescriptions for any patient.")
        sub.setObjectName("page_subtitle")
        layout.addWidget(sub)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(32, 40, 32, 40)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("🔍")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")

        note = QLabel(
            "Prescription history will be available in Phase 5.\n"
            "You will be able to search, view, reprint, and export past prescriptions."
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setObjectName("page_subtitle")
        note.setWordWrap(True)

        inner.addWidget(icon)
        inner.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()
