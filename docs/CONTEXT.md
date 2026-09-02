# CONTEXT.md - VESP Control de Objetivos

## Last updated: Agosto 2026 | Version: 1.5.2

---

## ⚠️ Notas de consolidación (leer antes de tocar código)

- **Versión real: 1.5.2** (según `version.txt`, la fuente más confiable).
- **ANALISIS_ESTABILIDAD.md estaba obsoleto**: describía como "pendientes" 9 de 12 problemas
  que la sección 6 de este mismo CONTEXT ya marcaba como resueltos en v1.1.0-v1.5.2. Se descartó.
- **Conflicto detectado sin resolver — revisar manualmente:**
  - `GUIA_INSTALACION.md` y `readme.md` mencionan **SQLAlchemy** como dependencia de BD.
    `requirements.txt` real NO tiene SQLAlchemy (usa sqlite3 stdlib). Documentación vieja, ignorar.
  - `readme.md` dice entry point `python main.py`; el real es `python scripts/main.py`. Usar el real.
  - `ui/login.py`: la validación de inputs de login (3-50 caracteres, alfanumérico + `_`, rate-limiting de 5 intentos/15 min) está completamente implementada en `_validar_entrada_login()`.
    - `api/`: cuenta con una arquitectura de Flask madura y modular en `api/routes/` (`auth`, `pasadas`, `objetivos`, `supervisores`, `usuarios`, `reportes`, `logs`, `salud`, `sincronizacion`, `exportacion`) y Swagger en `docs.py`.
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

sistema-control-objetivos/
├── scripts/
│   └── main.py              # Entry point
├── ui/
│   ├── login.py
│   ├── ventana_principal.py
│   ├── dashboard.py
│   ├── importar_excel.py    # Import UI + DialogoResolverObjetivos/Supervisores
│   ├── tabla_diaria.py
│   ├── vista_*.py            # Auditoría, logs, caché, sincronización, validaciones, indexación
│   └── widgets/              # Componentes UI reusables (sidebar, badges, tabla_cobertura, estilos)
├── services/
│   ├── sesion.py
│   ├── permisos.py
│   ├── importador/
│   ├── gestor_turnos.py
│   ├── sync_manager.py
│   └── (33 services total)
├── database/
│   ├── db.py                # SQLite init, migrations, backup
│   └── gestor_db.py         # Conexiones y transacciones thread-safe
├── models/
│   ├── usuario.py
│   ├── objetivos.py
│   ├── supervisores.py
│   ├── equipos.py
│   ├── turnos.py
│   ├── types.py
│   ├── validators.py
│   └── exceptions.py
├── api/                      # Flask REST API
│   ├── app.py                # App Flask init
│   ├── docs.py               # Integración Swagger / OpenAPI
│   └── routes/               # Blueprints modulares (auth, pasadas, objetivos, supervisores, usuarios, etc.)
├── assets/                   # vesp.png, icono.ico
├── backups/                  # Auto-generated
├── tests/
│   └── conftest.py + test_*.py
├── docs/                      # Reference docs (not injected as context)
├── requirements.txt
├── requirements-dev.txt
└── CONTEXT.md                 # This file

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
- API JWT config uses `VESP_JWT_SECRET`; the Flask API raises a clear error and does not use a hardcoded fallback if the variable is missing

## Permisos por rol

| Rol        | Permisos                                                       |
| ---------- | -------------------------------------------------------------- |
| Admin      | Control total, gestión de usuarios, hard delete y backups.     |
| Supervisor | Crear y editar objetivos, equipos y pasadas.                   |
| Operador   | Ver y registrar pasadas básicas.                               |
| Auditor    | Solo lectura de toda la información.                           |
| Gerente    | Vista ejecutiva y acceso a reportes.                           |

### Objectives (objetivos)

- Create with name, start date, weekly coverage days
- Soft-delete with recorded end date
- Hard delete (admin only): requires typing exact name, logged in audit trail
- Real-time search in main table
- The objectives REST API previously treated `Objetivo` instances like tuples in some endpoints (`obj[0]`, `obj[1]`) and now serializes them correctly as dicts based on the real model fields (`id`, `nombre`, `fecha_inicio`, `fecha_fin`, `dias_semana`, `activo`); signature mismatches between the API and the model functions for creating, updating, and deleting objectives were also corrected
- SQLite foreign key enforcement is enabled through the shared DB configuration used by the database manager and objective-related flows; objective hard deletes now remove dependent `pasadas` rows explicitly, log the dependency count, and raise a clear database error if the delete cannot be completed so no data is silently lost
- The objectives list UI no longer uses direct SQL for objective updates; it reads and writes through the objective model layer so the UI stays aligned with persistence and cache/sync invalidation

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

### Import (ui/importar_excel.py + services/importador/)

- Import CONTROL_RECORRIDOS Excel files
- Sheets named by date and shift; three horizontal column blocks per sheet
- Detects each block from its complete header row, including shifted columns
- Stops at the `OBSERVACIONES:` section and ignores its free text
- Normalizes Excel time values, including text using `;` as separator
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
- El parser de CONTROL_RECORRIDOS usa un único flujo estructurado para normalizar objetivo,
  supervisor, turno, hora, fecha y descartes.
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
- services/importador/ handles all Excel import logic; do not duplicate elsewhere
- El turno de importación viene siempre de la hoja, nunca se infiere del horario puntual de la fila

---

## 6. Stability Status

### Resolved (v1.1.0 - v1.5.2)

- scripts/main.py: try-except on all init components; graceful degradation
- ui/login.py::verificar_login(): bcrypt errors differentiated; failed attempts logged; input validation (`_validar_entrada_login`) and rate limiting (`_verificar_rate_limit`) fully implemented
- ui/login.py::_login_post_cambio(): None check on fetchone() before indexing
- services/sesion.py: obtener_sesion_valida() added as central session validator
- database/db.py: explicit rollback on migration failure; duplicate column treated as no-op
- services/importador/: structured parser, normalization, matching, validation, and transactional import
- ui/importar_excel.py: DialogoResolverSupervisores added (mirrors DialogoResolverObjetivos)
- ui/importar_excel.py: "Deshacer importación" feature added with filters + double confirmation

### Pending (high priority)

- database/db.py: foreign key enforcement is enabled consistently through the shared SQLite configuration used by the database manager and objective-related flows
- services/permisos.py: decorators lack try-except and logging on failure

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
- Files named by responsibility: gestor_turnos.py, importador/

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
VESP_JWT_SECRET=REEMPLAZAR_CON_SECRETO_JWT_LARGO_Y_ALEATORIO
VESP_ENCRYPTION_KEY=REEMPLAZAR_CON_CLAVE_DE_CIFRADO_LARGA_Y_ALEATORIA
VESP_API_HOST=127.0.0.1
VESP_API_PORT=5000
VESP_API_DEBUG=false
VESP_DB_PATH=seguridad.db
VESP_LOG_LEVEL=INFO
```

- `VESP_JWT_SECRET` is required by the Flask API at startup; the app fails fast if it is missing.
- `VESP_API_DEBUG` defaults to `false` and does not enable debug mode unless explicitly set.
- `VESP_ENCRYPTION_KEY` is validated only when encryption/decryption functionality is actually used; importing the module no longer fails if the variable is missing.
- The legacy JWT secret configuration name is not used anywhere in the project.
- psutil (system/process utilities used by services requiring it)

## Runtime local files (not versioned)

- sync_queue.json (project root) is local runtime state generated by services/sync_manager.py.
- It is git-ignored and must never be committed.
