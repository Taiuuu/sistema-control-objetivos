# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de supervisores
# =============================================================================

import sqlite3
from database.db import DB_PATH
from services.cache import invalidar_supervisores
from services.sincronizacion import notificar_cambio


# =============================================================================
# ALTA
# =============================================================================

def agregar_supervisor(nombre: str) -> None:
    """Registra un nuevo supervisor en el sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO supervisores (nombre) VALUES (?)
    """, (nombre,))
    supervisor_id = cursor.lastrowid
    conexion.commit()
    conexion.close()

    # Notificar cambio para sincronización
    notificar_cambio("supervisores", "INSERT", {
        "id": supervisor_id,
        "nombre": nombre
    })
# =============================================================================

def listar_supervisores() -> list:
    """Retorna todos los supervisores registrados en el sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM supervisores")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado