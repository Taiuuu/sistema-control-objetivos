# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de pasadas (turnos)
# Compatible con estructura real de tu base de datos
# =============================================================================

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from database.gestor_db import gestor_db
from services.cache import cache_global, invalidar_pasadas
from services.sincronizacion import notificar_cambio

from .exceptions import (
    TurnoError,
    TurnoNoEncontrado,
    TurnoYaRegistrado,
    DatabaseError,
    ValidationError
)

from .types import Pasada
from .validators import (
    validar_fecha,
    validar_hora,
    validar_turno,
    validar_id
)

logger = logging.getLogger(__name__)


# =============================================================================
# ALTAS
# =============================================================================

def registrar_turno(
    fecha: str,
    turno: str,
    objetivo_id: int,
    supervisor_id: int,
    hora: Optional[str] = None
) -> Pasada:
    """
    Registra una nueva pasada.
    """

    try:
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        turno = validar_turno(turno)          # diurno / nocturno
        objetivo_id = validar_id(objetivo_id, "objetivo_id")
        supervisor_id = validar_id(supervisor_id, "supervisor_id")
        hora = validar_hora(hora)            # HH:mm

        if _pasada_ya_existe(fecha, objetivo_id, supervisor_id, turno):
            raise TurnoYaRegistrado(
                f"Ya existe pasada para fecha={fecha}, objetivo={objetivo_id}, supervisor={supervisor_id}"
            )

        with gestor_db.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO pasadas
                (fecha, hora, turno, objetivo_id, supervisor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                fecha,
                hora,
                turno,
                objetivo_id,
                supervisor_id
            ))

            pasada_id = cursor.lastrowid

        pasada = Pasada(
            id=pasada_id,
            fecha=fecha,
            hora=hora,
            turno=turno,
            objetivo_id=objetivo_id,
            supervisor_id=supervisor_id
        )

        invalidar_pasadas()

        notificar_cambio("pasadas", "INSERT", {
            "id": pasada_id
        })

        logger.info(
            f"Pasada registrada ID={pasada_id} "
            f"{fecha} {hora} {turno}"
        )

        return pasada

    except (ValidationError, TurnoError):
        raise

    except Exception as e:
        logger.error(f"Error inesperado al registrar pasada: {e}")
        raise DatabaseError("INSERT", str(e))


# =============================================================================
# CONSULTAS
# =============================================================================

@cache_global.auto_cache(ttl=30)
def listar_turnos_del_dia(fecha: str) -> List[Pasada]:
    """
    Lista pasadas del día.
    """

    try:
        fecha = validar_fecha(fecha, "fecha", requerida=True)

        resultados = gestor_db.ejecutar("""
            SELECT id, fecha, hora, turno, objetivo_id, supervisor_id
            FROM pasadas
            WHERE fecha = ?
            ORDER BY hora ASC
        """, (fecha,))

        return [
            Pasada(
                id=r["id"],
                fecha=r["fecha"],
                hora=r["hora"],
                turno=r["turno"],
                objetivo_id=r["objetivo_id"],
                supervisor_id=r["supervisor_id"]
            )
            for r in resultados
        ]

    except Exception as e:
        logger.error(f"Error listando turnos: {e}")
        raise DatabaseError("SELECT", str(e))


def obtener_pasada(pasada_id: int) -> Pasada:
    """
    Obtiene una pasada por ID.
    """

    try:
        pasada_id = validar_id(pasada_id)

        resultado = gestor_db.ejecutar("""
            SELECT id, fecha, hora, turno, objetivo_id, supervisor_id
            FROM pasadas
            WHERE id = ?
        """, (pasada_id,))

        if not resultado:
            raise TurnoNoEncontrado(f"No existe pasada ID={pasada_id}")

        r = resultado[0]

        return Pasada(
            id=r["id"],
            fecha=r["fecha"],
            hora=r["hora"],
            turno=r["turno"],
            objetivo_id=r["objetivo_id"],
            supervisor_id=r["supervisor_id"]
        )

    except (ValidationError, TurnoError):
        raise

    except Exception as e:
        logger.error(f"Error obteniendo pasada: {e}")
        raise DatabaseError("SELECT", str(e))


def listar_pasadas_por_objetivo(objetivo_id: int) -> List[Pasada]:
    """
    Lista pasadas de un objetivo.
    """

    try:
        objetivo_id = validar_id(objetivo_id)

        resultados = gestor_db.ejecutar("""
            SELECT id, fecha, hora, turno, objetivo_id, supervisor_id
            FROM pasadas
            WHERE objetivo_id = ?
            ORDER BY fecha DESC, hora DESC
        """, (objetivo_id,))

        return [
            Pasada(
                id=r["id"],
                fecha=r["fecha"],
                hora=r["hora"],
                turno=r["turno"],
                objetivo_id=r["objetivo_id"],
                supervisor_id=r["supervisor_id"]
            )
            for r in resultados
        ]

    except Exception as e:
        logger.error(f"Error listando por objetivo: {e}")
        raise DatabaseError("SELECT", str(e))


def listar_pasadas_por_supervisor(supervisor_id: int) -> List[Pasada]:
    """
    Lista pasadas de un supervisor.
    """

    try:
        supervisor_id = validar_id(supervisor_id)

        resultados = gestor_db.ejecutar("""
            SELECT id, fecha, hora, turno, objetivo_id, supervisor_id
            FROM pasadas
            WHERE supervisor_id = ?
            ORDER BY fecha DESC, hora DESC
        """, (supervisor_id,))

        return [
            Pasada(
                id=r["id"],
                fecha=r["fecha"],
                hora=r["hora"],
                turno=r["turno"],
                objetivo_id=r["objetivo_id"],
                supervisor_id=r["supervisor_id"]
            )
            for r in resultados
        ]

    except Exception as e:
        logger.error(f"Error listando por supervisor: {e}")
        raise DatabaseError("SELECT", str(e))


# =============================================================================
# ACTUALIZACIÓN
# =============================================================================

def actualizar_pasada(
    pasada_id: int,
    hora: Optional[str] = None,
    turno: Optional[str] = None
) -> Pasada:
    """
    Actualiza hora y/o turno.
    """

    try:
        pasada = obtener_pasada(pasada_id)

        nueva_hora = validar_hora(hora) if hora else pasada.hora
        nuevo_turno = validar_turno(turno) if turno else pasada.turno

        with gestor_db.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE pasadas
                SET hora = ?, turno = ?
                WHERE id = ?
            """, (
                nueva_hora,
                nuevo_turno,
                pasada_id
            ))

        invalidar_pasadas()

        notificar_cambio("pasadas", "UPDATE", {
            "id": pasada_id
        })

        pasada.hora = nueva_hora
        pasada.turno = nuevo_turno

        logger.info(f"Pasada actualizada ID={pasada_id}")

        return pasada

    except Exception as e:
        logger.error(f"Error actualizando pasada: {e}")
        raise DatabaseError("UPDATE", str(e))


# =============================================================================
# AUXILIARES
# =============================================================================

def _pasada_ya_existe(
    fecha: str,
    objetivo_id: int,
    supervisor_id: int,
    turno: str
) -> bool:
    """
    Verifica duplicado.
    """

    try:
        resultado = gestor_db.ejecutar("""
            SELECT id
            FROM pasadas
            WHERE fecha = ?
            AND objetivo_id = ?
            AND supervisor_id = ?
            AND turno = ?
        """, (
            fecha,
            objetivo_id,
            supervisor_id,
            turno
        ))

        return bool(resultado)

    except Exception:
        return False