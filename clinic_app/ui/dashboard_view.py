"""
Dashboard view — shown on application start.

Displays a greeting, quick-action shortcuts, and placeholder stat cards.
In Phase 2+ the stats will be populated from the database.
"""

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


def _stat_card(icon: str, label: str, value: str) -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setObjectName("stat_card")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    row = QHBoxLayout(card)
    row.setContentsMargins(20, 18, 20, 18)
    row.setSpacing(16)

    icon_lbl = QLabel(icon)
    icon_lbl.setObjectName("stat_icon")
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    text_col = QVBoxLayout()
    text_col.setSpacing(4)

    lbl = QLabel(label.upper())
    lbl.setObjectName("stat_label")

    val = QLabel(value)
    val.setObjectName("stat_value")

    text_col.addWidget(lbl)
    text_col.addWidget(val)

    row.addWidget(icon_lbl)
    row.addLayout(text_col)
    row.addStretch()

    return card, val


def _shortcut_button(icon: str, label: str) -> QPushButton:
    btn = QPushButton(f"  {icon}  {label}")
    btn.setObjectName("secondary_btn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    btn.setMinimumHeight(52)
    return btn


class DashboardView(QWidget):
    """Main dashboard landing page."""

    # Emitted when the user clicks a shortcut so MainWindow can switch pages.
    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        # ---- Scroll area so the content works on small screens --------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(28)

        # ---- Page heading ---------------------------------------------
        heading = QLabel("Dashboard")
        heading.setObjectName("page_title")

        sub = QLabel("Welcome back. Here is your clinic at a glance.")
        sub.setObjectName("page_subtitle")

        layout.addWidget(heading)
        layout.addWidget(sub)

        # ---- Stat cards row ------------------------------------------
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)

        c1, self._stat_pts = _stat_card("👤", "Patients Registered", "—")
        c2, self._stat_rx_today = _stat_card("📋", "Prescriptions Today", "—")
        c3, self._stat_consultations = _stat_card("📅", "Consultations Total", "—")

        stats_grid.addWidget(c1, 0, 0)
        stats_grid.addWidget(c2, 0, 1)
        stats_grid.addWidget(c3, 0, 2)

        layout.addLayout(stats_grid)

        # ---- Divider -------------------------------------------------
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ---- Quick actions -------------------------------------------
        qa_title = QLabel("Quick Actions")
        qa_title.setObjectName("page_subtitle")
        layout.addWidget(qa_title)

        btn_add   = _shortcut_button("➕", "Register New Patient")
        btn_presc = _shortcut_button("📝", "New Prescription")
        btn_hist  = _shortcut_button("🔍", "Search Prescription History")

        btn_add.clicked.connect(lambda: self.navigate_requested.emit("patients"))
        btn_presc.clicked.connect(lambda: self.navigate_requested.emit("new_prescription"))
        btn_hist.clicked.connect(lambda: self.navigate_requested.emit("history"))

        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(12)
        actions_layout.addWidget(btn_add)
        actions_layout.addWidget(btn_presc)
        actions_layout.addWidget(btn_hist)
        layout.addLayout(actions_layout)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def on_section_activated(self):
        """Refresh dashboard statistics from the database."""
        self._refresh_stats()

    def _refresh_stats(self):
        try:
            from clinic_app.database.connection import get_session
            from clinic_app.models.patient import Patient
            from clinic_app.models.consultation import Consultation
            from clinic_app.models.prescription import Prescription
            from datetime import date

            with get_session() as s:
                pt_count = s.query(Patient).filter(Patient.is_active == True).count()
                consult_count = s.query(Consultation).count()

                today_start = date.today()
                rx_today = s.query(Prescription).filter(Prescription.created_at >= today_start).count()

                self._stat_pts.setText(str(pt_count))
                self._stat_rx_today.setText(str(rx_today))
                self._stat_consultations.setText(str(consult_count))
        except Exception:
            pass
