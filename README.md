# B. D Medical Center — Clinic Prescription Management System

A Windows desktop application built with Python and PySide6 (Qt6) that replaces handwritten prescriptions with digital, structured consultations and printable prescriptions.

---

## 📋 Features

- **Clinic & Doctor Context:** Built for outpatient clinic workflow.
- **Patient Management (Phase 2):**
  - Register new patients with automatic Patient ID (`PT-#####`).
  - Search patients by name, code, or phone number.
  - View patient profile and edit demographic / contact details.
  - Duplicate-checking mechanism.
  - Soft archiving (no accidental data loss).
- **Consultation & Prescription Builder (Phase 3):**
  - Record chief complaints, observations, investigations, and diagnosis.
  - Track vital signs (Temperature, Blood Pressure, Pulse, Weight).
  - Dynamic medicine rows with name autocomplete from pre-seeded catalog.
  - Custom dosage, duration, and instructions.
  - Save as Draft or Review & Finalize (with audit lock).
  - Consultation history per patient.
- **Offline & Local Storage:** Stores data locally in an embedded SQLite database using SQLAlchemy with WAL mode. Doctor/staff never needs to know SQL or open database tools.

---

## 🛠️ Prerequisites

Before running the application, ensure you have:

- **Operating System:** Windows 10 or Windows 11 (64-bit recommended)
- **Python:** Python 3.10 to 3.13 installed
  - Make sure **"Add Python to PATH"** was checked during installation.
  - Verify with:
    ```bash
    python --version
    ```

---

## 🚀 Setup & Installation for Developers

### 1. Clone the repository
```bash
git clone <repository_url>
cd "Digital Prescription"
```

### 2. Create and activate a Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt - CMD):**
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

> *Tip: If PowerShell gives an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again.*

### 3. Install Required Dependencies

Install the required Python packages specified in `requirements.txt`:
```bash
pip install -r requirements.txt
```

*Direct package installation (if preferred):*
```bash
pip install PySide6 SQLAlchemy
```

---

## 💻 Running the Application

Once dependencies are installed, launch the application using:

```bash
python app.py
```

The application will:
1. Initialize the SQLite database automatically in `%APPDATA%\BDMedicalCenter\clinic.db`.
2. Seed the initial medicine catalogue if it's the first run.
3. Open the desktop UI window ready for use.

---

## 📁 Project Directory Structure

```text
Digital Prescription/
├── app.py                            # Main application entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation and developer setup
├── .gitignore                        # Git exclusion rules
├── MVP.md                            # Product roadmap & requirements specification
│
└── clinic_app/
    ├── database/
    │   ├── connection.py             # SQLite connection & table initialization
    │   └── migrations/               # Database migrations (if applicable)
    │
    ├── models/                       # SQLAlchemy ORM models
    │   ├── patient.py                # Patient model
    │   ├── consultation.py           # Consultation & vitals model
    │   ├── prescription.py           # Prescription & PrescriptionItem models
    │   └── medicine.py               # MedicineCatalog model
    │
    ├── services/                     # Business logic layer
    │   ├── patient_service.py        # Patient CRUD & search operations
    │   └── prescription_service.py   # Prescriptions, drafts, and catalog service
    │
    ├── ui/                           # PySide6 graphical user interface
    │   ├── main_window.py            # Main application window & sidebar
    │   ├── dashboard_view.py         # Dashboard & quick actions
    │   ├── patients_view.py          # Patients list & search page
    │   ├── patient_form.py           # Add / Edit patient form
    │   ├── patient_detail_view.py    # Patient profile & history view
    │   ├── prescription_form.py      # Consultation & Rx builder
    │   ├── medicine_row_widget.py    # Dynamic medicine input row
    │   ├── prescription_review_dialog.py # Modal review before finalization
    │   ├── prescription_history_view.py  # Prescriptions archive (Phase 5)
    │   ├── settings_view.py          # Clinic settings (Phase 6)
    │   └── message_bar.py            # Reusable feedback notifications
    │
    └── resources/
        ├── styles/
        │   └── main.qss              # Qt stylesheet (QSS) for custom UI styling
        └── images/                   # Icons and clinic assets
```

---

## 📌 Development Roadmap

- [x] **Phase 1:** Project Foundation & Application Shell
- [x] **Phase 2:** Patient Management (SQLite Backend)
- [x] **Phase 3:** Consultation & Prescription Builder
- [x] **Phase 4:** Prescription Template, PDF Generation & Printing
- [ ] **Phase 5:** Prescription History & Retrieval
- [ ] **Phase 6:** Clinic Settings, Backup/Restore, Security & Windows Packaging
