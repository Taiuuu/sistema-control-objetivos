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


def obtener_supervisor(supervisor_id: int) -> tuple | None:
    """Retorna un supervisor específico por ID."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM supervisores WHERE id = ?", (supervisor_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


# =============================================================================
# MODIFICACIÓN
# =============================================================================

def actualizar_supervisor(supervisor_id: int, nombre: str) -> None:
    """Actualiza el nombre de un supervisor."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE supervisores SET nombre = ? WHERE id = ?
    """, (nombre, supervisor_id))
    conexion.commit()
    conexion.close()
    
    # Notificar cambio para sincronización
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "nombre": nombre
    })


# =============================================================================
# BAJA
# =============================================================================

def dar_de_baja_supervisor(supervisor_id: int) -> None:
    """Elimina un supervisor del sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM supervisores WHERE id = ?", (supervisor_id,))
    conexion.commit()
    conexion.close()
    
    # Notificar cambio para sincronización
    notificar_cambio("supervisores", "DELETE", {
        "id": supervisor_id
    })