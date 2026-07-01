# CONTEXT.md - VESP Control de Objetivos

## Last updated: Julio 2026 | Version: 1.5.2

---

## ⚠️ Notas de consolidación (leer antes de tocar código)

Este archivo reemplaza como fuente única a: ARQUITECTURA.md, ARQUITECTURA_MULTIUSUARIO.md,
ANALISIS_ESTABILIDAD.md, FUNCIONALIDADES.md, GUIA_INSTALACION.md, MANUAL_USUARIO.md,
ROADMAP.md, TESTING_CI_CD.md, readme.md. Esos archivos tenían versiones distintas entre sí
(0.9.0 / 1.0.0 / 1.1.0 / 1.5.2) y datos contradictorios. Se resolvió así:

- **Versión real: 1.5.2** (según `version.txt`, la fuente más confiable).
- **ANALISIS_ESTABILIDAD.md estaba obsoleto**: describía como "pendientes" 9 de 12 problemas
  que la sección 6 de este mismo CONTEXT ya marcaba como resueltos en v1.1.0-v1.5.2. Se descartó.
- **Conflicto detectado sin resolver — revisar manualmente:**
  - `GUIA_INSTALACION.md` y `readme.md` mencionan **SQLAlchemy** como dependencia de BD.
    `requirements.txt` real NO tiene SQLAlchemy (usa sqlite3 stdlib). Documentación vieja, ignorar.
  - `readme.md` dice entry point `python main.py`; el real es `python scripts/main.py`. Usar el real.
  - `MANUAL_USUARIO.md` presenta la validación de inputs de login (3-50 caracteres, alfanumérico+_)
    como si ya existiera, pero este CONTEXT la lista como "Pending". **Verificar en código cuál es cierto
    antes de asumir.**
  - `pasadas.py` (Flask blueprint subido suelto) usa `flask_jwt_extended` y `models.turnos`
    (`registrar_turno`, `listar_turnos_del_dia`), lo cual no coincide con la estructura de `models/`
    descrita abajo (`models/pasada.py`). Puede ser código legacy/experimental de `api/`. **No asumir
    que representa el estado actual de `api/` sin confirmar.**
  - `requirements.txt` y `requirements-dev.txt` tienen versiones de pytest distintas (9.0.2 vs 7.4.3).
    Usar la de `requirements.txt` como real.
- MANUAL_USUARIO.md y GUIA_INSTALACION.md se resumen abajo solo en lo operativo que no estaba ya cubierto.

---

## 1. Project Summary

VESP Control de Objetivos is a desktop application for managing security patrol records.
It tracks daily patrol passes (pasadas) by supervisors across monitored locations (objetivos),
generates compliance reports, and maintains a full audit log.

- Current users: admin + operadores in a single organization
- Current version: 1.5.2 (stable, in use)
- Entry point: `python scripts/main.py`
- Default credentials on first run: admin / 0000 (forced change on first login)
- Author: Taiel Clot

---

## 2. Tech Stack

- Python 3.8+ (dev/CI matrix real: 3.10, 3.11, 3.12)
- PyQt6 (desktop UI)
- SQLite (local DB file: seguridad.db) — acceso directo con `sqlite3`, sin ORM
- bcrypt (password hashing)
- openpyxl (Excel export/import)
- Flask + Flask-JWT-Extended (REST API, optional, non-blocking if unavailable)
- reportlab (export PDF)
- PyInstaller (installer generation)

