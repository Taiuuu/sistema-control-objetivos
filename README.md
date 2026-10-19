# VESP Organizations

VESP Organizations es una aplicación de escritorio para gestionar rondas de seguridad privada.
Permite registrar pasadas por turno, administrar objetivos, supervisores y equipos, generar
reportes de cumplimiento e importar recorridos desde Excel.

**Versión actual:** 1.7.4 (definida en `version.txt`)
**Aplicación principal:** PyQt6 + SQLite
**API REST:** servicio Flask auxiliar; no reemplaza la aplicación de escritorio

## Funcionalidades

- Gestión de objetivos, supervisores, equipos, turnos y pasadas diurnas/nocturnas.
- Importación Excel con vista previa, detección de duplicados y resolución de coincidencias.
- Reportes mensuales, diarios y por objetivo con exportación a Excel y PDF.
- Usuarios con roles y permisos (`admin`, `supervisor`, `auditor`, `gerente` y `operador`), auditoría y control de sesiones.
- Feriados, notas diarias, copias de seguridad verificadas y restauración.
- Interfaz PyQt6 con temas claro y oscuro.

## Integridad de la importación VESP

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
el turno no altera la identidad. La migración respalda la base antes de archivar copias
previas repetidas, conserva la de menor ID en `pasadas` y guarda las demás en
`pasadas_duplicados_migracion`, y crea un índice único. Cada confirmación crea un backup
previo y ejecuta altas, cambios y auditoría en una única transacción; una conciliación
fallida revierte las escrituras.

![Vista previa de importación Excel](docs/img/vista-previa-importacion.png)

## Cómo se cuentan las pasadas

La pasada de madrugada marcada como **NOCHE** pertenece al turno que empezó el día
anterior: si su hora es anterior a las 08:00, su fecha de turno es el día anterior.
El mes de una pasada se determina por esa fecha de turno, no por la fecha calendario
de madrugada. Se respeta el turno informado; la hora por sí sola no resuelve los
intervalos superpuestos entre DIA y NOCHE.

Ejemplos:

- 14/10/2026 a las 03:00, NOCHE → turno del 13/10; cuenta en octubre.
- 01/11/2026 a las 02:00, NOCHE → turno del 31/10; cuenta en octubre.
- 14/10/2026 a las 07:40, DIA → turno del 14/10; cuenta en octubre.

Para los casos límite y la regla completa, consultá [las reglas de cálculo](docs/reglas_de_calculo.md).

## Requisitos

- Python 3.10 o superior.
- Dependencias de la aplicación definidas en `requirements.txt`. El instalador Inno Setup es para Windows.

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

Reemplazá los marcadores de `.env.example` por valores propios. La API Flask exige
`VESP_JWT_SECRET` y `VESP_SSE_PUBLISH_TOKEN` para iniciar; las funciones de cifrado
requieren `VESP_ENCRYPTION_KEY`. La tabla resume las variables de entorno que consulta la aplicación Python (incluida
`TEST_DB_PATH`, usada principalmente por las pruebas), no las variables de workflows de CI.
El ejemplo también menciona opciones sin consumidor implementado.

