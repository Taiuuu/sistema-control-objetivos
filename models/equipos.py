# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de equipos de turno
# =============================================================================

import sqlite3
from database.db import DB_PATH
from services.sincronizacion import notificar_cambio


def guardar_equipo_turno(fecha: str, turno: str, supervisor1_id: int, supervisor2_id: int) -> None:
    """
    Registra los dos supervisores asignados a un turno en una fecha.
    Si ya existe un equipo para esa fecha y turno lo reemplaza.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM equipos WHERE fecha = ? AND turno = ?", (fecha, turno))
    cursor.execute("""
        INSERT INTO equipos (fecha, turno, supervisor1_id, supervisor2_id)
        VALUES (?, ?, ?, ?)
    """, (fecha, turno, supervisor1_id, supervisor2_id))
    equipo_id = cursor.lastrowid
    conexion.commit()
    conexion.close()

    # Notificar cambio para sincronización
    notificar_cambio("equipos", "INSERT", {
        "id": equipo_id,
        "fecha": fecha,
        "turno": turno,
        "supervisor1_id": supervisor1_id,
        "supervisor2_id": supervisor2_id
    })