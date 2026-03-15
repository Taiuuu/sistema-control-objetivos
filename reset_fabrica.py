# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Script de reset de fábrica - borra todos los datos del sistema
# USAR CON PRECAUCIÓN - esta acción no se puede deshacer
# =============================================================================

import sqlite3
import os
import bcrypt


def reset_fabrica():
    confirmar = input("¿Seguro que querés borrar TODOS los datos? Escribí CONFIRMAR para continuar: ")
    if confirmar != "CONFIRMAR":
        print("Reset cancelado.")
        return

    conn = sqlite3.connect('seguridad.db')

    # Borrar todos los datos de todas las tablas
    conn.execute("DELETE FROM pasadas")
    conn.execute("DELETE FROM equipos")
    conn.execute("DELETE FROM objetivos")
    conn.execute("DELETE FROM supervisores")
    conn.execute("DELETE FROM notas")
    conn.execute("DELETE FROM logs")
    conn.execute("DELETE FROM usuarios")

    # Resetear los contadores de autoincremento
    conn.execute("DELETE FROM sqlite_sequence")

    # Recrear usuario admin por defecto sin requerir cambio de contraseña
    password_hash = bcrypt.hashpw(b"0000", bcrypt.gensalt()).decode()
    conn.execute("""
        INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
        VALUES (?, ?, ?, ?)
    """, ("admin", password_hash, "admin", 0))

    conn.commit()
    conn.close()

    # Borrar backups
    if os.path.exists("backups"):
        for archivo in os.listdir("backups"):
            os.remove(os.path.join("backups", archivo))
        print("Backups eliminados.")

    print("Reset completado. El sistema quedó como de fábrica.")
    print("Usuario: admin | Contraseña: 0000")


if __name__ == "__main__":
    reset_fabrica()