| Variable | Para qué sirve | Valor por defecto | ¿Obligatoria? |
|---|---|---|---|
| `VESP_DB_PATH` | Ruta de la base SQLite. | `~/VESP Control/seguridad.db` (salvo que se use `TEST_DB_PATH`). | No |
| `TEST_DB_PATH` | Ruta alternativa de base, usada principalmente por las pruebas; se considera solo si no está definida `VESP_DB_PATH`. | Sin valor. | No |
| `VESP_BACKUP_EXTERNAL_PATH` | Carpeta para una copia externa adicional. | Sin valor; también se puede configurar desde la interfaz. | No |
| `VESP_ENCRYPTION_KEY` | Clave para las funciones de cifrado de sesión. | Sin valor. | No para iniciar; sí para usar el cifrado. |
| `VESP_SYNC_REMOTO` | Activa el flujo de sincronización remota (requiere un servidor remoto configurado). | Desactivada (`0`). | No |
| `VESP_JWT_SECRET` | Firma de los JWT de la API Flask. | Sin valor. | Sí para iniciar la API. |
| `VESP_SSE_PUBLISH_TOKEN` | Token configurado para publicación SSE desde la API. | Sin valor. | Sí para iniciar la API. |
| `VESP_RATE_LIMIT_STORAGE_URI` | Almacenamiento del rate limiting de la API. | Memoria local (`memory://`). | No |
| `VESP_REDIS_URL` | Redis usado por el transporte de eventos SSE. | Redis local (`redis://localhost:6379/0`). | No; Redis debe estar disponible para las operaciones SSE. |
| `VESP_API_HOST` | Dirección de escucha de la API. | `127.0.0.1`. | No |
| `VESP_API_PORT` | Puerto de escucha de la API. | `5000`. | No |
| `VESP_API_DEBUG` | Activa el modo debug de Flask. | Desactivado (`false`). | No |

Aunque `VESP_SSE_PUBLISH_TOKEN` se exige al arrancar, la ruta `/api/sse/publish` no compara
el encabezado con el valor configurado y el emisor local tampoco lo usa para construirlo.
No uses esa ruta hasta corregir ambas partes. No publiques secretos en el README ni en el
repositorio.

## Uso

### Aplicación de escritorio

```bash
python scripts/main.py
```

En el primer inicio se crea o actualiza la base SQLite local, se ejecutan las migraciones y se
abre la pantalla de login. La instalación crea una cuenta administradora inicial y exige
cambiar su contraseña en el primer acceso. No se documentan aquí las credenciales iniciales.

![Pantalla principal de VESP Organizations](docs/img/pantalla-principal.png)
![Reporte de cumplimiento](docs/img/reporte-cumplimiento.png)

### Reportes y exportación

Las pantallas **Lista de pasadas**, **Reporte mensual** y **Reporte por objetivo** usan
el diálogo **Exportar**. La selección inicial parte de los filtros de la pantalla y puede
ajustarse: período (mes, rango o día), objetivos, supervisores, equipo, turnos, columnas y
orden, contenido (resumen, detalle o ambos), agrupación y formato Excel/PDF. La vista previa
muestra hasta 100 filas y el total; si no hay resultados, no se crea un archivo vacío.

El resumen mensual y el reporte por objetivo requieren un mes calendario completo; el
reporte por objetivo requiere un único objetivo. La lista de pasadas exporta detalle del
día elegido. No existe una pantalla independiente de reporte diario. Las plantillas y la
última carpeta se guardan en la configuración local de la aplicación.

El Excel incluye **Resumen**, **Detalle** si se solicita y **Parámetros** con período,
filtros, criterio de turnos, generación, usuario y versión. Sus encabezados, filtros,
totales, tipos numéricos y ajustes de impresión están preparados para pantalla e impresión.
El PDF se genera en A4 vertical u horizontal, con fuentes que admiten tildes y eñes,
encabezados repetidos al paginar y subtotales de agrupación. Ambos formatos se generan
desde la misma instantánea de datos. Cada archivo se registra en auditoría; el proceso no
modifica pasadas ni datos de negocio.

Para probar la exportación, abrí un reporte, elegí **Exportar**, actualizá la vista previa,
seleccioná columnas/contenido/formato y continuá. Un archivo existente no se sobrescribe;
si está abierto en Excel o un visor, cerralo o elegí otra ruta. Al terminar podés abrir el
archivo o su carpeta. Para más pasos, consultá el [manual de usuario](docs/MANUAL_USUARIO.md).

### Copias de seguridad y recuperación

