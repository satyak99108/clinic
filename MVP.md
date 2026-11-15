# Clinic Prescription Management System --- MVP Roadmap

## 1. Project Overview

Build a Windows desktop application for a clinic that replaces
handwritten prescriptions with digitally created, printable
prescriptions.

The doctor should use a simple graphical interface. **The doctor must
never need to write SQL, open a database tool, or understand database
tables.** SQLite is an internal storage mechanism used by the
application.

### MVP goal

A doctor or authorized clinic staff member should be able to:

1.  Register a patient.
2.  Find an existing patient.
3.  Open and update a patient's basic details.
4.  Create a consultation and enter prescription details.
5.  Preview and generate a printable PDF.
6.  Retrieve a patient's previous consultations and prescriptions.

### Initial assumptions

- Target: Windows desktop application.
- Initial deployment: one clinic computer, offline-capable.
- Database: SQLite stored locally.
- Interface: simple, professional, form-based GUI.
- Suggested stack: Python, PySide6, SQLite, SQLAlchemy, and
  HTML/CSS-based PDF rendering.
- These are starting assumptions, not permanent limitations.
  Multi-computer access can be planned as a later upgrade.

---

## 2. MVP Scope

### Included in the MVP

- Clinic profile and doctor details.
- Patient registration and patient ID generation.
- Patient search and patient list.
- Patient detail view and editing.
- Consultation and prescription entry.
- Multiple medicines per prescription.
- Prescription preview, PDF export, and printing.
- Patient consultation/prescription history.
- Basic validation and error messages.
- Local database backup and restore.
- Basic application access protection.

### Not included in the first MVP

- AI diagnosis or AI medicine recommendations.
- Online patient portal.
- Appointment scheduling and billing.
- Pharmacy inventory management.
- Insurance claims.
- Multi-branch clinic management.
- Cloud synchronization or multi-computer concurrent access.
- Automatic interpretation of handwritten prescriptions.

Keep these outside the MVP unless the clinic confirms they are
essential.

---

## 3. Exact Development Roadmap

## Phase 1 --- Project Foundation and Application Shell

**Objective:** Create the desktop application structure and navigation.

### Tasks

- [ ] Set up the Python project and virtual environment.
- [ ] Install and configure PySide6.
- [ ] Create the main application window.
- [ ] Add a left sidebar or clear navigation menu.
- [ ] Add these initial sections:
  - Dashboard
  - Patients
  - New Prescription
  - Prescription History
  - Settings
- [ ] Create a consistent visual style, typography, spacing, and form
      controls.
- [ ] Add clear success, warning, and error messages.
- [ ] Make the layout usable at common Windows screen sizes.

### Completion criteria

- The application launches as a desktop window.
- The user can navigate between all main sections.
- No database or programming knowledge is required to operate the
  interface.

---

## Phase 2 --- Patient Management (SQLite Behind the Interface)

**Objective:** Let the doctor or receptionist add, edit, search, and
retrieve patients through normal screens and forms.

**Critical usability requirement:** SQLite is completely hidden from the
doctor. The application performs all database operations automatically.
Do not expose SQL commands, database browsers, table names, or technical
database errors in the user interface.

### 2.1 Patient information fields

Recommended fields:

---

Field Requirement

---

Patient ID Automatically generated; read-only

Full name Required

Age or date of birth Capture date of birth where known;
otherwise allow age

Gender Select from a simple dropdown;
allow an appropriate "Prefer not to
say/Not recorded" option

Phone number Optional or required according to
clinic workflow; validate format

Address Optional

Emergency contact Optional

Date registered Automatically recorded

Additional notes Optional; avoid unnecessary
sensitive information

---

Do not ask for every possible detail during registration. Keep the
initial form short and allow optional details to be added later.

### 2.2 Patient screens and workflow

#### A. Patients list

Show a searchable list with useful columns:

- Patient ID
- Patient name
- Phone number
- Age or date of birth
- Last visit

Available actions:

- **Add Patient**
- **View**
- **Edit**
- **Create Prescription**

Include sorting and pagination or a manageable scrolling list if the
clinic has many records.

#### B. Add patient

Provide a normal form with labelled fields, dropdowns, and validation.

Workflow:

1.  User selects **Add Patient**.
2.  Application opens the registration form.
3.  User enters the patient's details.
4.  User selects **Save Patient**.
5.  Application validates the form.
6.  Application saves the record to SQLite.
7.  Application displays a success message and the new Patient ID.
8.  User can immediately start a consultation or return to the patient
    list.

Prevent accidental duplicate registrations where possible. Before
saving, check for a likely existing patient using phone number and name.
If a possible match exists, show the existing record and ask the user
whether to open it or continue creating a separate record. Do not
automatically merge patients.

#### C. Search patient

Provide one prominent search box. The user should be able to search by:

- Patient name
- Patient ID
- Phone number

Search should work with partial text. For example, entering `Aak` should
find a patient named `Aakriti Kapoor`.

Show a clear "No patients found" message and an easy way to add a new
patient.

#### D. View patient

Selecting a patient opens a readable profile showing:

- Basic patient information
- Patient ID
- Registration date
- Previous consultations
- Previous prescriptions

Actions:

- **Edit Details**
- **New Consultation / Prescription**
- **View Previous Prescription**

#### E. Edit patient

- Open the existing details in the same form used for registration.
- Allow authorized users to update editable fields.
- Keep Patient ID and original registration date unchanged.
- Ask for confirmation before saving changes.
- Show a success message after saving.

Keep an appropriate record of when patient details were last updated. Do
not silently overwrite or alter old prescription snapshots when a
patient's profile changes.

### 2.3 Internal SQLite data design

SQLite is an implementation detail, not a user-facing feature.

Suggested `patients` table:

- `id` --- internal primary key
- `patient_code` --- unique, human-readable patient ID
- `full_name`
- `date_of_birth` --- nullable
- `age_at_registration` --- optional fallback if date of birth is
  unknown
- `gender`
- `phone`
- `address`
- `emergency_contact`
- `notes`
- `created_at`
- `updated_at`

Implementation requirements:

- Use SQLAlchemy or a similarly structured data-access layer.
- Use parameterized database operations through the application code.
- Create the database and tables automatically on first launch.
- Keep database operations separate from the GUI code.
- Add appropriate indexes for patient ID, name, and phone search.
- Enforce unique patient IDs.
- Validate input before saving.
- Handle database errors gracefully; show user-friendly messages
  rather than raw SQL or stack traces.
- Use transactions for operations that must succeed or fail together.
- Do not delete patient records casually. Prefer an archive/inactive
  status with restricted access and an audit trail where appropriate.
- Store dates and timestamps consistently.

### 2.4 Phase 2 acceptance tests

Phase 2 is complete only when all of these work through the graphical
interface:

- [ ] Register a new patient without using SQL or another technical
      tool.
- [ ] See the automatically generated Patient ID.
- [ ] Find the patient by full name.
- [ ] Find the patient using part of the name.
- [ ] Find the patient by Patient ID.
- [ ] Find the patient by phone number.
- [ ] Open and view the patient's details.
- [ ] Edit the patient's phone number or address and save the changes.
- [ ] Close and reopen the application and confirm the patient record
      remains available.
- [ ] Handle missing required fields with clear guidance.
- [ ] Warn about a likely duplicate without automatically merging
      records.
- [ ] Show a friendly message if a save or search fails.

**Doctor-facing experience:** buttons, text fields, dropdowns, patient
lists, and confirmation messages only. SQLite and SQL remain entirely
behind the application.

---

## Phase 3 --- Consultation and Prescription Builder

**Objective:** Let the doctor record a consultation and create a
prescription for a selected patient.

### Consultation fields

- Patient (selected from existing patient records)
- Consultation date and time (automatic, editable only if appropriate)
- Chief complaints
- Observations
- Vitals, where recorded (for example temperature, blood pressure,
  pulse, weight)
