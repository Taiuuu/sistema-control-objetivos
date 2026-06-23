# CONTEXT.md - VESP Control de Objetivos
# Last updated: Junio 2026 | Version: 1.5.2

---

## 1. Project Summary

VESP Control de Objetivos is a desktop application for managing security patrol records.
It tracks daily patrol passes (pasadas) by supervisors across monitored locations (objetivos),
generates compliance reports, and maintains a full audit log.

- Current users: admin + operadores in a single organization
- Current version: 1.1.0 (stable, in use)
- Entry point: `python scripts/main.py`
- Default credentials on first run: admin / 0000 (forced change on first login)

---

## 2. Tech Stack

- Python 3.8+
- PyQt6 >= 6.0 (desktop UI)
- SQLite (local DB file: seguridad.db)
- bcrypt (password hashing)
- openpyxl >= 3.8 (Excel export/import)
- Flask (optional REST API, non-blocking if unavailable)
- PyInstaller (installer generation)

Dev dependencies: pytest, flake8, black, bandit, safety, pre-commit

---

## 3. Folder Structure (active only)

```
sistema-control-objetivos/
├── scripts/
│   └── main.py              # Entry point
├── ui/
│   ├── login.py
│   ├── ventana_principal.py
│   ├── dashboard.py
│   ├── importar_excel.py    # Import UI + DialogoResolverObjetivos/Supervisores
│   └── reporte_*.py
├── services/
│   ├── sesion.py
│   ├── permisos.py
│   ├── importador_universal.py
│   └── (18 services total)
├── database/
│   └── db.py                # SQLite init, migrations, backup
├── models/
│   ├── usuario.py
│   ├── objetivo.py
│   ├── pasada.py
│   └── supervisor.py
├── api/                     # Flask REST, optional
├── assets/                  # vesp.png, icono.ico
├── backups/                 # Auto-generated
├── tests/
│   └── conftest.py + test_*.py
├── docs/                    # Reference docs (not injected as context)
├── requirements.txt
├── requirements-dev.txt
└── CONTEXT.md               # This file
```

Not active yet (planned for v2.0+): desktop/, mobile/, shared/, backend/

---

## 4. Features by Module

**Auth & security**
- Login with bcrypt-hashed passwords
- Strong password validation with real-time visual indicator
- Roles: admin, supervisor, operador, auditor, gerente
- Mandatory password change on first login (default: 0000)
- Auto-logout on inactivity with pre-logout backup
- Admin can reset any user password

**Objectives (objetivos)**
- Create with name, start date, weekly coverage days
- Soft-delete with recorded end date
- Real-time search in main table

**Supervisors**
- Create and delete supervisors
- Shift teams: two supervisors per shift per day
- Auto-filter by team when logging a pasada

**Pasadas (patrol passes)**
- Log with date, time, shift, objetivo, supervisor
- Edit and delete existing pasadas
- Main table shows daily status per objetivo and shift:
  - Both passed / Day missing / Night missing / Nobody passed
  - Color coding: green / yellow / red

**Reports**
- Monthly compliance report per objetivo
- % calculated over configured coverage days only
- Export to Excel and PDF with corporate logo

**Notes**
- Daily notes per objective, deletable

**Users (admin only)**
- Create, delete, reset password
- Admin account protected from deletion

**Audit log**
- All actions logged with user, date, time
- Filterable by date, admin-only view

**Backup**
- Auto daily backup on startup
- Auto backup before inactivity logout
- 30-day retention with auto-cleanup

**Import (ui/importar_excel.py + services/importador_universal.py)**
- Import CONTROL_RECORRIDOS Excel files
- Sheets named by date and shift; three horizontal column blocks per sheet
- File is parsed once (preview cached); import reuses preview, never reparses
- Auto-resolves objetivos and supervisores that already exist in DB
- For unresolved ones: shows DialogoResolverObjetivos / DialogoResolverSupervisores
  - User can map to existing or create new inline
  - Cancelling aborts the import entirely
- Duplicate detection with time tolerance
- Known name mapping: "POLI - GRAND BOURG" -> "POLIDEPORTIVO GRAND BOURG"
- Supports datetime.datetime and time for hora fields; handles overnight shifts
- Hidden rows in Excel are detected and skipped
- Final summary: N imported / N duplicates skipped / N errors
- "Deshacer importacion" menu option: filter pasadas by date range, supervisor,
  objetivo; multi-select; double confirmation (type "ELIMINAR") to bulk delete

**Objetivos (admin only: hard delete)**
- Soft-delete: marca fecha de baja, objetivo permanece en BD
- Hard delete (admin only): removes from DB permanently, requires typing exact name
- Both actions logged in audit trail

**UI**
- Dark corporate theme (toggleable)
- Side menu organized by section
- Keyboard shortcuts (Ctrl+E export, Ctrl+Q quit, Esc close dialog)
- Single-instance forms (cannot open twice)
- Corporate icon in taskbar

**System**
- Auto-update notification from GitHub releases
- Factory reset script
- Version shown on login screen

---

## 5. Architecture Decisions (do not change)

- Single SQLite file (seguridad.db), no external DB server
- Layered: ui/ -> services/ -> database/ (no direct DB calls from UI)
- RBAC via decorators in services/permisos.py (@requiere_permiso)
- Session state managed exclusively through services/sesion.py
  - Use obtener_sesion_valida() -> returns (usuario_id, rol) or None
- Flask API is optional; app must start and run without it
- All migrations must include explicit rollback on failure
- Backups are file copies of seguridad.db, stored in backups/
- importador_universal.py handles all Excel import logic; do not duplicate elsewhere

---

## 6. Stability Status

**Resolved (v1.1.0 - v1.5.2)**
- scripts/main.py: try-except on all init components; graceful degradation
- ui/login.py::verificar_login(): bcrypt errors differentiated; failed attempts logged
- ui/login.py::_login_post_cambio(): None check on fetchone() before indexing
- services/sesion.py: obtener_sesion_valida() added as central session validator
- database/db.py: explicit rollback on migration failure; duplicate column treated as no-op
- importador_universal.py: file parsed once, preview cached (_cache_inicializado flag)
- importador_universal.py: auto-resolves existing objetivos/supervisores, manual dialog only for new ones
- importador_universal.py: hora normalization supports datetime.datetime and out-of-range times
- ui/importar_excel.py: DialogoResolverSupervisores added (mirrors DialogoResolverObjetivos)
- ui/importar_excel.py: "Deshacer importacion" feature added with filters + double confirmation

**Pending (high priority)**
- database/db.py: FOREIGN KEY enforcement not yet enabled on transactions
- ui/login.py: input validation (max length, character whitelist) not complete
- services/permisos.py: decorators lack try-except and logging on failure

**Known risks**
- No input length limits on login fields yet (SQL injection mitigated by parameterization but still incomplete)
- Theme switching may not propagate to all widgets consistently
- Log files have no rotation limit

---

## 7. Roadmap (confirmed next steps only)

**Immediate**
1. Add input validation to ui/login.py (max 50 chars, alphanumeric + underscore)
2. Add error handling + logging to permisos.py decorators
3. Fix theme propagation in ventana_principal.py
4. Write basic stability tests: login validation, permission decorators, graceful BD failure

**v2.0 (planned, not started)**
- Modular refactor: move code into desktop/, shared/, mobile/android/
- Android app (Kivy) for field use by supervisors
- Offline sync with JSON persistence

**v3.0 (future, one line)**
- Centralized Flask backend + PostgreSQL + web client + iOS (Flutter)

---

## 8. Working Conventions

**Code style**
- Google-style docstrings on all public functions
- Type hints on all function signatures
- Specific exceptions only (never bare `except Exception: pass`)
- Log with logging module: INFO for actions, ERROR with exc_info=True on failures

**Naming**
- Spanish for all domain terms: objetivo, pasada, supervisor, turno, equipo
- snake_case for functions and variables
- PascalCase for classes
- Files named by responsibility: gestor_turnos.py, importador_universal.py

**Commits**
- Atomic commits: one concern per commit
- Format: `fix(archivo): descripcion` / `feat(archivo): descripcion` / `refactor(archivo): descripcion`

**UI patterns**
- Forms check for existing instance before opening (no duplicate windows)
- All destructive actions require confirmation dialog
- Hard delete confirmation: double dialog + type exact name (objetivos) or "ELIMINAR" (bulk pasadas)
- Supervisor deletion requires reassignment dialog before proceeding
- Import resolution: separate dialogs for objetivos and supervisores; both support create-inline

**Testing**
- pytest, fixtures in conftest.py
- Coverage targets: services 80%, database 85%, api 75%
- Run: `pytest --cov=services --cov=database --cov=api`

**DB access**
- Always close connections explicitly or use context managers
- Always commit or rollback, never leave transactions open
- Migrations are additive only; never drop columns