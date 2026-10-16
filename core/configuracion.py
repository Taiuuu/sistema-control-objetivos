"""Rutas centrales de datos de VESP.

La ruta de la base conserva la ubicación histórica y permite migrar directorios
sin modificar el código mediante VESP_DB_PATH.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_APP_DATA_HOME = Path.home() / "VESP Control"
DB_PATH = Path(
    os.environ.get("VESP_DB_PATH")
    or os.environ.get("TEST_DB_PATH")
    or _APP_DATA_HOME / "seguridad.db"
).expanduser().resolve()
DATA_DIR = DB_PATH.parent / "data"
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"
EXPORTS_DIR = DATA_DIR / "exports_seguridad"
SETTINGS_PATH = DATA_DIR / "configuracion.json"


def asegurar_directorios() -> None:
    """Prepara el almacenamiento antes de cualquier operación de la app."""
    for directorio in (DB_PATH.parent, DATA_DIR, BACKUP_DIR, LOG_DIR, EXPORTS_DIR):
        directorio.mkdir(parents=True, exist_ok=True)


def obtener_ruta_backup_externo() -> Path | None:
    """Devuelve la copia externa configurada por entorno o por la interfaz."""
    configurada = os.environ.get("VESP_BACKUP_EXTERNAL_PATH")
    if not configurada and SETTINGS_PATH.exists():
        try:
            configurada = json.loads(SETTINGS_PATH.read_text(encoding="utf-8")).get(
                "backup_externo"
            )
        except (OSError, json.JSONDecodeError) as error:
            import logging
            logging.getLogger(__name__).warning(
                "No se pudo leer la configuración de copia externa: %s", error
            )
    return Path(configurada).expanduser() if configurada else None


def establecer_ruta_backup_externo(ruta: str | os.PathLike[str] | None) -> None:
    """Guarda la ruta opcional de copia externa elegida por el usuario."""
    asegurar_directorios()
    actual = {}
    if SETTINGS_PATH.exists():
        try:
            actual = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            import logging
            logging.getLogger(__name__).warning(
                "Se reemplazará una configuración ilegible: %s", error
            )
    actual["backup_externo"] = str(Path(ruta).expanduser()) if ruta else ""
    SETTINGS_PATH.write_text(
        json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8"
    )


asegurar_directorios()
