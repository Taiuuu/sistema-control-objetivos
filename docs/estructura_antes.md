# Estructura y dependencias antes de la reorganización

## Línea base

- Rama solicitada: `reorganizacion` (ya estaba activa; el árbol estaba limpio antes de compilar).
- `python -m compileall .`: completó sin errores.
- `python -m pytest`: no pudo iniciar porque el entorno no reconoce las opciones `--cov` configuradas en `pytest.ini` (no está instalado `pytest-cov`).
- `python -m pytest -o addopts='--verbose --strict-markers --tb=short'`: recolectó 208 casos y se detuvo por 4 errores de colección; todos se deben a que PyQt6 no puede cargar `libGL.so.1`.
- `python scripts/verificar_estructura.py`: devolvió código distinto de cero; los imports de módulos PyQt6 fallan por la misma biblioteca del sistema ausente.
- La compilación regeneró bytecode que ya estaba versionado; esos archivos se retirarán del índice en la limpieza solicitada.

## Mapa AST

Se inspeccionaron los `Import`, `ImportFrom` y niveles relativos con `ast` sobre los paquetes existentes. El grafo entre paquetes tiene estas relaciones observadas:

| Origen | Destinos internos observados |
|---|---|
| `api` | `core`, `database`, `models`, `services` |
| `core` | `database`, `services` |
| `database` | Sin imports a `ui` ni `services` |
| `models` | `database` (violación de la dirección deseada) |
| `scripts` | `api`, `core`, `database`, `models`, `services`, `ui` |
| `services` | `core`, `database`, `models` |
| `tests` | `api`, `database`, `models`, `services`, `tests`, `ui` |
| `ui` | `core`, `database`, `models`, `services`, `ui` |

La dependencia directa `ui -> database` existe en pantallas y widgets, y hay imports de PyQt6 en `services.actualizador`, `services.background_task`, `services.notificaciones` y `services.sincronizacion`. Se conservan como deuda conocida; esta reorganización no cambia lógica ni sustituye esos accesos.

## Rutas sensibles detectadas

- `scripts/main.py`, `scripts/restaurar_backup.py`, `scripts/preview_components.py` y `scripts/verificar_pasadas_excel.py` calculan la raíz desde `__file__`.
- `services.actualizador` lee `version.txt` desde el directorio de trabajo y consulta la URL remota `.../main/version.txt`.
- `tests/test_importador_integridad.py` construye la ruta del Excel de septiembre desde la raíz; `tests/test_parser.py` apunta a un Excel de agosto que no está en el inventario versionado.
- `tests/test_golden_pasadas.py` resuelve el fixture desde `tests/` y el JSON dorado está en `tests/golden/`.
- `ui/login.py` resuelve `docs/version.txt` a partir de `__file__`.
- No hay archivos `.spec` versionados. `scripts/instalador.iss`, el workflow de release, la guía del instalador y los comandos `pyinstaller` sí contienen rutas de empaquetado.

## Datos versionados

`CONTROL RECORRIDOS - SEPTIEMBRE - 2026.xlsx`, `seguridad.db`, `sync_queue.json`, `version.txt` y varios `.pyc` están versionados. El Excel contiene datos reales de supervisores y objetivos; su movimiento a `tests/fixtures/` requiere actualizar su prueba. No se modifica `.gitignore` para ese movimiento.