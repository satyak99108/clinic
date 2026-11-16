"""
PrescriptionHistoryView — Search, view, reprint, and export past prescriptions.

Features:
- Instant search by Patient Name, Patient ID, Prescription Code, or Diagnosis
- Status filter: All, Finalized, Draft
- Comprehensive summary table with patient, date, status, medicines count, and diagnosis
- Actions per row:
  - 👁 View Details (Opens full read-only modal)
  - 🖨 Print / PDF (Direct print dialog or save to PDF)
- Preserves historical records safely (read-only views)
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic_app.models.prescription import Prescription
from clinic_app.services import prescription_service
from clinic_app.ui.message_bar import MessageBar
from clinic_app.ui.prescription_preview_dialog import PrescriptionPreviewDialog


class PrescriptionHistoryView(QWidget):
    # Emitted when user wishes to resume editing a draft prescription
    edit_draft_requested = Signal(object)  # Prescription

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_prescriptions: list[Prescription] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ---- Header --------------------------------------------------
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_lbl = QLabel("Prescription History")
        title_lbl.setObjectName("page_title")
        sub_lbl = QLabel("Find, inspect, reprint, or export historical consultations & prescriptions.")
        sub_lbl.setObjectName("page_subtitle")
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)

        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.setObjectName("secondary_btn")
        refresh_btn.setMinimumWidth(130)
        refresh_btn.clicked.connect(self.refresh)

        header.addLayout(title_col, stretch=1)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # ---- Search & Filters Bar ------------------------------------
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("🔍  Search by Patient Name, ID (PT-), Rx Code (RX-), or Diagnosis...")
        self._search_box.setClearButtonEnabled(True)
        self._search_box.setMinimumHeight(38)

        # Debounce typing
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._do_search)
        self._search_box.textChanged.connect(self._search_timer.start)

        # Status filter dropdown
        self._status_combo = QComboBox()
        self._status_combo.setMinimumHeight(38)
        self._status_combo.addItems(["Status: All", "Status: Finalized", "Status: Draft"])
        self._status_combo.currentIndexChanged.connect(self._do_search)

        filter_row.addWidget(self._search_box, stretch=3)
        filter_row.addWidget(self._status_combo, stretch=1)
        layout.addLayout(filter_row)

        # ---- Message Bar Slot ----------------------------------------
        self._msg_slot = QVBoxLayout()
        layout.addLayout(self._msg_slot)

        # ---- Table ---------------------------------------------------
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Rx Code", "Date", "Patient ID", "Patient Name", "Diagnosis", "Status", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._on_row_double_clicked)

        # Column widths
        self._table.setColumnWidth(0, 130)  # Rx Code
        self._table.setColumnWidth(1, 105)  # Date
        self._table.setColumnWidth(2, 100)  # Patient ID
        self._table.setColumnWidth(3, 160)  # Patient Name
        self._table.setColumnWidth(5, 105)  # Status
        self._table.setColumnWidth(6, 210)  # Actions

        layout.addWidget(self._table)

        # ---- Empty State Label ---------------------------------------
        self._empty_lbl = QLabel("No prescriptions found.")
        self._empty_lbl.setObjectName("page_subtitle")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setVisible(False)
        layout.addWidget(self._empty_lbl)

        # ---- Count Label ---------------------------------------------
        self._count_lbl = QLabel("")
        self._count_lbl.setObjectName("page_subtitle")
        layout.addWidget(self._count_lbl)

    def on_section_activated(self):
        """Called automatically when switching to Prescription History view."""
        self.refresh()

    def refresh(self):
        """Reload prescriptions from DB."""
        self._clear_messages()
        self._do_search()

    def _do_search(self):
        query = self._search_box.text().strip()
        selected_status_text = self._status_combo.currentText()
        status_filter = "All"
        if "Finalized" in selected_status_text:
            status_filter = "Finalized"
        elif "Draft" in selected_status_text:
            status_filter = "Draft"

        try:
            self._all_prescriptions = prescription_service.search_all_prescriptions(
                query=query, status_filter=status_filter
            )
            self._populate_table(self._all_prescriptions)
        except Exception as e:
            self._show_error("Failed to load prescription history. Please refresh.")

    def _populate_table(self, prescriptions: list[Prescription]):
        self._table.setRowCount(0)

        if not prescriptions:
            self._table.setVisible(False)
            self._empty_lbl.setVisible(True)
            search_txt = self._search_box.text().strip()
            msg = (
                "No prescriptions found matching your search."
                if search_txt
                else "No prescriptions recorded yet. Create a prescription to see it here."
            )
            self._empty_lbl.setText(msg)
            self._count_lbl.setText("")
            return

        self._table.setVisible(True)
        self._empty_lbl.setVisible(False)
        self._table.setRowCount(len(prescriptions))

        for row, rx in enumerate(prescriptions):
            self._table.setRowHeight(row, 50)

            patient = rx.patient
            consultation = rx.consultation

            rx_date = (
                consultation.consultation_date.strftime("%d-%m-%Y")
                if consultation and consultation.consultation_date
                else "—"
            )

            def _item(text, align=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft):
                it = QTableWidgetItem(str(text))
                it.setTextAlignment(align)
                it.setData(Qt.ItemDataRole.UserRole, rx.id)
                return it

            self._table.setItem(row, 0, _item(rx.prescription_code))
            self._table.setItem(row, 1, _item(rx_date))
            self._table.setItem(row, 2, _item(patient.patient_code if patient else "—"))
            self._table.setItem(row, 3, _item(patient.full_name if patient else "—"))
            self._table.setItem(row, 4, _item(consultation.diagnosis if consultation and consultation.diagnosis else "—"))

            # Status with colour highlight
            status_item = _item(rx.status, align=Qt.AlignmentFlag.AlignCenter)
            if rx.status == "Finalized":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self._table.setItem(row, 5, status_item)

            # Actions column widget
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            view_btn = QPushButton("👁 View")
            view_btn.setObjectName("action_btn")
            view_btn.setFixedHeight(30)
            view_btn.clicked.connect(lambda _, r_obj=rx: self._view_prescription(r_obj))
            btn_layout.addWidget(view_btn)

            print_btn = QPushButton("🖨 Print / PDF")
            print_btn.setObjectName("action_btn")
            print_btn.setFixedHeight(30)
            print_btn.clicked.connect(lambda _, r_obj=rx: self._view_prescription(r_obj))
            btn_layout.addWidget(print_btn)

            self._table.setCellWidget(row, 6, btn_widget)

        n = len(prescriptions)
        self._count_lbl.setText(f"Total: {n} prescription{'s' if n != 1 else ''}")

    def _on_row_double_clicked(self, index):
        item = self._table.item(index.row(), 0)
        if item:
            rx_id = item.data(Qt.ItemDataRole.UserRole)
            target = next((r for r in self._all_prescriptions if r.id == rx_id), None)
            if target:
                self._view_prescription(target)

    def _view_prescription(self, prescription: Prescription):
        """Open read-only inspection, printing, and PDF dialog."""
        dlg = PrescriptionPreviewDialog(prescription, self)
        dlg.exec()

    def _show_error(self, msg: str):
        self._clear_messages()
        bar = MessageBar(msg, MessageBar.ERROR)
        self._msg_slot.addWidget(bar)

    def _clear_messages(self):
        while self._msg_slot.count():
            item = self._msg_slot.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
