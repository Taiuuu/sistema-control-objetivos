# VESP Control de Objetivos

Sistema profesional de gestión de seguridad privada para el registro, supervisión y reporte de objetivos operativos.

Desarrollado por Taiel Clot.

---

## ¿Qué hace este proyecto?

VESP es una aplicación de escritorio con soporte para API REST que permite:

- Registrar y administrar objetivos de seguridad.
- Controlar pasadas por turno diurno y nocturno.
- Gestionar supervisores y turnos.
- Generar reportes de cumplimiento y estadísticas.
- Mantener auditoría de operaciones y copias de seguridad.
- Autenticar usuarios con permisos según roles.

---

## Componentes principales

- `ui/`: Interfaz de usuario en PyQt6.
- `api/`: Endpoints REST para integración y sincronización.
- `services/`: Lógica de negocio, validaciones y operaciones sobre datos.
- `database/`: Conexión y acceso a SQLite.
- `models/`: Modelos de datos y validaciones.
- `tests/`: Pruebas de funcionamiento.

---

## Características centrales

- Gestión de objetivos, supervisores y pasadas.
- Reportes mensuales y exportación de datos.
- Sistema de roles y permisos.
- Auditoría de acciones y registros de eventos.
- Backups automáticos de la base de datos.
- Protección de datos sensibles con encriptación.

---

## Instalación desde código fuente

### Requisitos

- Python 3.8 o superior
- `pip`

### Instalación

```bash
cd "c:\Proyecto Vesp\sistema-control-objetivos"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Ejecución

```bash
python main.py
```

---

## Primer acceso

- Usuario: `admin`
- Contraseña: `0000`

Al iniciar por primera vez, el sistema crea la base de datos y puede solicitar el cambio de contraseña.

---

## API REST

La aplicación incluye endpoints para gestión de datos y sincronización.

Ejemplos de rutas:

- `POST /api/auth/login`
- `GET /api/objetivos`
- `POST /api/objetivos`
- `GET /api/supervisores`
- `POST /api/pasadas`
- `GET /api/reportes/mensual/<anio>/<mes>`

Para iniciar la API:

```bash
python -m api.app
```

---

## Tecnologías utilizadas

- Python 3
- PyQt6
- SQLite
- bcrypt
- openpyxl
- reportlab
- requests

---

## Autor

**Taiel Clot**

Desarrollador responsable del proyecto.

```
