# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de registro de pasadas (turnos)
# =============================================================================

import sqlite3
from database.db import DB_PATH
from services.sincronizacion import notificar_cambio


def registrar_turno(fecha: str, hora: str | None, turno: str, objetivo_id: int, supervisor_id: int) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
        VALUES (?, ?, ?, ?, ?)
    """, (fecha, hora, turno, objetivo_id, supervisor_id))
    pasada_id = cursor.lastrowid
    conexion.commit()
    conexion.close()

    # Notificar cambio para sincronización
    notificar_cambio("pasadas", "INSERT", {
        "id": pasada_id,
        "fecha": fecha,
        "hora": hora,
        "turno": turno,
        "objetivo_id": objetivo_id,
        "supervisor_id": supervisor_id
    })
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