"""
Settings view — placeholder for Phase 1.
Full implementation in Phase 6 (clinic profile, backup, security).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("page_title")
        layout.addWidget(title)

        sub = QLabel("Manage clinic details, doctor profile, and application preferences.")
        sub.setObjectName("page_subtitle")
        layout.addWidget(sub)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(32, 40, 32, 40)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("⚙️")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")

        note = QLabel(
            "Clinic settings and backup options will be available in Phase 6.\n"
            "You will be able to set clinic name, logo, doctor details, and configure backup."
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setObjectName("page_subtitle")
        note.setWordWrap(True)

        inner.addWidget(icon)
        inner.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()
