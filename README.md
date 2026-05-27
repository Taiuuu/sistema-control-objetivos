# VESP Control de Objetivos

Sistema de gestión de rondas y objetivos basado en escritorio con PyQt6 y SQLite. Esta aplicación está diseñada para operaciones de control interno, importación de datos desde Excel, gestión de objetivos, seguridad de sesiones y soporte básico de API REST local.

## Estructura del proyecto

- `scripts/` - Lanzador principal y utilidades de mantenimiento.
- `ui/` - Interfaces gráficas PyQt6 para todas las pantallas de la aplicación.
- `services/` - Lógica de negocio, validaciones, importadores, sincronización, backup y notificaciones.
- `database/` - Acceso y migración de la base de datos SQLite.
- `models/` - Definiciones de entidades y validaciones de dominio.
- `api/` - API REST independiente y rutas Flask.
- `docs/` - Documentación técnica y guías internas.
- `tests/` - Suite de pruebas automatizadas.

## Dependencias

Instala las dependencias con:

```bash
python -m pip install -r requirements.txt
```

Requisitos claves:

- Python 3.11+ / 3.14 compatible
- PyQt6
- Flask
- openpyxl
- pandas
- bcrypt
- redis (si se usa SSE y notificaciones)

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos
```

2. Crea un entorno virtual y activa:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

4. Copia la plantilla de variables de entorno:

```bash
copy .env.example .env
```

5. Ajusta `JWT_SECRET_KEY` y `ENCRYPTION_KEY` en `.env`.

## Ejecución

### Ejecutar la aplicación de escritorio

```bash
python scripts/main.py
```

La aplicación inicializa:

- base de datos SQLite local
- migraciones de esquema
- backup automático
- servidor API local de soporte
- interfaz de login y ventana principal

### Ejecutar la API Flask independiente

```bash
python api/app.py
```

Esto arranca el servidor Flask en `http://0.0.0.0:5000`.

## Pruebas

Ejecuta la suite de pruebas con:

```bash
python -m pytest
```

## Configuración

Variables de entorno relevantes disponibles en `.env.example`:

- `VESP_JWT_SECRET` - Secreto JWT para la API
- `VESP_ENCRYPTION_KEY` - Clave de cifrado
- `VESP_DB_PATH` - Ruta opcional a la base de datos SQLite
- `VESP_API_HOST` - Host de la API
- `VESP_API_PORT` - Puerto de la API
- `VESP_API_DEBUG` - Activar modo debug para la API
- `VESP_LOG_LEVEL` - Nivel de logging

## Notas de arquitectura

- La UI está construida con PyQt6 en `ui/`.
- La lógica se agrupa en `services/` para separar validaciones, importadores, sincronización y reportes.
- La base de datos SQLite se maneja desde `database/db.py` y `database/gestor_db.py`.
- La carpeta `api/` contiene una versión Flask de la API REST y rutas modulares.

## Autor y empresa

- Autor: Clot Taiel
- Empresa: V.E.S.P Organizations SA
