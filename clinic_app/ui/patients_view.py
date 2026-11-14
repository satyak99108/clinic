"""
PatientsView — the full Patient Management section.

Internal navigation uses a QStackedWidget:
  Page 0  →  Patient list (search, table, Add Patient button)
  Page 1  →  Add / Edit patient form
  Page 2  →  Patient detail / profile

No SQL or database concepts are exposed in any label or message.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic_app.models.patient import Patient
from clinic_app.services import patient_service
from clinic_app.services.patient_service import PatientServiceError
from clinic_app.ui.message_bar import MessageBar
from clinic_app.ui.patient_detail_view import PatientDetailView
from clinic_app.ui.patient_form import PatientFormPage


# ---------------------------------------------------------------------------
# Patient list page (page 0)
# ---------------------------------------------------------------------------

class _PatientListPage(QWidget):
    add_requested    = Signal()
    view_requested   = Signal(object)   # Patient
    edit_requested   = Signal(object)   # Patient

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_patients: list[Patient] = []
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ---- Header --------------------------------------------------
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_lbl = QLabel("Patients")
        title_lbl.setObjectName("page_title")
        sub_lbl = QLabel("Register, search, view, and edit patient records.")
        sub_lbl.setObjectName("page_subtitle")
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)

        add_btn = QPushButton("➕  Add Patient")
        add_btn.setObjectName("primary_btn")
        add_btn.setMinimumWidth(140)
        add_btn.clicked.connect(self.add_requested)

        header.addLayout(title_col, stretch=1)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # ---- Search bar ----------------------------------------------
        search_row = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText(
            "🔍   Search by name, Patient ID, or phone number…"
        )
        self._search_box.setClearButtonEnabled(True)
        self._search_box.setMinimumHeight(40)

        # Debounce: search 300 ms after last keystroke
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._do_search)
        self._search_box.textChanged.connect(self._search_timer.start)

        search_row.addWidget(self._search_box)
        layout.addLayout(search_row)

        # ---- Message slot --------------------------------------------
        self._msg_slot = QVBoxLayout()
        layout.addLayout(self._msg_slot)

        # ---- Table ---------------------------------------------------
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Patient ID", "Full Name", "Gender", "Age / DOB", "Phone", "Actions"]
        )
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._on_row_double_clicked)

        # Column widths
        self._table.setColumnWidth(0, 100)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 180)
        self._table.setColumnWidth(4, 130)
        self._table.setColumnWidth(5, 170)

        layout.addWidget(self._table)

        # ---- Empty state label ---------------------------------------
        self._empty_lbl = QLabel("No patients found.")
        self._empty_lbl.setObjectName("page_subtitle")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setVisible(False)
        layout.addWidget(self._empty_lbl)

        # ---- Count label ---------------------------------------------
        self._count_lbl = QLabel("")
        self._count_lbl.setObjectName("page_subtitle")
        layout.addWidget(self._count_lbl)

    # ------------------------------------------------------------------
    def refresh(self):
        """Reload all patients from the database and repopulate the table."""
        self._clear_messages()
        try:
            self._all_patients = patient_service.get_all_patients()
        except Exception:
            self._show_error(
                "Could not load the patient list. Please restart the application."
            )
            self._all_patients = []
        self._populate_table(self._all_patients)

    def _do_search(self):
        query = self._search_box.text().strip()
        self._clear_messages()
        try:
            results = patient_service.search_patients(query)
        except Exception:
            self._show_error("Search encountered a problem. Please try again.")
            return
        self._populate_table(results)

    # ------------------------------------------------------------------
    def _populate_table(self, patients: list[Patient]):
        self._table.setRowCount(0)

        if not patients:
            self._table.setVisible(False)
            self._empty_lbl.setVisible(True)
            msg = (
                "No patients registered yet. Click Add Patient to get started."
                if not self._search_box.text().strip()
                else f"No patients found for \"{self._search_box.text().strip()}\"."
            )
            self._empty_lbl.setText(msg)
            self._count_lbl.setText("")
            return

        self._table.setVisible(True)
        self._empty_lbl.setVisible(False)
        self._table.setRowCount(len(patients))

        for row, p in enumerate(patients):
            self._table.setRowHeight(row, 52)

            def _item(text, align=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft):
                it = QTableWidgetItem(str(text))
                it.setTextAlignment(align)
                it.setData(Qt.ItemDataRole.UserRole, p.id)
                return it

            self._table.setItem(row, 0, _item(p.patient_code))
            self._table.setItem(row, 1, _item(p.full_name))
            self._table.setItem(row, 2, _item(p.gender))
            self._table.setItem(row, 3, _item(p.display_age()))
            self._table.setItem(row, 4, _item(p.phone or "—"))

            # Action buttons in the last column
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            view_btn = QPushButton("👁 View")
            view_btn.setObjectName("secondary_btn")
            view_btn.setFixedHeight(32)
            view_btn.clicked.connect(lambda _, pt=p: self.view_requested.emit(pt))

            edit_btn = QPushButton("✏ Edit")
            edit_btn.setObjectName("secondary_btn")
            edit_btn.setFixedHeight(32)
            edit_btn.clicked.connect(lambda _, pt=p: self.edit_requested.emit(pt))

            btn_layout.addWidget(view_btn)
            btn_layout.addWidget(edit_btn)
            self._table.setCellWidget(row, 5, btn_widget)

        n = len(patients)
        self._count_lbl.setText(
            f"Showing {n} patient{'s' if n != 1 else ''}"
        )

    # ------------------------------------------------------------------
    def _on_row_double_clicked(self, index):
        item = self._table.item(index.row(), 0)
        if item:
            pid = item.data(Qt.ItemDataRole.UserRole)
            patient = next((p for p in self._all_patients if p.id == pid), None)
            if patient:
                self.view_requested.emit(patient)

    # ------------------------------------------------------------------
    def show_success(self, msg: str):
        self._clear_messages()
        bar = MessageBar(msg, MessageBar.SUCCESS)
        bar.auto_hide(4000)
        self._msg_slot.addWidget(bar)

    def _show_error(self, msg: str):
        self._clear_messages()
        bar = MessageBar(msg, MessageBar.ERROR)
        self._msg_slot.addWidget(bar)

    def _clear_messages(self):
        while self._msg_slot.count():
            item = self._msg_slot.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ---------------------------------------------------------------------------
# Top-level PatientsView (manages the internal stack)
# ---------------------------------------------------------------------------

class PatientsView(QWidget):
    """
    Container for the entire Patients section.

    Internal pages:
      0 — _list_page  (patient list + search)
      1 — _form_page  (add / edit patient)
      2 — _detail_page (view patient)
    """

    # Forwarded for Phase 3 integration
    new_prescription_requested = Signal(object)  # Patient

    _PAGE_LIST   = 0
    _PAGE_FORM   = 1
    _PAGE_DETAIL = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()

        # ---- List page -----------------------------------------------
        self._list_page = _PatientListPage()
        self._list_page.add_requested.connect(self._navigate_to_add)
        self._list_page.view_requested.connect(self._navigate_to_detail)
        self._list_page.edit_requested.connect(self._navigate_to_edit)

        # ---- Form page -----------------------------------------------
        self._form_page = PatientFormPage()
        self._form_page.saved.connect(self._on_patient_saved)
        self._form_page.cancelled.connect(self._navigate_to_list)

        # ---- Detail page ---------------------------------------------
        self._detail_page = PatientDetailView()
        self._detail_page.back_requested.connect(self._navigate_to_list)
        self._detail_page.edit_requested.connect(self._navigate_to_edit)
        self._detail_page.new_prescription_requested.connect(
            self.new_prescription_requested
        )

        self._stack.addWidget(self._list_page)    # 0
        self._stack.addWidget(self._form_page)    # 1
        self._stack.addWidget(self._detail_page)  # 2

        layout.addWidget(self._stack)

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _navigate_to_list(self):
        self._stack.setCurrentIndex(self._PAGE_LIST)
        self._list_page.refresh()

    def _navigate_to_add(self):
        self._form_page.load_for_add()
        self._stack.setCurrentIndex(self._PAGE_FORM)

    def _navigate_to_edit(self, patient: Patient):
        self._form_page.load_for_edit(patient)
        self._stack.setCurrentIndex(self._PAGE_FORM)

    def _navigate_to_detail(self, patient: Patient):
        self._detail_page.load_patient(patient)
        self._stack.setCurrentIndex(self._PAGE_DETAIL)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_patient_saved(self, patient: Patient):
        self._navigate_to_list()
        if self._form_page._edit_mode:
            msg = f"Patient details updated — {patient.patient_code}  {patient.full_name}"
        else:
            msg = (
                f"Patient registered successfully!  "
                f"Patient ID: {patient.patient_code}  —  {patient.full_name}"
            )
        self._list_page.show_success(msg)

    # ------------------------------------------------------------------
    # Called by MainWindow when this section becomes active
    # ------------------------------------------------------------------

    def on_section_activated(self):
        """Refresh the list whenever the Patients section is opened."""
        if self._stack.currentIndex() == self._PAGE_LIST:
            self._list_page.refresh()
