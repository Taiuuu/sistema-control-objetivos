# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de equipos de turno - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo para la gestión de equipos de turno del sistema.

Un "equipo de turno" es la asignación de supervisores (2 o 3) a un turno
específico en una fecha determinada.

Proporciona funciones para:
- Crear/actualizar equipos de turno
- Consultar equipos por fecha o turno
- Buscar supervisores disponibles
- Validar integridad de equipos

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from database.gestor_db import gestor_db
from services.cache import cache_global, invalidar_supervisores
from services.sincronizacion import notificar_cambio

from .exceptions import (
    EquipoError, EquipoNoEncontrado, DatabaseError, ValidationError
)
from .types import Equipo, TurnoEnum
from .validators import (
    validar_fecha, validar_turno, validar_id
)

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCIONES DE ALTA (CREATE) / ACTUALIZACIÓN (UPDATE)
# =============================================================================

def guardar_equipo_turno(
    fecha: str,
    turno: str,
    supervisor1_id: int,
    supervisor2_id: int,
    supervisor3_id: Optional[int] = None
) -> Equipo:
    """Registra o actualiza los supervisores asignados a un turno.
    
    Si ya existe equipo para esa fecha y turno, lo reemplaza (UPSERT).
    
    Args:
        fecha: Fecha del turno (YYYY-MM-DD).
        turno: Tipo de turno ('Mañana', 'Tarde', 'Noche', 'Completo').
        supervisor1_id: ID del primer supervisor (requerido).
        supervisor2_id: ID del segundo supervisor (requerido).
        supervisor3_id: ID del tercer supervisor (opcional).
    
    Returns:
        Objeto Equipo con los datos del equipo creado/actualizado.
    
    Raises:
        ValidationError: Si los parámetros no son válidos.
        DatabaseError: Si hay error en la base de datos.
    
    Example:
        >>> equipo = guardar_equipo_turno("2026-04-27", "Mañana", 1, 2, 3)
        >>> print(equipo.id)
        42
    """
    try:
        # Validar parámetros
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        turno = validar_turno(turno)
        supervisor1_id = validar_id(supervisor1_id, "supervisor1_id")
        supervisor2_id = validar_id(supervisor2_id, "supervisor2_id")
        
        if supervisor3_id is not None:
            supervisor3_id = validar_id(supervisor3_id, "supervisor3_id")
        
        # Validar que supervisores sean diferentes
        if supervisor1_id == supervisor2_id:
            raise ValidationError("supervisores", "El supervisor 1 y 2 no pueden ser iguales")
        
        if supervisor3_id and (supervisor3_id == supervisor1_id or supervisor3_id == supervisor2_id):
            raise ValidationError("supervisor3_id", "El supervisor 3 no puede repetirse")
        
        # Intentar UPSERT (eliminar si existe, luego insertar)
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            
            # Eliminar equipo existente para esta fecha y turno
            cursor.execute(
                "DELETE FROM equipos WHERE fecha = ? AND turno = ?",
                (fecha, turno)
            )
            
            # Insertar nuevo equipo
            cursor.execute("""
                INSERT INTO equipos 
                    (fecha, turno, supervisor1_id, supervisor2_id, supervisor3_id)
                VALUES (?, ?, ?, ?, ?)
            """, (fecha, turno, supervisor1_id, supervisor2_id, supervisor3_id))
            
            equipo_id = cursor.lastrowid
        
        # Construir objeto retorno
        equipo = Equipo(
            id=equipo_id,
            nombre=f"Turno {turno} - {fecha}",
            descripcion=f"Supervisores: {supervisor1_id}, {supervisor2_id}" +
                       (f", {supervisor3_id}" if supervisor3_id else ""),
            estado="activo",
            creado_en=datetime.now().isoformat()
        )
        
        # Notificar cambio para sincronización
        notificar_cambio("equipos", "INSERT", {
            "id": equipo_id,
            "fecha": fecha,
            "turno": turno,
            "supervisor1_id": supervisor1_id,
            "supervisor2_id": supervisor2_id,
            "supervisor3_id": supervisor3_id
        })
        
        # Invalidar caché
        invalidar_supervisores()
        
        logger.info(f"Equipo turno guardado: {fecha} {turno} (ID: {equipo_id})")
        return equipo
        
    except (ValidationError, EquipoError) as e:
        logger.error(f"Error validando equipo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al guardar equipo: {e}")
        raise DatabaseError("INSERT", str(e))


# =============================================================================
# FUNCIONES DE CONSULTA (READ)
# =============================================================================

@cache_global.auto_cache(ttl=60)
def obtener_equipos_por_fecha(fecha: str) -> List[Tuple[str, int, int, Optional[int]]]:
    """Obtiene todos los equipos de una fecha específica.
    
    Args:
        fecha: Fecha a consultar (YYYY-MM-DD).
    
    Returns:
        Lista de tuplas (turno, sup1_id, sup2_id, sup3_id).
        
    Raises:
        ValidationError: Si la fecha no es válida.
        DatabaseError: Si hay error en la consulta.
    """
    try:
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        
        query = """
            SELECT turno, supervisor1_id, supervisor2_id, supervisor3_id
            FROM equipos
            WHERE fecha = ?
            ORDER BY turno
        """
        
        resultados = gestor_db.ejecutar(query, (fecha,))
        
        equipos = [
            (r['turno'], r['supervisor1_id'], r['supervisor2_id'], r['supervisor3_id'])
            for r in resultados
        ]
        
        logger.debug(f"Equipos obtenidos para {fecha}: {len(equipos)} turnos")
        return equipos
        
    except ValidationError as e:
        logger.error(f"Error validando fecha: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener equipos por fecha: {e}")
        raise DatabaseError("SELECT", str(e))


