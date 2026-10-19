# Inventario de referencias para la reorganización

Inventario inicial generado antes de mover rutas. Se debe repetir la búsqueda global tras cada lote; este documento no reemplaza esa comprobación.

## Imports y carga dinámica

- Imports absolutos y relativos Python: analizados con `ast` en todos los `.py` versionados, incluidos tests y scripts.
- Carga dinámica: `scripts/verificar_estructura.py` usa `importlib.import_module`; `tests/test_importador_integridad.py` usa `__import__("io")`.
- No se encontraron configuraciones `.spec` versionadas ni registros de plugins por nombre de módulo.
- `scripts/verificar_estructura.py` enumera módulos mediante `Path.rglob("*.py")` y fija el directorio de trabajo en la raíz.

## Rutas de archivos y recursos

- Referencias calculadas con `__file__`: `scripts/main.py`, `scripts/preview_components.py`, `scripts/restaurar_backup.py`, `scripts/verificar_estructura.py`, `scripts/verificar_pasadas_excel.py`, `tests/conftest.py`, `tests/diagnostico_excel.py`, tests individuales, `ui/login.py`.
- Accesos de recursos: `services/assets.py`, `ui/theme/tokens.py`, estilos QSS de `ui/`, hojas de estilo y rutas de imágenes bajo `assets/`.
- Excel de septiembre: `tests/test_importador_integridad.py` lo busca en la raíz; el destino propuesto es `tests/fixtures/`.
- Excel de agosto: `tests/test_parser.py` refiere `CONTROL RECORRIDOS AGOSTO 2026 (2).xlsx`, no presente entre archivos versionados.
- Archivos JSON/rutas runtime: `services/sync_manager.py` y `sync_queue.json`; `services/import_history.py`; versión raíz leída por `services/actualizador.py`; `docs/version.txt` leído por `ui/login.py`.
- Búsquedas de `open`, `Path`, `os.path`, `__file__`, `url(`, `importlib`, `hiddenimports` y rutas de Excel cubrieron `.py`, `.spec`, `.iss`, `.qss`, `.md`, `.txt`, `.json`, `.yml`, `.yaml`, `.bat` y `.ps1` versionados.

## Empaquetado, arranque y configuración

- Entrada desktop: `scripts/main.py`; la documentación la inicia con `python scripts/main.py`.
- Entrada Flask: `python -m api.app`; blueprints en `api/routes/` y especificación en `api/docs.py`.
- Inno Setup: `instalador.iss` en la raíz; `GUIA_INSTALADOR_INNO_SETUP.txt` y `.github/workflows/release.yml` apuntan a esa ubicación.
- No hay `.spec` versionados; `.gitignore` ignora `*.spec`. La guía contiene el comando PyInstaller y rutas de datos `assets`.
- CI: `.github/workflows/tests.yml` y `.github/workflows/release.yml`; pytest usa `pytest.ini` y `tests/conftest.py`.
- Tests dorados/fixtures: `tests/golden/`, `tests/fixtures/`, `tests/test_golden_pasadas.py` y `tests/test_importador_integridad.py`.

## Documentación y rutas mencionadas

- Rutas literales de arranque y estructura en `README.md`, `docs/MANUAL_USUARIO.md`, `docs/analisis_calculo_pasadas.md` y `GUIA_INSTALADOR_INNO_SETUP.txt`.
- La documentación de diseño está en `docs/contexts/ui-theme.md`.
- El script base del instalador incluye rutas absolutas específicas de Windows (`C:\\Proyecto Vesp\\...`); no se pueden validar en este contenedor Linux.

## Observaciones

- `seguridad.db`, el Excel de septiembre, `sync_queue.json`, `version.txt` y bytecode `.pyc` aparecen en el índice Git.
- La raíz contiene también `CONTROL RECORRIDOS - OCTUBRE - 2026.xlsx`, que no aparece en el índice y no se debe mover hasta verificar si es un dato local.
- `.gitignore` ya incluye `__pycache__/`, `*.py[cod]`, `data/`, `.venv/`, `venv/`, `dist/`, `build/` y `.env`.