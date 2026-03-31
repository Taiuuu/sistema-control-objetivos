# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de registro de pasadas (turnos)
# =============================================================================

import sqlite3
from database.db import DB_PATH


def registrar_turno(fecha: str, hora: str | None, turno: str, objetivo_id: int, supervisor_id: int) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
        VALUES (?, ?, ?, ?, ?)
    """, (fecha, hora, turno, objetivo_id, supervisor_id))
    conexion.commit()
    conexion.close()


def registrar_turno_ambos(fecha: str, hora: str | None, turno: str, objetivo_id: int,
                          supervisor1_id: int, supervisor2_id: int) -> None:
    """Registra una pasada para los dos supervisores del turno al mismo tiempo."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
        VALUES (?, ?, ?, ?, ?)
    """, (fecha, hora, turno, objetivo_id, supervisor1_id))
    cursor.execute("""
        INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
        VALUES (?, ?, ?, ?, ?)
    """, (fecha, hora, turno, objetivo_id, supervisor2_id))
    conexion.commit()
    conexion.close()


def listar_turnos_del_dia(fecha: str) -> list:
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