# =============================================================================
# VESP Organizations - Servicio de feriados
# =============================================================================

import calendar
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from database.gestor_db import gestor_db
from services.cache import cache_global

logger = logging.getLogger(__name__)


def _validar_fecha(fecha: str) -> str:
    try:
        return datetime.strptime(fecha, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Fecha inválida: {fecha}") from exc


@cache_global.auto_cache(ttl=300)
def listar_feriados() -> List[Dict[str, Any]]:
    resultados = gestor_db.ejecutar(
        "SELECT id, fecha, descripcion FROM feriados ORDER BY fecha"
    )
    return [
        {
            "id": r["id"],
            "fecha": r["fecha"],
            "descripcion": r["descripcion"],
        }
        for r in resultados
    ]


def registrar_feriado(fecha: str, descripcion: Optional[str] = None) -> Dict[str, Any]:
    fecha = _validar_fecha(fecha)
    descripcion = (descripcion or "").strip() or None

    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM feriados WHERE fecha = ?",
            (fecha,),
        )
        existente = cursor.fetchone()
        if existente:
            cursor.execute(
                "UPDATE feriados SET descripcion = ? WHERE fecha = ?",
                (descripcion, fecha),
            )
            feriado_id = existente[0]
        else:
            cursor.execute(
                "INSERT INTO feriados (fecha, descripcion) VALUES (?, ?)",
                (fecha, descripcion),
            )
            feriado_id = cursor.lastrowid

    cache_global.invalidar_patron("feriados")
    logger.info("Feriado registrado: %s", fecha)
    return {"id": feriado_id, "fecha": fecha, "descripcion": descripcion}


def eliminar_feriado(fecha: str) -> bool:
    fecha = _validar_fecha(fecha)
    with gestor_db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM feriados WHERE fecha = ?", (fecha,))
        eliminado = cursor.rowcount > 0

    cache_global.invalidar_patron("feriados")
    return eliminado


def es_feriado(fecha: str) -> bool:
    fecha = _validar_fecha(fecha)
    resultado = gestor_db.ejecutar_scalar(
        "SELECT 1 FROM feriados WHERE fecha = ?",
        (fecha,),
    )
    return bool(resultado)


@cache_global.auto_cache(ttl=300)
def obtener_feriados_mes(anio: int, mes: int) -> List[Dict[str, Any]]:
    total_dias = calendar.monthrange(anio, mes)[1]
    fecha_inicio = f"{anio:04d}-{mes:02d}-01"
    fecha_fin = f"{anio:04d}-{mes:02d}-{total_dias:02d}"
    resultados = gestor_db.ejecutar(
        "SELECT id, fecha, descripcion FROM feriados WHERE fecha BETWEEN ? AND ? ORDER BY fecha",
        (fecha_inicio, fecha_fin),
    )
    return [
        {
            "id": r["id"],
            "fecha": r["fecha"],
            "descripcion": r["descripcion"],
        }
        for r in resultados
    ]
