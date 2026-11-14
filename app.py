"""
app.py — Application entry point.

Run with:
    python app.py

The script bootstraps PySide6, loads the stylesheet, and opens the
main window.  No database setup is required for Phase 1.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont

from clinic_app.database.connection import init_db
from clinic_app.ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Load and apply the global QSS stylesheet."""
    qss_path = Path(__file__).parent / "clinic_app" / "resources" / "styles" / "main.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    else:
        print(f"[warn] Stylesheet not found: {qss_path}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Clinic Prescription System")
    app.setOrganizationName("Clinic")
    app.setApplicationVersion("0.1.0")

    # Use Segoe UI as the default font on Windows
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    load_stylesheet(app)

    # Initialise the database (creates tables on first run)
    init_db()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
