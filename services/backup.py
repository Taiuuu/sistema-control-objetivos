# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de backup automático de la base de datos
# =============================================================================

import os
import shutil
import datetime
from database.db import DB_PATH


BACKUP_DIR = "backups"
DIAS_RETENTION = 30  # Cantidad de días que se conservan los backups


# =============================================================================
# BACKUP
# =============================================================================

def hacer_backup() -> None:
    """
    Crea una copia de seguridad de la base de datos con la fecha en el nombre.
    Solo genera un backup por día. Elimina backups con más de DIAS_RETENTION días.
    """
    if not os.path.exists(DB_PATH):
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)

    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")

    # Evitar duplicados del mismo día
    backups_hoy = [f for f in os.listdir(BACKUP_DIR) if fecha_hoy in f]
    if backups_hoy:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    destino = os.path.join(BACKUP_DIR, f"seguridad_{timestamp}.db")
    shutil.copy2(DB_PATH, destino)
    print(f"Backup creado: {destino}")

    _limpiar_backups_antiguos()


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
        fecha_modificacion = datetime.datetime.fromtimestamp(os.path.getmtime(ruta))
        dias_diferencia = (ahora - fecha_modificacion).days

        if dias_diferencia > DIAS_RETENTION:
            os.remove(ruta)
            print(f"Backup eliminado por antigüedad: {archivo}")