- Investigations suggested
- Diagnosis
- Remarks
- Follow-up date and time

### Medicine entry

Allow the doctor to add multiple medicine rows.

Each row should support:

- Medicine name
- Strength/form, where applicable
- Dosage (free text, e.g. `1-1-1`)
- Duration
- Measure/unit, where relevant
- Instructions (e.g. after meal)

Requirements:

- Add/remove medicine rows easily.
- Do not force a fixed dosage pattern.
- Allow the doctor to enter custom instructions.
- Provide optional medicine-name suggestions from a locally maintained
  catalogue.
- Do not automatically prescribe or recommend medicines.
- Make the doctor review the completed prescription before finalizing
  it.

### Completion criteria

- A consultation can be linked to the correct patient.
- One prescription can contain multiple medicines.
- The doctor can save a draft and return to it.
- Required fields and invalid values are handled clearly.

---

## Phase 4 --- Prescription Template, PDF, and Printing

**Objective:** Generate a professional prescription based on the
clinic's sample layout.

### Tasks

- [x] Create a reusable A4 prescription template using HTML and CSS.
- [x] Add clinic logo, name, address, and contact information.
- [x] Add doctor name, qualifications, and registration number.
- [x] Add patient details and prescription date.
- [x] Display complaints, observations, investigations, and diagnosis.
- [x] Display medicines in a clean table.
- [x] Add remarks and follow-up details.
- [x] Add an authorised signature area.
- [x] Add a computer-generated document footer if desired.
- [x] Preview the prescription before finalizing.
- [x] Export the prescription as PDF.
- [x] Support printing through the Windows print dialog.

### Completion criteria

- The generated PDF is readable and correctly formatted on A4 paper.
- Long medicine names and multiple medicine rows do not overlap or
  disappear.
- The doctor can review the document before printing.
- The PDF can be saved to a chosen location.
- Reopening a saved prescription reproduces the original issued
  content.

---

## Phase 5 --- Prescription History and Retrieval

**Objective:** Let the clinic retrieve past consultations and
prescriptions.

### Tasks

- [ ] Show consultation history inside the patient profile.
- [ ] Show prescription date and prescription ID.
- [ ] Open a past prescription in read-only mode.
- [ ] Reprint or export a previous prescription.
- [ ] Search prescriptions by patient ID, name, or date.
- [ ] Clearly distinguish drafts from finalized prescriptions.

### Data integrity rule

A finalized prescription should be treated as a historical clinical
record. Do not silently edit it when patient details, doctor details, or
medicine catalogue entries change later. If a correction is needed, use
a controlled amendment or a newly issued prescription, preserving the
original record and recording who made the change and when.

### Completion criteria

- The doctor can find a patient's previous prescription.
- The historical prescription remains unchanged if the patient's
  current contact details are edited.
- A finalized prescription cannot be casually overwritten.

---

## Phase 6 --- Clinic Settings, Backup, Security, and Packaging

**Objective:** Prepare the MVP for controlled real-world clinic use.

### Clinic settings

- Clinic name
- Logo
- Address
- Phone number
- Doctor name
- Qualifications
- Registration number
- Signature image or signature area
- Prescription layout preferences

### Backup and restore

- Add a simple **Back Up Data** action.
- Let an authorized user choose a backup destination.
- Add a guided restore process with confirmation.
- Validate a backup before replacing current data.
- Never overwrite the only copy of the clinic database without
  warning.
- Test backup and restore before release.

### Security and privacy

- Add appropriate user access controls.
- Restrict access to patient records to authorized clinic users.
- Avoid storing passwords in plain text.
- Protect backups and the local database against unauthorized access.
- Avoid displaying sensitive patient details unnecessarily.
- Keep an audit trail for important changes, especially finalized
  prescriptions.
- Use synthetic test records during development.
- Establish clinic-approved retention, consent, and privacy procedures
  before using real patient information.

### Windows packaging

- Package the application as a Windows executable.
- Ensure the database is stored in a persistent application-data
  location, not inside a temporary folder or the executable
  installation directory.
- Test installation, launch, upgrades, printing, and backup on the
  target clinic computer.

### Completion criteria

- The application can be installed and launched on the clinic
  computer.
- Patient data remains available after application restarts and
  upgrades.
- Backup and restore work in a tested scenario.
- Unauthorized users cannot casually access patient records.
- The clinic can update its own letterhead and doctor details without
  editing code.

---

## 4. Suggested Application Navigation

Use simple labels that a non-technical doctor or receptionist can
understand.

---

Navigation item Purpose

---

Dashboard Today's overview and shortcuts

Patients Register, search, view, and edit
patients

New Prescription Start a consultation and enter
prescription details

Prescription History Find and reopen past prescriptions

Settings Clinic and doctor information

Backup & Restore Protect and recover clinic records

---

Avoid technical labels such as "Database", "SQL", "Tables", "Queries",
or "Schema" in the user interface.

---

## 5. Core User Journeys

### Journey A --- First visit

1.  Open the application.
2.  Select **Patients**.
3.  Select **Add Patient**.
4.  Enter patient information.
5.  Save the patient.
6.  Select **New Prescription** for that patient.
7.  Enter consultation and medicine details.
8.  Preview and finalize the prescription.
9.  Save as PDF or print.

### Journey B --- Returning patient

1.  Open **Patients**.
2.  Search by name, Patient ID, or phone number.
3.  Open the matching patient.
4.  Review previous prescriptions if needed.
5.  Select **New Consultation / Prescription**.
6.  Enter the new consultation.
7.  Preview, finalize, and print.

### Journey C --- Correcting patient contact details

1.  Search for the patient.
2.  Open the patient profile.
3.  Select **Edit Details**.
4.  Update the required information.
5.  Save changes.
6.  Confirm that the updated profile appears while old finalized
    prescriptions remain unchanged.

---

## 6. Recommended Project Structure

A maintainable starting structure:

```text
clinic-prescription-app/
│
├── app.py
├── requirements.txt
├── README.md
│
├── app/
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── dashboard_view.py
│   │   ├── patients_view.py
│   │   ├── patient_form.py
│   │   ├── patient_detail_view.py
│   │   ├── prescription_form.py
│   │   ├── prescription_history_view.py
│   │   └── settings_view.py
│   │
│   ├── models/
│   │   ├── patient.py
│   │   ├── consultation.py
│   │   ├── prescription.py
│   │   └── medicine.py
│   │
│   ├── services/
│   │   ├── patient_service.py
│   │   ├── prescription_service.py
│   │   ├── pdf_service.py
│   │   └── backup_service.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   └── migrations/
│   │
│   ├── templates/
│   │   └── prescription.html
│   │
│   └── resources/
│       ├── styles/
│       └── images/
│
└── tests/
    ├── test_patients.py
    ├── test_prescriptions.py
    └── test_backup.py
```

This is a suggested structure; it can be adjusted as the application
grows.

---

## 7. Definition of MVP Complete

The MVP is ready for a supervised clinic pilot when:

- [ ] A clinic user can operate the entire workflow without SQL or
      programming knowledge.
- [ ] Patients can be added, searched, viewed, and edited through the
      GUI.
- [ ] Patient records persist after closing and reopening the
      application.
- [ ] A doctor can create a consultation and enter multiple medicines.
- [ ] A prescription can be previewed, saved, exported, and printed.
- [ ] Previous finalized prescriptions can be retrieved accurately.
- [ ] Editing a patient's profile does not alter old finalized
      prescriptions.
- [ ] Backup and restore have been tested.
- [ ] Basic access protection is in place.
- [ ] The application has been tested with synthetic data and then
      reviewed by the clinic before real patient use.

**Build order:** complete and test each phase before moving to the next.
Do not start with advanced features. The first working milestone should
be Phase 1 plus Phase 2: a desktop interface where clinic staff can
register, search, view, and edit patients without ever seeing the
database.
