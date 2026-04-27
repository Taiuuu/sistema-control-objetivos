# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de pasadas (turnos) - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo para la gestión completa del ciclo de vida de pasadas/turnos del sistema.

Proporciona funciones para:
- Registrar nuevas pasadas (turnos)
- Consultar pasadas (individuales o listados)
- Actualizar información de pasadas
- Buscar y filtrar pasadas por fecha, objetivo o supervisor
- Obtener reportes de turnos

Una "pasada" es un registro de turno completado por un supervisor en una fecha específica.

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from database.gestor_db import gestor_db
from services.cache import cache_global, invalidar_pasadas
from services.sincronizacion import notificar_cambio

from .exceptions import (
    TurnoError, TurnoNoEncontrado, TurnoYaRegistrado, 
    DatabaseError, SupervisorInactivo
)
from .types import Pasada, TurnoEnum
from .validators import (
    validar_fecha, validar_hora, validar_turno, 
    validar_id
)

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCIONES DE ALTA (CREATE)
# =============================================================================

def registrar_turno(
    fecha: str,
    turno: str,
    objetivo_id: int,
    supervisor_id: int,
    hora: Optional[str] = None,
    observaciones: Optional[str] = None
) -> Pasada:
    """Registra una nueva pasada/turno en el sistema.
    
    Args:
        fecha: Fecha del turno en formato YYYY-MM-DD.
        turno: Tipo de turno ('Mañana', 'Tarde', 'Noche', 'Completo').
        objetivo_id: ID del objetivo asociado.
        supervisor_id: ID del supervisor que realiza la pasada.
        hora: Hora opcional del registro en formato HH:MM o HH:MM:SS.
        observaciones: Notas adicionales sobre la pasada.
    
    Returns:
        Objeto Pasada con los datos de la pasada creada, incluyendo ID.
    
    Raises:
        ValidationError: Si algún parámetro no cumple validaciones.
        TurnoYaRegistrado: Si ya existe pasada idéntica.
        DatabaseError: Si hay error en la base de datos.
    
    Example:
        >>> pasada = registrar_turno("2026-04-27", "Mañana", 1, 2)
        >>> print(pasada.id)
        105
    """
    try:
        # Validar parámetros
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        turno = validar_turno(turno)
        objetivo_id = validar_id(objetivo_id, "objetivo_id")
        supervisor_id = validar_id(supervisor_id, "supervisor_id")
        hora = validar_hora(hora)
        
        # Verificar que no exista pasada duplicada
        if _pasada_ya_existe(fecha, objetivo_id, supervisor_id):
            logger.warning(f"Intento de registrar pasada duplicada: {fecha} obj={objetivo_id} sup={supervisor_id}")
            raise TurnoYaRegistrado(fecha, objetivo_id, supervisor_id)
        
        # Insertar en base de datos
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pasadas 
                    (fecha, hora, turno, objetivo_id, supervisor_id, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fecha, hora, turno, objetivo_id, supervisor_id, observaciones))
            pasada_id = cursor.lastrowid
        
        # Construir objeto retorno
        pasada = Pasada(
            id=pasada_id,
            fecha=fecha,
            hora=hora,
            turno=turno,
            objetivo_id=objetivo_id,
            supervisor_id=supervisor_id,
            observaciones=observaciones,
            creado_en=datetime.now().isoformat()
        )
        
        # Notificar cambio para sincronización
        notificar_cambio("pasadas", "INSERT", {
            "id": pasada_id,
            "fecha": fecha,
            "hora": hora,
            "turno": turno,
            "objetivo_id": objetivo_id,
            "supervisor_id": supervisor_id,
            "observaciones": observaciones
        })
        
        # Invalidar caché
        invalidar_pasadas()
        
        logger.info(f"Pasada registrada: {fecha} {turno} (ID: {pasada_id})")
        return pasada
        
    except (ValidationError, TurnoError) as e:
        logger.error(f"Error validando pasada: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al registrar pasada: {e}")
        raise DatabaseError("INSERT", str(e))


