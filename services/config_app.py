# =============================================================================
# VESP - Configuración de funciones opcionales (servidor remoto / multi-usuario)
# =============================================================================

import os

VESP_DATA_DIR = os.path.join(os.path.expanduser("~"), "VESP Control")


def sync_remoto_habilitado() -> bool:
    """True solo si hay servidor remoto configurado (desactivado por defecto)."""
    return os.environ.get("VESP_SYNC_REMOTO", "0").lower() in ("1", "true", "yes", "on")


def ruta_sync_queue() -> str:
    return os.path.join(VESP_DATA_DIR, "sync_queue.json")