def obtener_equipo_por_fecha_turno(fecha: str, turno: str) -> Optional[Tuple[int, int, int, Optional[int]]]:
    """Obtiene el equipo asignado a un turno específico.
    
    Args:
        fecha: Fecha (YYYY-MM-DD).
        turno: Tipo de turno.
    
    Returns:
        Tupla (id_equipo, sup1_id, sup2_id, sup3_id) o None si no existe.
    """
    try:
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        turno = validar_turno(turno)
        
        resultado = gestor_db.ejecutar(
            """SELECT id, supervisor1_id, supervisor2_id, supervisor3_id
               FROM equipos 
               WHERE fecha = ? AND turno = ?""",
            (fecha, turno)
        )
        
        if not resultado:
            return None
        
        r = resultado[0]
        return (r['id'], r['supervisor1_id'], r['supervisor2_id'], r['supervisor3_id'])
        
    except ValidationError as e:
        logger.error(f"Error validando parámetros: {e}")
        raise
    except Exception as e:
        logger.error(f"Error obtener equipo por fecha-turno: {e}")
        raise DatabaseError("SELECT", str(e))


def obtener_turnos_del_supervisor(supervisor_id: int, fecha: str) -> List[str]:
    """Obtiene todos los turnos asignados a un supervisor en una fecha.
    
    Args:
        supervisor_id: ID del supervisor.
        fecha: Fecha a consultar (YYYY-MM-DD).
    
    Returns:
        Lista de turnos asignados al supervisor.
    """
    try:
        supervisor_id = validar_id(supervisor_id)
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        
        query = """
            SELECT DISTINCT turno
            FROM equipos
            WHERE fecha = ? AND (
                supervisor1_id = ? OR 
                supervisor2_id = ? OR 
                supervisor3_id = ?
            )
            ORDER BY turno
        """
        
        resultados = gestor_db.ejecutar(
            query,
            (fecha, supervisor_id, supervisor_id, supervisor_id)
        )
        
        turnos = [r['turno'] for r in resultados]
        
        logger.debug(f"Turnos del supervisor {supervisor_id} en {fecha}: {len(turnos)}")
        return turnos
        
    except ValidationError as e:
        logger.error(f"Error validando parámetros: {e}")
        raise
    except Exception as e:
        logger.error(f"Error obtener turnos del supervisor: {e}")
        raise DatabaseError("SELECT", str(e))


def listar_equipos(fecha_desde: Optional[str] = None, limite: int = 100) -> List[Equipo]:
    """Lista equipos del sistema con opciones de filtrado.
    
    Args:
        fecha_desde: Mostrar solo equipos desde esta fecha.
        limite: Número máximo de registros.
    
    Returns:
        Lista de objetos Equipo.
    """
    try:
        if fecha_desde:
            fecha_desde = validar_fecha(fecha_desde, "fecha_desde", requerida=False)
        
        if fecha_desde:
            query = """
                SELECT id, fecha, turno, supervisor1_id, supervisor2_id, supervisor3_id
                FROM equipos
                WHERE fecha >= ?
                ORDER BY fecha DESC, turno
                LIMIT ?
            """
            resultados = gestor_db.ejecutar(query, (fecha_desde, limite))
        else:
            query = """
                SELECT id, fecha, turno, supervisor1_id, supervisor2_id, supervisor3_id
                FROM equipos
                ORDER BY fecha DESC, turno
                LIMIT ?
            """
            resultados = gestor_db.ejecutar(query, (limite,))
        
        equipos = [
            Equipo(
                id=r['id'],
                nombre=f"Turno {r['turno']} - {r['fecha']}",
                descripcion=f"Supervisores: {r['supervisor1_id']}, {r['supervisor2_id']}" +
                           (f", {r['supervisor3_id']}" if r['supervisor3_id'] else ""),
                estado="activo"
            )
            for r in resultados
        ]
        
        logger.info(f"Listado de equipos: {len(equipos)} registros")
        return equipos
        
    except Exception as e:
        logger.error(f"Error listando equipos: {e}")
        raise DatabaseError("SELECT", str(e))


# =============================================================================
# FUNCIONES AUXILIARES PRIVADAS
# =============================================================================

def _validar_supervisor_disponible(supervisor_id: int, fecha: str, turno: str) -> bool:
    """Verifica si un supervisor está disponible para un turno (uso interno).
    
    Args:
        supervisor_id: ID del supervisor.
        fecha: Fecha (YYYY-MM-DD).
        turno: Tipo de turno.
    
    Returns:
        True si está disponible, False si ya está asignado.
    """
    try:
        turnos_asignados = obtener_turnos_del_supervisor(supervisor_id, fecha)
        return turno not in turnos_asignados
    except Exception:
        return False