def registrar_turno_ambos(
    fecha: str,
    turno: str,
    objetivo_id: int,
    supervisor1_id: int,
    supervisor2_id: int,
    hora: Optional[str] = None
) -> Tuple[Pasada, Pasada]:
    """Registra pasada para dos supervisores en una sola transacción.
    
    Útil para registrar un turno compartido entre dos supervisores.
    
    Args:
        fecha: Fecha del turno (YYYY-MM-DD).
        turno: Tipo de turno.
        objetivo_id: ID del objetivo.
        supervisor1_id: ID del primer supervisor.
        supervisor2_id: ID del segundo supervisor.
        hora: Hora opcional del registro.
    
    Returns:
        Tupla con dos objetos Pasada.
    
    Raises:
        ValidationError: Si algún parámetro no cumple validaciones.
        DatabaseError: Si hay error en la base de datos.
    """
    try:
        # Validar parámetros
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        turno = validar_turno(turno)
        objetivo_id = validar_id(objetivo_id, "objetivo_id")
        supervisor1_id = validar_id(supervisor1_id, "supervisor1_id")
        supervisor2_id = validar_id(supervisor2_id, "supervisor2_id")
        hora = validar_hora(hora)
        
        if supervisor1_id == supervisor2_id:
            raise ValidationError("supervisores", "Los supervisores no pueden ser iguales")
        
        # Insertar ambas pasadas en una transacción
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pasadas 
                    (fecha, hora, turno, objetivo_id, supervisor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (fecha, hora, turno, objetivo_id, supervisor1_id))
            pasada1_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO pasadas 
                    (fecha, hora, turno, objetivo_id, supervisor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (fecha, hora, turno, objetivo_id, supervisor2_id))
            pasada2_id = cursor.lastrowid
        
        # Construir objetos retorno
        pasada1 = Pasada(
            id=pasada1_id,
            fecha=fecha,
            hora=hora,
            turno=turno,
            objetivo_id=objetivo_id,
            supervisor_id=supervisor1_id,
            creado_en=datetime.now().isoformat()
        )
        
        pasada2 = Pasada(
            id=pasada2_id,
            fecha=fecha,
            hora=hora,
            turno=turno,
            objetivo_id=objetivo_id,
            supervisor_id=supervisor2_id,
            creado_en=datetime.now().isoformat()
        )
        
        # Notificar cambios
        notificar_cambio("pasadas", "INSERT", {
            "id": pasada1_id,
            "fecha": fecha,
            "turno": turno,
            "objetivo_id": objetivo_id,
            "supervisor_id": supervisor1_id
        })
        notificar_cambio("pasadas", "INSERT", {
            "id": pasada2_id,
            "fecha": fecha,
            "turno": turno,
            "objetivo_id": objetivo_id,
            "supervisor_id": supervisor2_id
        })
        
        invalidar_pasadas()
        
        logger.info(f"Pasadas registradas para ambos supervisores: {fecha} {turno}")
        return pasada1, pasada2
        
    except (ValidationError, TurnoError) as e:
        logger.error(f"Error registrando pasadas ambos: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("INSERT", str(e))


# =============================================================================
# FUNCIONES DE CONSULTA (READ)
# =============================================================================

@cache_global.auto_cache(ttl=30)
def listar_turnos_del_dia(fecha: str) -> List[Pasada]:
    """Lista todos los turnos registrados de un día específico.
    
    Args:
        fecha: Fecha a consultar (YYYY-MM-DD).
    
    Returns:
        Lista de objetos Pasada del día.
        
    Raises:
        ValidationError: Si la fecha no es válida.
        DatabaseError: Si hay error en la consulta.
        
    Note:
        Resultado cacheado por 30 segundos.
    """
    try:
        fecha = validar_fecha(fecha, "fecha", requerida=True)
        
        query = """
            SELECT p.id, p.fecha, p.hora, p.turno, p.objetivo_id, 
                   p.supervisor_id, p.observaciones
            FROM pasadas p
            WHERE p.fecha = ?
            ORDER BY p.hora, p.turno
        """
        
        resultados = gestor_db.ejecutar(query, (fecha,))
        
        pasadas = [
            Pasada(
                id=r['id'],
                fecha=r['fecha'],
                hora=r['hora'],
                turno=r['turno'],
                objetivo_id=r['objetivo_id'],
                supervisor_id=r['supervisor_id'],
                observaciones=r.get('observaciones')
            )
            for r in resultados
        ]
        
        logger.debug(f"Listado de pasadas del día {fecha}: {len(pasadas)} registros")
        return pasadas
        
    except ValidationError as e:
        logger.error(f"Error validando parámetros: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al listar turnos del día: {e}")
        raise DatabaseError("SELECT", str(e))


def obtener_pasada(pasada_id: int) -> Pasada:
    """Obtiene una pasada específica por ID.
    
    Args:
        pasada_id: ID de la pasada a recuperar.
    
    Returns:
        Objeto Pasada.
    
    Raises:
        ValidationError: Si el ID no es válido.
        TurnoNoEncontrado: Si no existe la pasada.
        DatabaseError: Si hay error en la consulta.
    """
    try:
        pasada_id = validar_id(pasada_id)
        
        resultado = gestor_db.ejecutar(
            """SELECT id, fecha, hora, turno, objetivo_id, supervisor_id, observaciones 
               FROM pasadas WHERE id = ?""",
            (pasada_id,)
        )
        
        if not resultado:
            logger.warning(f"Pasada no encontrada: ID {pasada_id}")
            raise TurnoNoEncontrado(pasada_id)
        
        r = resultado[0]
        pasada = Pasada(
            id=r['id'],
            fecha=r['fecha'],
            hora=r['hora'],
            turno=r['turno'],
            objetivo_id=r['objetivo_id'],
            supervisor_id=r['supervisor_id'],
            observaciones=r.get('observaciones')
        )
        
        logger.debug(f"Pasada obtenida: ID {pasada_id}")
        return pasada
        
    except (ValidationError, TurnoError) as e:
        logger.error(f"Error obteniendo pasada: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("SELECT", str(e))


def listar_pasadas_por_objetivo(objetivo_id: int, fecha_desde: Optional[str] = None) -> List[Pasada]:
    """Lista todas las pasadas de un objetivo.
    
    Args:
        objetivo_id: ID del objetivo.
        fecha_desde: Fecha inicial opcional (YYYY-MM-DD).
    
    Returns:
        Lista de pasadas del objetivo.
    """
    try:
        objetivo_id = validar_id(objetivo_id)
        if fecha_desde:
            fecha_desde = validar_fecha(fecha_desde, "fecha_desde", requerida=False)
        
        if fecha_desde:
            query = """
                SELECT id, fecha, hora, turno, objetivo_id, supervisor_id, observaciones
                FROM pasadas
                WHERE objetivo_id = ? AND fecha >= ?
                ORDER BY fecha DESC, hora DESC
            """
            resultados = gestor_db.ejecutar(query, (objetivo_id, fecha_desde))
        else:
            query = """
                SELECT id, fecha, hora, turno, objetivo_id, supervisor_id, observaciones
                FROM pasadas
                WHERE objetivo_id = ?
                ORDER BY fecha DESC, hora DESC
            """
            resultados = gestor_db.ejecutar(query, (objetivo_id,))
        
        pasadas = [
            Pasada(
                id=r['id'],
                fecha=r['fecha'],
                hora=r['hora'],
                turno=r['turno'],
                objetivo_id=r['objetivo_id'],
                supervisor_id=r['supervisor_id'],
                observaciones=r.get('observaciones')
            )
            for r in resultados
        ]
        
        logger.info(f"Listado de pasadas por objetivo {objetivo_id}: {len(pasadas)} registros")
        return pasadas
        
    except Exception as e:
        logger.error(f"Error listando pasadas por objetivo: {e}")
        raise DatabaseError("SELECT", str(e))


def listar_pasadas_por_supervisor(supervisor_id: int, fecha_desde: Optional[str] = None) -> List[Pasada]:
    """Lista todas las pasadas de un supervisor.
    
    Args:
        supervisor_id: ID del supervisor.
        fecha_desde: Fecha inicial opcional (YYYY-MM-DD).
    
    Returns:
        Lista de pasadas del supervisor.
    """
    try:
        supervisor_id = validar_id(supervisor_id)
        if fecha_desde:
            fecha_desde = validar_fecha(fecha_desde, "fecha_desde", requerida=False)
        
        if fecha_desde:
            query = """
                SELECT id, fecha, hora, turno, objetivo_id, supervisor_id, observaciones
                FROM pasadas
                WHERE supervisor_id = ? AND fecha >= ?
                ORDER BY fecha DESC, hora DESC
            """
            resultados = gestor_db.ejecutar(query, (supervisor_id, fecha_desde))
        else:
            query = """
                SELECT id, fecha, hora, turno, objetivo_id, supervisor_id, observaciones
                FROM pasadas
                WHERE supervisor_id = ?
                ORDER BY fecha DESC, hora DESC
            """
            resultados = gestor_db.ejecutar(query, (supervisor_id,))
        
        pasadas = [
            Pasada(
                id=r['id'],
                fecha=r['fecha'],
                hora=r['hora'],
                turno=r['turno'],
                objetivo_id=r['objetivo_id'],
                supervisor_id=r['supervisor_id'],
                observaciones=r.get('observaciones')
            )
            for r in resultados
        ]
        
        logger.info(f"Listado de pasadas por supervisor {supervisor_id}: {len(pasadas)} registros")
        return pasadas
        
    except Exception as e:
        logger.error(f"Error listando pasadas por supervisor: {e}")
        raise DatabaseError("SELECT", str(e))


# =============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# =============================================================================

def actualizar_pasada(
    pasada_id: int,
    hora: Optional[str] = None,
    turno: Optional[str] = None,
    observaciones: Optional[str] = None
) -> Pasada:
    """Actualiza información de una pasada.
    
    Args:
        pasada_id: ID de la pasada a actualizar.
        hora: Nueva hora (HH:MM o HH:MM:SS).
        turno: Nuevo tipo de turno.
        observaciones: Nuevas observaciones.
    
    Returns:
        Objeto Pasada actualizado.
    """
    try:
        pasada_id = validar_id(pasada_id)
        
        # Obtener pasada actual
        pasada = obtener_pasada(pasada_id)
        
        # Validar parámetros si se proporcionan
        if hora is not None:
            hora = validar_hora(hora)
        else:
            hora = pasada.hora
        
        if turno is not None:
            turno = validar_turno(turno)
        else:
            turno = pasada.turno
        
        if observaciones is None:
            observaciones = pasada.observaciones
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pasadas
                SET hora = ?, turno = ?, observaciones = ?
                WHERE id = ?
            """, (hora, turno, observaciones, pasada_id))
        
        # Actualizar objeto
        pasada.hora = hora
        pasada.turno = turno
        pasada.observaciones = observaciones
        pasada.actualizado_en = datetime.now().isoformat()
        
        # Notificar cambio
        notificar_cambio("pasadas", "UPDATE", {
            "id": pasada_id,
            "hora": hora,
            "turno": turno,
            "observaciones": observaciones
        })
        
        invalidar_pasadas()
        
        logger.info(f"Pasada actualizada: ID {pasada_id}")
        return pasada
        
    except (ValidationError, TurnoError) as e:
        logger.error(f"Error actualizando pasada: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("UPDATE", str(e))


# =============================================================================
# FUNCIONES AUXILIARES PRIVADAS
# =============================================================================

def _pasada_ya_existe(fecha: str, objetivo_id: int, supervisor_id: int) -> bool:
    """Verifica si ya existe una pasada idéntica (uso interno).
    
    Args:
        fecha: Fecha de la pasada.
        objetivo_id: ID del objetivo.
        supervisor_id: ID del supervisor.
    
    Returns:
        True si existe, False en caso contrario.
    """
    try:
        resultado = gestor_db.ejecutar(
            """SELECT id FROM pasadas 
               WHERE fecha = ? AND objetivo_id = ? AND supervisor_id = ?""",
            (fecha, objetivo_id, supervisor_id)
        )
        return bool(resultado)
    except Exception:
        return False