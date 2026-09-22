# VESP Control de Objetivos

VESP Control de Objetivos es una aplicación de escritorio para gestionar rondas de seguridad
privada. Permite registrar pasadas por turno, administrar objetivos, supervisores y equipos,
generar reportes de cumplimiento e importar recorridos desde Excel.

**Versión actual:** 1.5.2 estable
**Aplicación principal:** PyQt6 + SQLite
**API REST:** servicio Flask auxiliar local, no reemplaza la aplicación de escritorio

## Funcionalidades

- Gestión de objetivos, supervisores, equipos y pasadas diurnas/nocturnas.
- Importación de archivos Excel `CONTROL_RECORRIDOS`, con vista previa y detección de duplicados.
- Reportes mensuales y diarios con exportación a Excel y PDF.
- Usuarios, roles, permisos, cambio obligatorio de contraseña y control de sesiones.
- Auditoría de operaciones, copias de seguridad automáticas y restauración/fábrica.
- Feriados, notas diarias, sincronización y notificaciones según la configuración instalada.

## Requisitos

- Python 3.10 o superior.
- Windows para la aplicación distribuida; el código usa SQLite y puede ejecutarse en otros sistemas con sus dependencias de Python.

## Instalación

```bash
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

python -m pip install -r requirements.txt
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
```

Antes de usar la aplicación o la API, reemplazar en `.env` los valores de ejemplo de
`VESP_JWT_SECRET` y `VESP_ENCRYPTION_KEY` por secretos propios. El resto de las variables es
opcional y está documentado en `.env.example`.

## Uso

### Aplicación de escritorio

```bash
python scripts/main.py
```

En el primer inicio se crea o actualiza la base SQLite local, se ejecutan las migraciones y se
abre la pantalla de login. Las credenciales iniciales son `admin` / `0000`; el cambio de
contraseña es obligatorio en el primer acceso.

### API REST independiente

La API requiere `VESP_JWT_SECRET` y se inicia desde la raíz del proyecto:

```bash
python -m api.app
```

Por defecto queda disponible en `http://127.0.0.1:5000`. El host, puerto y modo debug pueden
configurarse con `VESP_API_HOST`, `VESP_API_PORT` y `VESP_API_DEBUG`. La especificación OpenAPI
está disponible en `GET /api/docs`.

Rutas principales:

- `POST /api/auth/login`
- `GET|POST /api/objetivos`
- `GET|POST /api/supervisores`
- `GET|POST /api/pasadas`
- `GET /api/reportes/mensual/<anio>/<mes>`
- `GET /api/sse/events`

## Pruebas

```bash
python -m pytest
```

Las dependencias de desarrollo adicionales se encuentran en `docs/requirements-dev.txt`.

## Estructura

- `scripts/` - Entrada principal y utilidades de mantenimiento.
- `ui/` - Ventanas y componentes de la interfaz PyQt6.
- `services/` - Lógica de negocio, importación, reportes, sincronización y seguridad.
- `models/` - Entidades y validaciones de dominio.
- `database/` - Inicialización, migraciones y acceso thread-safe a SQLite.
- `api/` - API Flask modular y sus blueprints.
- `tests/` - Pruebas automatizadas.
- `docs/` - Manual de usuario, contexto técnico y documentación de desarrollo.

## Documentación adicional

- [Manual de usuario](docs/MANUAL_USUARIO.md)
- [Contexto técnico](docs/CONTEXT.md)
- [Guía del instalador](GUIA_INSTALADOR_INNO_SETUP.txt)

## Autoría

Taiel Clot - V.E.S.P Organizations SA
