# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de supervisores
# =============================================================================

import sqlite3
from database.db import DB_PATH
from services.sincronizacion import notificar_cambio


def agregar_supervisor(nombre: str, fecha_alta: str | None = None) -> None:
    """Registra un nuevo supervisor. Si no se indica fecha_alta usa hoy."""
    import datetime
    if not fecha_alta:
        fecha_alta = datetime.date.today().isoformat()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO supervisores (nombre, fecha_alta) VALUES (?, ?)
    """, (nombre, fecha_alta))
    supervisor_id = cursor.lastrowid
    conexion.commit()
    conexion.close()
    notificar_cambio("supervisores", "INSERT", {
        "id": supervisor_id,
        "nombre": nombre,
        "fecha_alta": fecha_alta
    })


def listar_supervisores(solo_activos: bool = False) -> list:
    """
    Retorna supervisores. Si solo_activos=True filtra los dados de baja.
    Cada fila: (id, nombre, fecha_alta, fecha_baja)
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    if solo_activos:
        cursor.execute("""
            SELECT id, nombre, fecha_alta, fecha_baja
            FROM supervisores
            WHERE fecha_baja IS NULL
            ORDER BY nombre
        """)
    else:
        cursor.execute("""
            SELECT id, nombre, fecha_alta, fecha_baja
            FROM supervisores
            ORDER BY fecha_baja IS NULL DESC, nombre
        """)
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def obtener_supervisor(supervisor_id: int) -> tuple | None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, nombre, fecha_alta, fecha_baja FROM supervisores WHERE id = ?",
        (supervisor_id,)
    )
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def actualizar_supervisor(
    supervisor_id: int,
    nombre: str,
    fecha_alta: str | None = None,
    fecha_baja: str | None = None
) -> None:
    """Actualiza nombre, fecha_alta y/o fecha_baja de un supervisor."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE supervisores
        SET nombre = ?, fecha_alta = ?, fecha_baja = ?
        WHERE id = ?
    """, (nombre, fecha_alta, fecha_baja, supervisor_id))
    conexion.commit()
    conexion.close()
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "nombre": nombre,
        "fecha_alta": fecha_alta,
        "fecha_baja": fecha_baja
    })


def dar_de_baja_supervisor(supervisor_id: int, fecha_baja: str) -> None:
    """Marca la fecha de baja sin eliminar el registro."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE supervisores SET fecha_baja = ? WHERE id = ?
    """, (fecha_baja, supervisor_id))
    conexion.commit()
    conexion.close()
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "fecha_baja": fecha_baja
    })


def reactivar_supervisor(supervisor_id: int) -> None:
    """Borra la fecha de baja, reactivando al supervisor."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE supervisores SET fecha_baja = NULL WHERE id = ?
    """, (supervisor_id,))
    conexion.commit()
    conexion.close()
    notificar_cambio("supervisores", "UPDATE", {
        "id": supervisor_id,
        "fecha_baja": None
    })