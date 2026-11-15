"""
PrescriptionPreviewDialog — Interactive preview, PDF export, and direct printing dialog.
Allows the doctor to see the exact formatted prescription (letterhead, clinical notes,
medicines, signature, footer) before or after finalizing.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from clinic_app.models.prescription import Prescription
from clinic_app.services import pdf_service


class PrescriptionPreviewDialog(QDialog):
    def __init__(self, prescription: Prescription, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Prescription Preview — {prescription.prescription_code}")
        self.resize(880, 850)
        self.setModal(True)

        self._prescription = prescription
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(12)

        # Header toolbar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title = QLabel(f"Prescription Preview ({self._prescription.prescription_code})")
        title.setObjectName("page_title")
        title.setStyleSheet("font-size: 18px;")

        status_tag = QLabel(f" Status: {self._prescription.status} ")
        if self._prescription.status == "Finalized":
            status_tag.setStyleSheet("background: #EBFBEE; color: #2F9E44; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
        else:
            status_tag.setStyleSheet("background: #FFF9DB; color: #E67700; font-weight: bold; border-radius: 4px; padding: 4px 8px;")

        top_bar.addWidget(title)
        top_bar.addWidget(status_tag)
        top_bar.addStretch()

        # Action buttons
        export_btn = QPushButton("💾 Save as PDF")
        export_btn.setObjectName("secondary_btn")
        export_btn.setMinimumHeight(36)
        export_btn.clicked.connect(self._export_pdf)

        print_btn = QPushButton("🖨 Print Prescription")
        print_btn.setObjectName("primary_btn")
        print_btn.setMinimumHeight(36)
        print_btn.clicked.connect(self._print_prescription)

        close_btn = QPushButton("✕ Close")
        close_btn.setObjectName("secondary_btn")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)

        top_bar.addWidget(export_btn)
        top_bar.addWidget(print_btn)
        top_bar.addWidget(close_btn)
        root_layout.addLayout(top_bar)

        # HTML Viewer
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D0D7EE; border-radius: 8px;")

        # Render HTML
        html = pdf_service.render_prescription_html(self._prescription)
        self._browser.setHtml(html)
        root_layout.addWidget(self._browser)

    def _export_pdf(self):
        default_name = f"Prescription_{self._prescription.prescription_code}_{self._prescription.patient.patient_code if self._prescription.patient else ''}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Prescription as PDF",
            str(Path.home() / default_name),
            "PDF Files (*.pdf)",
        )
        if file_path:
            try:
                pdf_service.export_prescription_pdf(self._prescription, file_path)
                QMessageBox.information(
                    self,
                    "PDF Exported",
                    f"Prescription successfully saved to:\n{file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export PDF:\n{str(e)}",
                )

    def _print_prescription(self):
        try:
            success = pdf_service.print_prescription_dialog(self._prescription, self)
            if success:
                QMessageBox.information(self, "Printing", "Print job sent successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"An error occurred while printing:\n{str(e)}")
