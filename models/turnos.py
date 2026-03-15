# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de registro de pasadas (turnos)
# =============================================================================

import sqlite3
from database.db import DB_PATH


# =============================================================================
# ALTA
# =============================================================================

def registrar_turno(fecha: str, hora: str, turno: str, objetivo_id: int, supervisor_id: int) -> None:
    """
    Registra una pasada de un supervisor por un objetivo.
    turno: 'dia' o 'noche'
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
        VALUES (?, ?, ?, ?, ?)
    """, (fecha, hora, turno, objetivo_id, supervisor_id))
    conexion.commit()
    conexion.close()


# =============================================================================
# CONSULTA
# =============================================================================

def listar_turnos_del_dia(fecha: str) -> list:
    """
    Retorna todas las pasadas registradas para una fecha dada,
    incluyendo nombre del objetivo y del supervisor.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    """, (fecha,))
    resultado = cursor.fetchall()
    conexion.close()
    return resultado