Dev dependencies: pytest, pytest-cov, pytest-mock, pytest-flask, black, flake8, pylint, isort,
mypy, bandit, safety, pre-commit

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
│   ├── gestor_turnos.py
│   ├── sync_manager.py
│   └── (18 services total)
├── database/
│   └── db.py                # SQLite init, migrations, backup
├── models/
│   ├── usuario.py
│   ├── objetivo.py
│   ├── pasada.py
│   └── supervisor.py
├── api/                      # Flask REST, optional
├── assets/                   # vesp.png, icono.ico
├── backups/                  # Auto-generated
├── tests/
│   └── conftest.py + test_*.py
├── docs/                      # Reference docs (not injected as context)
├── requirements.txt
├── requirements-dev.txt
└── CONTEXT.md                 # This file
```

Not active yet (planned for v2.0+): `desktop/`, `mobile/`, `shared/`, `backend/`

---

## 4. Features by Module

### Auth & security
- Login with bcrypt-hashed passwords
- Strong password validation with real-time visual indicator
- Roles: admin, supervisor, operador, auditor, gerente
- Mandatory password change on first login (default: 0000)
- Auto-logout on inactivity with pre-logout backup
- Admin can reset any user password

**Permisos por rol:**

| Rol | Permisos |
|-----|----------|
| Admin | Control total, gestión de usuarios, hard delete, backups |
| Supervisor | Crear/editar objetivos, equipos, pasadas |
| Operador | Ver y registrar pasadas básicas |
| Auditor | Solo lectura de todo |
| Gerente | Vista ejecutiva y reportes |

### Objectives (objetivos)
- Create with name, start date, weekly coverage days
- Soft-delete with recorded end date
- Hard delete (admin only): requires typing exact name, logged in audit trail
- Real-time search in main table

### Supervisors
- Create and delete supervisors (deletion requires reassignment flow)
- Shift teams: two supervisors per shift per day
- Auto-filter by team when logging a pasada

### Pasadas (patrol passes)
- Log with date, time, shift, objetivo, supervisor
- Edit and delete existing pasadas
- Main table shows daily status per objetivo and shift:
  - Both passed / Day missing / Night missing / Nobody passed
  - Color coding: green / yellow / red

### Reports
- Monthly compliance report per objetivo
- % calculated over configured coverage days only
- Export to Excel and PDF with corporate logo

### Notes
- Daily notes per objective, deletable

### Users (admin only)
- Create, delete, reset password
- Admin account protected from deletion
- New users created with password 0000, mandatory change on first login

### Audit log
- All actions logged with user, date, time
- Filterable by date, admin-only view

### Backup
- Auto daily backup on startup
- Auto backup before inactivity logout
- 30-day retention with auto-cleanup
- Manual backup: Menú → Configuración → Hacer Backup
- Stored as file copies of `seguridad.db` in `backups/`

### Import (ui/importar_excel.py + services/importador_universal.py)
- Import CONTROL_RECORRIDOS Excel files
- Sheets named by date and shift; three horizontal column blocks per sheet (legacy format),
  también soporta formato tabular con encabezados
- File is parsed once (preview cached); import reuses preview, never reparses
- Auto-resolves objetivos and supervisores that already exist in DB
- For unresolved ones: shows DialogoResolverObjetivos / DialogoResolverSupervisores
  - User can map to existing or create new inline
  - Cancelling aborts the import entirely
- Duplicate detection
- Supports datetime.datetime and time for hora fields; handles overnight shifts and hour overflow (26:30 → next day 02:30)
- Hidden rows in Excel are detected and skipped
- Final summary: N imported / N duplicates skipped / N errors
- **Regla de negocio clave: el turno de la hoja (sheet) es la única fuente de verdad para el turno
  de cada pasada. Nunca se descarta ni reclasifica una fila por diferencias entre el turno de la
  celda y el turno de la hoja — la hoja siempre gana.**
- "Deshacer importación": filtro por fecha, supervisor, objetivo; multi-select; doble confirmación
  (escribir "ELIMINAR") para borrado masivo

### UI
- Dark corporate theme (toggleable)
- Side menu organized by section
- Keyboard shortcuts (Ctrl+E export, Ctrl+Q quit, Esc close dialog)
- Single-instance forms (cannot open twice)
- Corporate icon in taskbar

### System
- Auto-update notification from GitHub releases
- Factory reset script
- Version shown on login screen

---

## 5. Architecture Decisions (do not change)

- Single SQLite file (seguridad.db), no external DB server, no ORM
- Layered: ui/ -> services/ -> database/ (no direct DB calls from UI)
- RBAC via decorators in services/permisos.py (@requiere_permiso)
- Session state managed exclusively through services/sesion.py
  - Use `obtener_sesion_valida()` -> returns (usuario_id, rol) or None
- Flask API is optional; app must start and run without it
- All migrations must include explicit rollback on failure
- Backups are file copies of seguridad.db, stored in backups/
- importador_universal.py handles all Excel import logic; do not duplicate elsewhere
- El turno de importación viene siempre de la hoja, nunca se infiere del horario puntual de la fila

---

## 6. Stability Status

### Resolved (v1.1.0 - v1.5.2)
- scripts/main.py: try-except on all init components; graceful degradation
- ui/login.py::verificar_login(): bcrypt errors differentiated; failed attempts logged
- ui/login.py::_login_post_cambio(): None check on fetchone() before indexing
- services/sesion.py: obtener_sesion_valida() added as central session validator
- database/db.py: explicit rollback on migration failure; duplicate column treated as no-op
- importador_universal.py: file parsed once, preview cached (_cache_inicializado flag)
- importador_universal.py: auto-resolves existing objetivos/supervisores, manual dialog only for new ones
- importador_universal.py: hora normalization supports datetime.datetime and out-of-range times
- ui/importar_excel.py: DialogoResolverSupervisores added (mirrors DialogoResolverObjetivos)
- ui/importar_excel.py: "Deshacer importación" feature added with filters + double confirmation

### Pending (high priority)
- database/db.py: FOREIGN KEY enforcement not yet enabled on transactions
- ui/login.py: input validation (max length, character whitelist) — **verificar estado real, ver nota de conflicto arriba**
- services/permisos.py: decorators lack try-except and logging on failure
- importador_universal.py legacy parser: descarta filas cuando el turno de la celda no coincide
  con el turno de la hoja en vez de forzar el turno de la hoja (bug activo, corregir)

### Known risks
- No input length limits confirmados en login fields (SQL injection mitigado por parametrización)
- Theme switching may not propagate to all widgets consistently
- Log files have no rotation limit

---

## 7. Roadmap (confirmed next steps only)

### Immediate
1. Add input validation to ui/login.py (max 50 chars, alphanumeric + underscore) — confirmar si ya está hecho
2. Add error handling + logging to permisos.py decorators
3. Fix theme propagation in ventana_principal.py
4. Fix legacy import parser: no descartar filas por discrepancia de turno, forzar turno de hoja
5. Write basic stability tests: login validation, permission decorators, graceful BD failure

### v2.0 (planned, not started)
- Modular refactor: move code into desktop/, shared/, mobile/android/ (Kivy app para tablets)
- Offline sync with JSON persistence, reintento automático, resolución de conflictos
- Esquema de BD compatible con PostgreSQL (migración futura), migraciones con Alembic

### v3.0 (future, one line)
- Centralized Flask + SQLAlchemy backend + PostgreSQL + web client (React) + iOS (Flutter)

---

## 8. Working Conventions

### Code style
- Google-style docstrings on all public functions
- Type hints on all function signatures
- Specific exceptions only (never bare `except Exception: pass`)
- Log with logging module: INFO for actions, ERROR with exc_info=True on failures

### Naming
- Spanish for all domain terms: objetivo, pasada, supervisor, turno, equipo
- snake_case for functions and variables
- PascalCase for classes
- Files named by responsibility: gestor_turnos.py, importador_universal.py

### Commits
- Atomic commits: one concern per commit
- Format: `fix(archivo): descripcion` / `feat(archivo): descripcion` / `refactor(archivo): descripcion`

### UI patterns
- Forms check for existing instance before opening (no duplicate windows)
- All destructive actions require confirmation dialog
- Hard delete confirmation: double dialog + type exact name (objetivos) or "ELIMINAR" (bulk pasadas)
- Supervisor deletion requires reassignment dialog before proceeding
- Import resolution: separate dialogs for objetivos and supervisores; both support create-inline

### Testing
- pytest, fixtures in conftest.py (`test_db`, `db_initialized`, `admin_user`, `operador_user`,
  `test_objetivo`, `test_supervisor`, `api_client`, `auth_token`)
- Coverage targets: services 80%, database 85%, api 75%, mínimo global 60%
- Run: `pytest --cov=services --cov=database --cov=api`
- CI: GitHub Actions (`tests.yml`) corre en push/PR a main y develop; matriz Python 3.10/3.11/3.12
  en ubuntu-latest y windows-latest; incluye flake8, black, isort, bandit, safety
- Releases: tag `v*` dispara `release.yml` (build PyInstaller + Inno Setup + publish)

### DB access
- Always close connections explicitly or use context managers
- Always commit or rollback, never leave transactions open
- Migrations are additive only; never drop columns

---

## 9. Config de entorno (.env, opcional)

```env
DATABASE_PATH=seguridad.db
API_HOST=127.0.0.1
API_PORT=5000
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
SESSION_TIMEOUT=7200
BACKUP_INTERVAL=3600
BACKUP_DIR=backups/
SYNC_ENABLED=False
SYNC_SERVER=http://localhost:5000
```