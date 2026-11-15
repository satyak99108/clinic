"""
MainWindow — application shell with sidebar navigation.

Navigation items:
  • Dashboard
  • Patients
  • New Prescription
  • Prescription History
  • Settings

The sidebar uses QPushButton with checkable state so the active
section is visually highlighted.  Content pages are hosted in a
QStackedWidget so switching between them is instant.
"""

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from clinic_app.ui.dashboard_view import DashboardView
from clinic_app.ui.patients_view import PatientsView
from clinic_app.ui.prescription_form import PrescriptionFormView
from clinic_app.ui.prescription_history_view import PrescriptionHistoryView
from clinic_app.ui.settings_view import SettingsView


# ---------------------------------------------------------------------------
# Navigation item descriptor
# ---------------------------------------------------------------------------
_NAV_ITEMS = [
    ("dashboard",        "🏠",  "Dashboard"),
    ("patients",         "👤",  "Patients"),
    ("new_prescription", "📝",  "New Prescription"),
    ("history",          "🔍",  "Prescription History"),
    ("settings",         "⚙️",  "Settings"),
]


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clinic Prescription System")
        self.setMinimumSize(1024, 680)
        self.resize(1280, 800)

        self._nav_buttons: dict[str, QPushButton] = {}
        self._pages: dict[str, QWidget] = {}

        self._build_ui()
        self._navigate("dashboard")          # start on the dashboard

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Root widget with horizontal split: sidebar | content
        root = QWidget()
        root.setObjectName("root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content_area())

        self.setCentralWidget(root)

        # Status bar
        status = QStatusBar()
        self.setStatusBar(status)
        self._status_label = QLabel("Ready")
        status.addWidget(self._status_label)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title block
        title_lbl = QLabel("B. D Medical Center")
        title_lbl.setObjectName("sidebar_title")

        sub_lbl = QLabel("Prescription Manager")
        sub_lbl.setObjectName("sidebar_subtitle")

        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)

        # Thin separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2A3357; margin: 0 10px;")
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Navigation buttons
        for key, icon, label in _NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setMinimumHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            self._nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Version label at bottom of sidebar
        ver = QLabel("v0.4.0 · Phase 4")
        ver.setObjectName("sidebar_subtitle")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)
        layout.addSpacing(16)

        return sidebar

    def _build_content_area(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("content_area")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()

        # Register all pages
        self._register_page("dashboard",        DashboardView())
        self._register_page("patients",         PatientsView())
        self._register_page("new_prescription", PrescriptionFormView())
        self._register_page("history",          PrescriptionHistoryView())
        self._register_page("settings",         SettingsView())

        # Connect dashboard shortcuts to navigation
        dashboard: DashboardView = self._pages["dashboard"]
        dashboard.navigate_requested.connect(self._navigate)

        # Connect PatientsView new_prescription_requested to switch to New Prescription page
        patients_page: PatientsView = self._pages["patients"]
        patients_page.new_prescription_requested.connect(self._on_start_prescription_for_patient)

        layout.addWidget(self._stack)
        return wrapper

    def _register_page(self, key: str, widget: QWidget):
        self._pages[key] = widget
        self._stack.addWidget(widget)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, key: str):
        if key not in self._pages:
            return

        # Update button states
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)

        # Switch stack
        self._stack.setCurrentWidget(self._pages[key])

        # Notify the page it became active (if it supports it)
        page = self._pages[key]
        if hasattr(page, "on_section_activated"):
            page.on_section_activated()

        # Update status bar
        label = next((lbl for k, _, lbl in _NAV_ITEMS if k == key), key)
        self._status_label.setText(f"Section: {label}")

    def _on_start_prescription_for_patient(self, patient):
        """Switch to New Prescription page and pre-select the given patient."""
        self._navigate("new_prescription")
        presc_page: PrescriptionFormView = self._pages["new_prescription"]
        presc_page.set_patient_for_prescription(patient)

    # ------------------------------------------------------------------
    # Public helpers (for future phases)
    # ------------------------------------------------------------------

    def show_status(self, message: str):
        """Update the status bar text."""
        self._status_label.setText(message)
