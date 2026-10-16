"""Operaciones masivas que deben protegerse con backup y transacción."""

import calendar
import logging
import sqlite3
from datetime import date

from services.backup import crear_backup

logger = logging.getLogger("vesp.operaciones")


def obtener_vista_previa_borrado_mes(
    conexion: sqlite3.Connection, año: int, mes: int
) -> dict:
    """Calcula cantidad y rango de fechas sin modificar registros."""
    primero = date(año, mes, 1).isoformat()
    ultimo = date(año, mes, calendar.monthrange(año, mes)[1]).isoformat()
    cantidad, minimo, maximo = conexion.execute(
        "SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM pasadas "
        "WHERE fecha >= ? AND fecha <= ?",
        (primero, ultimo),
    ).fetchone()
    return {
        "cantidad": cantidad,
        "fecha_desde": minimo,
        "fecha_hasta": maximo,
        "mes": f"{mes:02d}-{año:04d}",
    }


def eliminar_pasadas_mes(
    conexion: sqlite3.Connection,
    año: int,
    mes: int,
    confirmacion: str,
) -> int:
    """Exige confirmación literal, backup verificado y un único commit."""
    vista = obtener_vista_previa_borrado_mes(conexion, año, mes)
    if confirmacion != vista["mes"]:
        raise ValueError(f"Para confirmar, escribí exactamente {vista['mes']}.")
    if not vista["cantidad"]:
        return 0
    crear_backup("pre_borrado_mes", conexion_origen=conexion)
    primero = date(año, mes, 1).isoformat()
    ultimo = date(año, mes, calendar.monthrange(año, mes)[1]).isoformat()
    try:
        conexion.execute("BEGIN")
        cursor = conexion.execute(
            "DELETE FROM pasadas WHERE fecha >= ? AND fecha <= ?",
            (primero, ultimo),
        )
        eliminadas = cursor.rowcount
        conexion.commit()
        logger.info(
            "Borrado mensual confirmado mes=%s filas=%s rango=%s..%s",
            vista["mes"], eliminadas, vista["fecha_desde"], vista["fecha_hasta"],
        )
        return eliminadas
    except Exception:
        conexion.rollback()
        logger.exception("Falló el borrado mensual %s; rollback realizado", vista["mes"])
        raise