La ruta de la base se configura con `VESP_DB_PATH`; si no se define, VESP conserva la
ubicación histórica `~/VESP Control/seguridad.db`. Junto a la base crea `data/backups/`,
`data/logs/` y `data/exports_seguridad/`. La carpeta `data/` contiene datos locales y no se
versiona.

VESP crea un backup diario al iniciar y una copia previa verificada antes de importar,
borrar un mes o ejecutar las migraciones de arranque. En Configuración → Copias de seguridad
se puede crear una copia manual, elegir una carpeta externa y restaurar una copia verificada.
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

Por defecto escucha en `127.0.0.1:5000`. El host, puerto y modo debug pueden configurarse
con `VESP_API_HOST`, `VESP_API_PORT` y `VESP_API_DEBUG`.
El rate limiting usa almacenamiento en memoria por defecto; para que los límites se compartan
entre procesos, configurá `VESP_RATE_LIMIT_STORAGE_URI` con una URL Redis.
El stream `/api/sse/events` requiere un JWT de usuario y usa Redis, configurable con
`VESP_REDIS_URL`. Aunque existe `POST /api/sse/publish`, su validación no usa el token
configurado: no la consideres operativa ni segura hasta corregirla. No hay una ruta
`/api/docs` registrada al iniciar la aplicación.

Rutas implementadas:

- `POST /api/auth/login`
- `GET /api/auth/protected` (requiere JWT)
- `GET|POST /api/objetivos`; `GET|PUT|DELETE /api/objetivos/<id>`
- `GET|POST /api/supervisores`; `GET|PUT|DELETE /api/supervisores/<id>`
- `POST /api/pasadas`; `GET /api/pasadas/dia/<fecha>`
- `GET /api/reportes/mensual/<anio>/<mes>` y `GET /api/reportes/diario/<fecha>`
- `GET /api/sse/events` (requiere JWT)
- `POST /api/sse/publish` (validación del token pendiente de corregir)

## Pruebas

Para instalar las dependencias de desarrollo y cobertura:

```bash
python -m pip install -r docs/requirements-dev.txt
```

Ejecutá la suite con:

```bash
python -m pytest
```

El smoke test adicional de imports, pantallas y rutas se ejecuta con:

```bash
python scripts/verificar_estructura.py
```

La prueba dorada `tests/test_golden_pasadas.py` usa
`tests/fixtures/CONTROL RECORRIDOS - OCTUBRE - 2026 COMPLETO.xlsx` y compara el resultado
con `tests/golden/2026-10.json`. Ese JSON está marcado **SIN VERIFICAR**; no tomes su conteo
como dato validado. También hay un Excel de septiembre en `tests/fixtures/`, pero no es la
fuente de esa prueba dorada.

## Estructura

- `api/` - Aplicación Flask y rutas organizadas en blueprints.
- `assets/` - Logos e imágenes compartidas.
- `core/` - Configuración de rutas de datos, instancia y logging.
- `database/` - Acceso a SQLite, esquema y migraciones.
- `docs/` - Manuales, reglas, contextos y documentación de desarrollo.
- `models/` - Entidades, tipos y validaciones de dominio.
- `scripts/` - Inicio de escritorio y utilidades de mantenimiento/verificación.
- `services/` - Servicios de aplicación, importador, pasadas, backups y reportes.
- `tests/` - Pruebas, datos de entrada en `fixtures/` y datos dorados en `golden/`.
- `ui/` - Interfaz PyQt6, componentes, importador, reportes, temas y widgets.

La descripción ampliada está en [docs/estructura.md](docs/estructura.md).

## Documentación adicional

- [Manual de usuario](docs/MANUAL_USUARIO.md)
- [Índice de contextos para desarrollo](docs/contexts/00-indice.md)
- [Estructura del proyecto](docs/estructura.md)
- [Reglas de cálculo de pasadas](docs/reglas_de_calculo.md)
- [Guía del instalador](GUIA_INSTALADOR_INNO_SETUP.txt)

## Autoría

Taiel Clot - VESP Organizations SA
