# VESP Organizations

VESP Organizations es una aplicación de escritorio para gestionar rondas de seguridad privada.
Permite registrar pasadas por turno, administrar objetivos, supervisores y equipos, generar
reportes de cumplimiento e importar recorridos desde Excel.

**Versión actual:** 1.7.4
**Aplicación principal:** PyQt6 + SQLite
**API REST:** servicio Flask auxiliar local, no reemplaza la aplicación de escritorio

## Funcionalidades

- Gestión de objetivos, supervisores, equipos y pasadas diurnas/nocturnas.
- Importación de archivos Excel `CONTROL_RECORRIDOS`, con vista previa y detección de duplicados.
- Reportes mensuales y diarios con exportación a Excel y PDF.
- Usuarios, roles, permisos, cambio obligatorio de contraseña y control de sesiones.
- Auditoría de operaciones, copias de seguridad automáticas y restauración/fábrica.
- Feriados, notas diarias, sincronización y notificaciones según la configuración instalada.

### Integridad de la importación VESP

La pantalla **Importar desde Excel** analiza el archivo en modo de vista previa, sin
escribir en SQLite. El resumen concilia las filas leídas entre filas a insertar/actualizar,
duplicadas y rechazadas; el informe descargable incluye severidad, hoja, fila, bloque,
motivo y sugerencias para devolverlo a supervisión.

Se aceptan horas `HH:MM` y los separadores alternativos `HH.MM` y `HH;MM`, horas
numéricas como `8`, formatos incompletos como `8:5` y sufijos `AM/PM`.
Una hora imposible, una fecha de hoja inválida, una fila sin objetivo o una fecha fuera
del mes indicado en el nombre del archivo se rechazan con su posición en el Excel.
Las advertencias —por ejemplo una hora normalizada, orden horario dudoso o dos objetivos
distintos con una pasada a la misma hora— no bloquean las demás filas. Como el formato
actual no contiene coordenadas, el importador advierte sobre coincidencias horarias en
objetivos distintos y deja la verificación de distancia a supervisión.

Los nombres se comparan en mayúsculas, sin tildes y con espacios colapsados. Las colisiones
normalizadas no se resuelven por orden ni por similitud: se rechazan hasta corregir o
seleccionar un registro sin ambigüedad. Si el nombre del archivo no contiene un mes español
reconocible, se toma el mes de la primera hoja de datos válida y se comprueba que las demás
hojas pertenezcan a ese mismo mes.

La clave natural de SQLite es objetivo + fecha operativa + hora (minuto) + supervisor;
el turno no altera la identidad de una pasada. La migración respalda la base antes de
archivar copias previas repetidas (conserva la de menor ID y guarda las demás en
`pasadas_duplicados_migracion`) y crea un índice único. Cada confirmación crea un backup
previo y ejecuta altas, cambios y auditoría en una única transacción; una conciliación
fallida revierte todas las escrituras.

Los turnos operan en dos ciclos coordinados: DIA 07:00–19:00 con NOCHE 19:00–07:00,
o DIA 08:00–20:00 con NOCHE 20:00–08:00. La hora no basta para distinguir los turnos
en sus intervalos superpuestos; se respeta el turno informado. Las pasadas NOCHE
anteriores a las 08:00 se atribuyen a la fecha de turno del día anterior. Ver
[las reglas de cálculo](docs/reglas_de_calculo.md).

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
opcional y está documentado en `.env.example`. Para iniciar la API también es obligatorio
definir `VESP_SSE_PUBLISH_TOKEN` con un secreto propio; la API no tiene un valor
predeterminado para esta variable.

## Uso

### Aplicación de escritorio

```bash
python scripts/main.py
```

En el primer inicio se crea o actualiza la base SQLite local, se ejecutan las migraciones y se
abre la pantalla de login. Las credenciales iniciales son `admin` / `0000`; el cambio de
contraseña es obligatorio en el primer acceso.

### Copias de seguridad y recuperación

