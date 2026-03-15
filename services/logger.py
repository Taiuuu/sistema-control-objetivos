# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de registro de acciones del sistema (logs de auditoría)
# =============================================================================

import sqlite3
import datetime
from database.db import DB_PATH


# =============================================================================
# REGISTRO
# =============================================================================

def registrar_accion(usuario_id: int | None, accion: str) -> None:
    """
    Registra una acción realizada en el sistema.
    Cada registro incluye fecha, hora, usuario y descripción de la acción.
    usuario_id puede ser None en acciones del sistema sin usuario activo.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    ahora = datetime.datetime.now()
    cursor.execute("""
        INSERT INTO logs (fecha, hora, usuario_id, accion)
        VALUES (?, ?, ?, ?)
    """, (
        ahora.strftime("%Y-%m-%d"),
        ahora.strftime("%H:%M:%S"),
        usuario_id,
        accion
    ))

    conexion.commit()
    conexion.close()