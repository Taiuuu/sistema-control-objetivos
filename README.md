# VESP Control de Objetivos

Sistema profesional de gestión de rondas y objetivos de seguridad privada, basado en escritorio
con PyQt6 y SQLite. Permite registrar y supervisar pasadas por turno, gestionar objetivos y
supervisores, generar reportes de cumplimiento, mantener auditoría completa, y soporte de
importación desde Excel y API REST local.

## ¿Qué hace este proyecto?

- Registrar y administrar objetivos de seguridad.
- Controlar pasadas por turno diurno y nocturno.
- Gestionar supervisores y equipos de turno.
- Importar datos desde Excel (formato CONTROL_RECORRIDOS).
- Generar reportes de cumplimiento y estadísticas (Excel/PDF).
- Mantener auditoría de operaciones y copias de seguridad automáticas.
- Autenticar usuarios con permisos según roles (admin, supervisor, operador, auditor, gerente).

## Estructura del proyecto

- `scripts/` - Lanzador principal y utilidades de mantenimiento.
- `ui/` - Interfaces gráficas PyQt6 para todas las pantallas de la aplicación.
- `services/` - Lógica de negocio: validaciones, importadores, sincronización, backup, notificaciones.
- `database/` - Acceso y migración de la base de datos SQLite (`db.py`, `gestor_db.py`).
- `models/` - Definiciones de entidades y validaciones de dominio.
- `api/` - API REST independiente y rutas Flask.
- `docs/` - Documentación técnica y guías internas.
- `tests/` - Suite de pruebas automatizadas.

## Tecnologías utilizadas

- Python 3.11+ (compatible hasta 3.14)
- PyQt6
- SQLite (acceso directo, sin ORM)
- Flask + Flask-JWT-Extended (API REST)
- openpyxl / pandas (importación Excel)
- bcrypt (hashing de contraseñas)
- reportlab (exportación PDF)
- redis (opcional, si se usan SSE/notificaciones)

## Instalación

```bash
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos

python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux

python -m pip install -r requirements.txt
```

Configurar variables de entorno:

```bash
copy .env.example .env     # Windows
# cp .env.example .env     # macOS/Linux
```

Ajustar `JWT_SECRET_KEY` y `ENCRYPTION_KEY` en `.env` antes de usar en producción.

## Ejecución

### Aplicación de escritorio

```bash
python scripts/main.py
```

Al iniciar, inicializa: base de datos SQLite local, migraciones de esquema, backup automático,
servidor API local de soporte, e interfaz de login.

**Primer acceso:**
- Usuario: `admin`
- Contraseña: `0000` (cambio obligatorio en el primer login)

### API Flask independiente

```bash
python api/app.py
```

Levanta el servidor en `http://0.0.0.0:5000`. Rutas principales:

- `POST /api/auth/login`
- `GET /api/objetivos` · `POST /api/objetivos`
- `GET /api/supervisores`
- `POST /api/pasadas`
- `GET /api/reportes/mensual/<anio>/<mes>`

## Pruebas

```bash
python -m pytest
```

## Variables de entorno (`.env.example`)

- `VESP_JWT_SECRET` - Secreto JWT para la API
- `VESP_ENCRYPTION_KEY` - Clave de cifrado
- `VESP_DB_PATH` - Ruta opcional a la base de datos SQLite
- `VESP_API_HOST` - Host de la API
- `VESP_API_PORT` - Puerto de la API
- `VESP_API_DEBUG` - Activar modo debug para la API
- `VESP_LOG_LEVEL` - Nivel de logging

## Notas de arquitectura

- UI construida con PyQt6 en `ui/`, sin llamadas directas a la BD (pasa siempre por `services/`).
- Lógica de negocio agrupada en `services/` (validaciones, importadores, sincronización, reportes).
- Base de datos SQLite manejada desde `database/db.py` y `database/gestor_db.py`.
- `api/` contiene una versión Flask de la API REST, independiente de la app de escritorio.

## Autor y empresa

- Autor: Taiel Clot
- Empresa: V.E.S.P Organizations SA