La ruta de la base se configura con `VESP_DB_PATH`; si no se define, VESP conserva la
ubicación histórica `~/VESP Control/seguridad.db`. Junto a la base crea `data/backups/`,
`data/logs/` y `data/exports_seguridad/`. La carpeta `data/` contiene datos locales y no se
versiona.

VESP crea un backup diario y una copia previa verificada antes de importar, borrar un mes o
ejecutar las migraciones de arranque. En Configuración → Copias de seguridad se puede crear
una copia manual, elegir una carpeta externa sincronizada y restaurar una copia verificada.
También se puede configurar la carpeta externa con `VESP_BACKUP_EXTERNAL_PATH`.

Si la interfaz no arranca, listá y restaurá copias desde una consola:

```bash
python scripts/restaurar_backup.py
python scripts/restaurar_backup.py --restaurar 1
```

El script muestra las copias verificadas y solicita escribir `RESTAURAR` antes de reemplazar
la base. Los errores y operaciones de recuperación quedan registrados en `data/logs/vesp.log`.

### API REST independiente

La API requiere `VESP_JWT_SECRET` y `VESP_SSE_PUBLISH_TOKEN`, definidos en `.env` o en el
entorno, y se inicia desde la raíz del proyecto:

```bash
python -m api.app
```

Por defecto queda disponible en `http://127.0.0.1:5000`. El host, puerto y modo debug pueden
configurarse con `VESP_API_HOST`, `VESP_API_PORT` y `VESP_API_DEBUG`. La especificación OpenAPI
está disponible en `GET /api/docs`.
El rate limiting usa almacenamiento en memoria por defecto; para que los límites se compartan
entre procesos, configurá `VESP_RATE_LIMIT_STORAGE_URI` con una URL Redis.
La publicación de notificaciones SSE requiere el encabezado
`Authorization: Bearer <VESP_SSE_PUBLISH_TOKEN>`. Definí un token secreto propio antes de
iniciar la API; no hay un valor predeterminado. El stream `/api/sse/events` requiere además
un JWT de usuario. Las notificaciones usan Redis; la URL se configura con `VESP_REDIS_URL`
(por defecto `redis://localhost:6379/0`).

Rutas principales:

- `POST /api/auth/login`
- `GET|POST /api/objetivos`
- `GET|POST /api/supervisores`
- `GET|POST /api/pasadas`
- `GET /api/reportes/mensual/<anio>/<mes>`
- `GET /api/sse/events`
- `POST /api/sse/publish` (requiere el token SSE configurado)

## Pruebas

Para instalar las dependencias de desarrollo y cobertura:

```bash
python -m pip install -r docs/requirements-dev.txt
```

```bash
python -m pytest
```

Las dependencias de desarrollo adicionales se encuentran en `docs/requirements-dev.txt`.
La prueba dorada del importador usa `tests/fixtures/CONTROL RECORRIDOS - SEPTIEMBRE - 2026.xlsx`
y crea un catálogo temporal a partir de los nombres presentes en ese mes;
no requiere mantener una lista fija de objetivos ni un JSON esperado aparte.

## Estructura

- `scripts/` - Entrada principal y utilidades de mantenimiento.
- `ui/` - Ventanas y componentes de la interfaz PyQt6.
- `services/` - Lógica de negocio, importación, reportes, sincronización y seguridad.
- `models/` - Entidades y validaciones de dominio.
- `database/` - Inicialización, migraciones y acceso thread-safe a SQLite.
- `api/` - API Flask modular y sus blueprints.
- `tests/` - Pruebas automatizadas.
- `docs/` - Manual de usuario, contextos del proyecto y documentación de desarrollo.

## Documentación adicional

- [Manual de usuario](docs/MANUAL_USUARIO.md)
- [Contexto de diseño de interfaz](docs/contexts/ui-theme.md)
- [Guía del instalador](GUIA_INSTALADOR_INNO_SETUP.txt)

## Autoría

Taiel Clot - VESP Organizations SA
