# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de pasadas (turnos)
# =============================================================================

import logging
from typing import List, Optional

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
    validar_id
)
from services.logica_turnos import calcular_turno_y_fecha_operativa

logger = logging.getLogger(__name__)

VENTANA_DUPLICADO_MINUTOS = 5


# =============================================================================
# ALTAS
# =============================================================================

def registrar_turno(
    fecha: str,
    turno: str,  # (se mantiene por compatibilidad, pero ya no se confía)
    objetivo_id: int,
    supervisor_id: int,
    hora: Optional[str] = None
) -> Pasada:
    """
    Registra una nueva pasada.
    """

    try:
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        objetivo_id = validar_id(objetivo_id, "objetivo_id")
        supervisor_id = validar_id(supervisor_id, "supervisor_id")
        hora = validar_hora(hora)

        turno_calculado, fecha_operativa = calcular_turno_y_fecha_operativa(fecha, hora)

        # Verificación de duplicado usando turno real calculado
        if _pasada_ya_existe(fecha_operativa.strftime("%Y-%m-%d"), objetivo_id, supervisor_id, turno_calculado, hora):
            raise TurnoYaRegistrado(fecha, objetivo_id, supervisor_id)

        with gestor_db.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO pasadas
                (fecha, hora, turno, objetivo_id, supervisor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                fecha_operativa.strftime("%Y-%m-%d"),
                hora,
                turno_calculado,
                objetivo_id,
                supervisor_id
            ))

            pasada_id = cursor.lastrowid

        pasada = Pasada(
            id=pasada_id,
            fecha=fecha_operativa.strftime("%Y-%m-%d"),
            hora=hora,
            turno=turno_calculado,
            objetivo_id=objetivo_id,
            supervisor_id=supervisor_id
        )

        invalidar_pasadas()

        notificar_cambio("pasadas", "INSERT", {
            "id": pasada_id
        })

        logger.info(
            f"Pasada registrada ID={pasada_id} "
            f"{fecha_operativa} {hora} {turno_calculado}"
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
    Lista pasadas del día (fecha operativa).
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
    Actualiza hora y recalcula turno correctamente.
    """

    try:
        pasada = obtener_pasada(pasada_id)

        nueva_hora = validar_hora(hora) if hora else pasada.hora

        turno_calculado, fecha_operativa = calcular_turno_y_fecha_operativa(
            pasada.fecha,
            nueva_hora
        )

        with gestor_db.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE pasadas
                SET hora = ?, turno = ?, fecha = ?
                WHERE id = ?
            """, (
                nueva_hora,
                turno_calculado,
                fecha_operativa.strftime("%Y-%m-%d"),
                pasada_id
            ))

        invalidar_pasadas()

        notificar_cambio("pasadas", "UPDATE", {
            "id": pasada_id
        })

        pasada.hora = nueva_hora
        pasada.turno = turno_calculado
        pasada.fecha = fecha_operativa.strftime("%Y-%m-%d")

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
    turno: str,
    hora: Optional[str]
) -> bool:
    """
    Verifica duplicado dentro de ventana de minutos.
    """

    try:
        if not hora:
            return False

        query = """
            SELECT 1
            FROM pasadas
            WHERE fecha = ?
              AND objetivo_id = ?
              AND supervisor_id = ?
              AND turno = ?
              AND hora IS NOT NULL
              AND ABS(
                  (CAST(substr(hora, 1, 2) AS INTEGER) * 60 + CAST(substr(hora, 4, 2) AS INTEGER)) -
                  (CAST(substr(?, 1, 2) AS INTEGER) * 60 + CAST(substr(?, 4, 2) AS INTEGER))
              ) <= ?
            LIMIT 1
        """

        params = (
            fecha,
            objetivo_id,
            supervisor_id,
            turno,
            hora,
            hora,
            VENTANA_DUPLICADO_MINUTOS
        )

        resultado = gestor_db.ejecutar(query, params)

        return bool(resultado)

    except Exception as e:
        logger.error(f"Error verificando duplicado: {e}")
        return False