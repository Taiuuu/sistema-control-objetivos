# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de backup automático de la base de datos
# =============================================================================

import os
import shutil
import datetime
import hashlib
import json
from database.db import DB_PATH


BACKUP_DIR = os.path.join(os.path.expanduser("~"), "VESP Control", "backups")
BACKUP_METADATA = os.path.join(BACKUP_DIR, "backup_meta.json")
DIAS_RETENTION = 30


# =============================================================================
# BACKUP
# =============================================================================

def hacer_backup() -> bool:
    """
    Crea una copia de seguridad inteligente de la base de datos.
    - Solo genera un backup si hay cambios reales en el archivo.
    - Evita duplicados idénticos.
    - Mantiene la retención de backups antiguos.
    """
    if not os.path.exists(DB_PATH):
        return False

    os.makedirs(BACKUP_DIR, exist_ok=True)

    metadata = _leer_metadata()
    db_stat = os.stat(DB_PATH)
    mtime = db_stat.st_mtime
    size = db_stat.st_size

    if metadata:
        if metadata.get("db_mtime") == mtime and metadata.get("db_size") == size:
            return False

    current_hash = _hash_archivo(DB_PATH)

    if metadata and metadata.get("db_hash") == current_hash:
        metadata.update({
            "db_mtime": mtime,
            "db_size": size,
            "last_checked": datetime.datetime.now().isoformat()
        })
        _guardar_metadata(metadata)
        return False

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    destino = os.path.join(BACKUP_DIR, f"seguridad_{timestamp}.db")
    shutil.copy2(DB_PATH, destino)
    print(f"Backup creado: {destino}")

    metadata = {
        "last_backup": datetime.datetime.now().isoformat(),
        "last_backup_file": os.path.basename(destino),
        "db_hash": current_hash,
        "db_mtime": mtime,
        "db_size": size,
    }
    _guardar_metadata(metadata)
    _limpiar_backups_antiguos()
    return True


def _hash_archivo(ruta: str) -> str:
    """Calcula el hash SHA256 del archivo dado."""
    hash_sha256 = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(8192), b""):
            hash_sha256.update(bloque)
    return hash_sha256.hexdigest()


def _leer_metadata() -> dict:
    """Lee el archivo de metadata si existe."""
    if not os.path.exists(BACKUP_METADATA):
        return {}

    try:
        with open(BACKUP_METADATA, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception:
        return {}


def _guardar_metadata(metadata: dict) -> None:
    """Guarda la metadata de backup en disco."""
    try:
        with open(BACKUP_METADATA, "w", encoding="utf-8") as archivo:
            json.dump(metadata, archivo, indent=2)
    except Exception as e:
        print(f"Error guardando metadata de backup: {e}")


# =============================================================================
# LIMPIEZA
# =============================================================================

def _limpiar_backups_antiguos() -> None:
    """Elimina backups que superan el límite de retención configurado."""
    if not os.path.exists(BACKUP_DIR):
        return

    ahora = datetime.datetime.now()

    for archivo in os.listdir(BACKUP_DIR):
        ruta = os.path.join(BACKUP_DIR, archivo)
        if not os.path.isfile(ruta) or archivo == os.path.basename(BACKUP_METADATA):
            continue

        fecha_modificacion = datetime.datetime.fromtimestamp(os.path.getmtime(ruta))
        dias_diferencia = (ahora - fecha_modificacion).days

        if dias_diferencia > DIAS_RETENTION:
            os.remove(ruta)
            print(f"Backup eliminado por antigüedad: {archivo}")