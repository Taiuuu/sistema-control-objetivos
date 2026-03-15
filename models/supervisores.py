# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de supervisores
# =============================================================================

import sqlite3
from database.db import DB_PATH


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
    conexion.commit()
    conexion.close()


# =============================================================================
# CONSULTA
# =============================================================================

def listar_supervisores() -> list:
    """Retorna todos los supervisores registrados en el sistema."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM supervisores")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado