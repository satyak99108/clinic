"""
Notification / message bar widgets.

Usage:
    bar = MessageBar("Patient saved successfully.", MessageBar.SUCCESS)
    some_layout.addWidget(bar)
    bar.auto_hide(3000)   # disappears after 3 s
"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


class MessageBar(QFrame):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR   = "error"

    _ICONS = {SUCCESS: "✔", WARNING: "⚠", ERROR: "✖"}

    def __init__(self, text: str, kind: str = SUCCESS, parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setObjectName(f"msg_{kind}")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon = QLabel(self._ICONS.get(kind, "ℹ"))
        icon.setObjectName(f"msg_text_{kind}")
        icon.setFixedWidth(20)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel(text)
        msg.setObjectName(f"msg_text_{kind}")
        msg.setWordWrap(True)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setObjectName("secondary_btn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)

        layout.addWidget(icon)
        layout.addWidget(msg, stretch=1)
        layout.addWidget(close_btn)

    def auto_hide(self, ms: int = 4000):
        QTimer.singleShot(ms, self.hide)
