# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Script de reset de fábrica - borra todos los datos del sistema
# USAR CON PRECAUCIÓN - esta acción no se puede deshacer
# =============================================================================

import sqlite3
import bcrypt
import logging
from database.db import DB_PATH
from services.backups.backup import crear_backup
from core.logging_config import configurar_logging
from core.instancia import adquirir_bloqueo_instancia

logger = logging.getLogger(__name__)

def reset_fabrica():
    confirmar = input("¿Seguro que querés borrar TODOS los datos? Escribí CONFIRMAR para continuar: ")
    if confirmar != "CONFIRMAR":
        print("Reset cancelado.")
        return

    bloqueo = adquirir_bloqueo_instancia(DB_PATH)
    if bloqueo is None:
        mensaje = "No se puede resetear mientras VESP está abierto."
        logger.error(mensaje)
        print(mensaje)
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        crear_backup("manual", conexion_origen=conn)
        conn.execute("BEGIN")
        # Borrar todos los datos de todas las tablas en una sola transacción.
        conn.execute("DELETE FROM pasadas")
        conn.execute("DELETE FROM equipos")
        conn.execute("DELETE FROM objetivos")
        conn.execute("DELETE FROM supervisores")
        conn.execute("DELETE FROM notas")
        conn.execute("DELETE FROM logs")
        conn.execute("DELETE FROM usuarios")
        conn.execute("DELETE FROM sqlite_sequence")

        password_hash = bcrypt.hashpw(b"0000", bcrypt.gensalt()).decode()
        conn.execute("""
            INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
            VALUES (?, ?, ?, ?)
        """, ("admin", password_hash, "admin", 0))
        conn.commit()
        logger.info("Reset de fábrica completado; backup verificado creado.")
    except Exception:
        conn.rollback()
        logger.exception("Falló el reset de fábrica; se aplicó rollback")
        raise
    finally:
        conn.close()
        bloqueo.unlock()

    print("Reset completado. El sistema quedó como de fábrica.")
    print("Usuario: admin | Contraseña: 0000")


if __name__ == "__main__":
    configurar_logging()
    reset_fabrica()