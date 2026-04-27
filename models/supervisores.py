# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de supervisores - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo para la gestión completa del ciclo de vida de supervisores del sistema.

Proporciona funciones para:
- Registrar nuevos supervisores
- Consultar supervisores (individuales o listados)
- Actualizar información de supervisores
- Dar de baja y reactivar supervisores
- Búsqueda y filtrado avanzado

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
from datetime import datetime, date
from typing import List, Optional

from database.gestor_db import gestor_db
from services.cache import cache_global, invalidar_supervisores
from services.sincronizacion import notificar_cambio

from .exceptions import (
    SupervisorError, SupervisorNoEncontrado, SupervisorYaExiste,
    SupervisorInactivo, DatabaseError
)
from .types import Supervisor, EstadoSupervisor
from .validators import validar_nombre, validar_fecha, validar_id

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCIONES DE ALTA (CREATE)
# =============================================================================

def agregar_supervisor(
    nombre: str,
    fecha_alta: Optional[str] = None
) -> Supervisor:
    """Registra un nuevo supervisor en el sistema.
    
    Args:
        nombre: Nombre completo del supervisor (3-255 caracteres).
        fecha_alta: Fecha de alta en formato YYYY-MM-DD. 
                   Si no se proporciona, usa la fecha actual.
    
    Returns:
        Objeto Supervisor con los datos del supervisor creado, incluyendo ID.
    
    Raises:
        ValidationError: Si algún parámetro no cumple validaciones.
        SupervisorYaExiste: Si ya existe un supervisor con ese nombre.
        DatabaseError: Si hay error en la base de datos.
    
    Example:
        >>> sup = agregar_supervisor("Juan García")
        >>> print(sup.id)
        5
    """
    try:
        # Validar parámetros
        nombre = validar_nombre(nombre)
        
        if fecha_alta is None:
            fecha_alta = date.today().isoformat()
        else:
            fecha_alta = validar_fecha(fecha_alta, "fecha_alta", requerida=True)
        
        # Verificar que no exista supervisor con el mismo nombre
        existente = _buscar_supervisor_por_nombre(nombre)
        if existente:
            logger.warning(f"Intento de crear supervisor duplicado: {nombre}")
            raise SupervisorYaExiste(nombre)
        
        # Insertar en base de datos
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO supervisores (nombre, fecha_alta)
                VALUES (?, ?)
            """, (nombre, fecha_alta))
            supervisor_id = cursor.lastrowid
        
        # Construir objeto retorno
        supervisor = Supervisor(
            id=supervisor_id,
            nombre=nombre,
            fecha_alta=fecha_alta,
            creado_en=datetime.now().isoformat()
        )
        
        # Notificar cambio para sincronización
        notificar_cambio("supervisores", "INSERT", {
            "id": supervisor_id,
            "nombre": nombre,
            "fecha_alta": fecha_alta
        })
        
        # Invalidar caché
        invalidar_supervisores()
        
        logger.info(f"Supervisor creado: {nombre} (ID: {supervisor_id})")
        return supervisor
        
    except (ValidationError, SupervisorError) as e:
        logger.error(f"Error validando supervisor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear supervisor: {e}")
        raise DatabaseError("INSERT", str(e))


# =============================================================================
# FUNCIONES DE CONSULTA (READ)
# =============================================================================

@cache_global.auto_cache(ttl=60)
def listar_supervisores(
    solo_activos: bool = False,
    orden: str = "nombre"
) -> List[Supervisor]:
    """Retorna todos los supervisores del sistema.
    
    Args:
        solo_activos: Si True, solo retorna supervisores sin fecha de baja.
        orden: Campo para ordenar ('nombre', 'fecha_alta', 'fecha_baja').
    
    Returns:
        Lista de objetos Supervisor.
        
    Raises:
        DatabaseError: Si hay error en la consulta.
        
    Note:
        Resultado cacheado por 60 segundos para optimizar consultas frecuentes.
    """
    try:
        campos_validos = {'nombre', 'fecha_alta', 'fecha_baja'}
        if orden not in campos_validos:
            orden = 'nombre'
        
        if solo_activos:
            query = f"""
                SELECT id, nombre, fecha_alta, fecha_baja
                FROM supervisores
                WHERE fecha_baja IS NULL
                ORDER BY {orden}
            """
        else:
            query = f"""
                SELECT id, nombre, fecha_alta, fecha_baja
                FROM supervisores
                ORDER BY CASE WHEN fecha_baja IS NULL THEN 0 ELSE 1 END,
                         {orden}
            """
        
        resultados = gestor_db.ejecutar(query)
        
        supervisores = [
            Supervisor(
                id=r['id'],
                nombre=r['nombre'],
                fecha_alta=r['fecha_alta'],
                fecha_baja=r['fecha_baja']
            )
            for r in resultados
        ]
        
        logger.debug(f"Listado de supervisores: {len(supervisores)} registros")
        return supervisores
        
    except Exception as e:
        logger.error(f"Error al listar supervisores: {e}")
        raise DatabaseError("SELECT", str(e))


def obtener_supervisor(supervisor_id: int) -> Supervisor:
    """Obtiene un supervisor específico por ID.
    
    Args:
        supervisor_id: ID del supervisor a recuperar.
    
    Returns:
        Objeto Supervisor con los datos solicitados.
    
    Raises:
        ValidationError: Si el ID no es válido.
        SupervisorNoEncontrado: Si no existe el supervisor.
        DatabaseError: Si hay error en la consulta.
    """
    try:
        supervisor_id = validar_id(supervisor_id)
        
        resultado = gestor_db.ejecutar(
            """SELECT id, nombre, fecha_alta, fecha_baja 
               FROM supervisores WHERE id = ?""",
            (supervisor_id,)
        )
        
        if not resultado:
            logger.warning(f"Supervisor no encontrado: ID {supervisor_id}")
            raise SupervisorNoEncontrado(supervisor_id)
        
        r = resultado[0]
        supervisor = Supervisor(
            id=r['id'],
            nombre=r['nombre'],
            fecha_alta=r['fecha_alta'],
            fecha_baja=r['fecha_baja']
        )
        
        logger.debug(f"Supervisor obtenido: {supervisor.nombre}")
        return supervisor
        
    except (ValidationError, SupervisorError) as e:
        logger.error(f"Error obteniendo supervisor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("SELECT", str(e))


def buscar_supervisores(texto: str) -> List[Supervisor]:
    """Busca supervisores por nombre (búsqueda parcial).
    
    Args:
        texto: Texto a buscar en el nombre de supervisores.
    
    Returns:
        Lista de supervisores que coinciden con la búsqueda.
    """
    try:
        texto = validar_nombre(texto, "búsqueda")
        
        resultados = gestor_db.ejecutar(
            """SELECT id, nombre, fecha_alta, fecha_baja 
               FROM supervisores 
               WHERE nombre LIKE ? 
               ORDER BY nombre""",
            (f"%{texto}%",)
        )
        
        supervisores = [
            Supervisor(
                id=r['id'],
                nombre=r['nombre'],
                fecha_alta=r['fecha_alta'],
                fecha_baja=r['fecha_baja']
            )
            for r in resultados
        ]
        
        logger.info(f"Búsqueda de supervisores: '{texto}' - {len(supervisores)} resultados")
        return supervisores
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise DatabaseError("SELECT", str(e))


# =============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# =============================================================================

def actualizar_supervisor(
    supervisor_id: int,
    nombre: str,
    fecha_alta: Optional[str] = None,
    fecha_baja: Optional[str] = None
) -> Supervisor:
    """Actualiza un supervisor existente.
    
    Args:
        supervisor_id: ID del supervisor a actualizar.
        nombre: Nuevo nombre (3-255 caracteres).
        fecha_alta: Nueva fecha de alta en formato YYYY-MM-DD.
        fecha_baja: Nueva fecha de baja en formato YYYY-MM-DD o None.
    
    Returns:
        Objeto Supervisor con los datos actualizados.
    
    Raises:
        ValidationError: Si algún parámetro no cumple validaciones.
        SupervisorNoEncontrado: Si no existe el supervisor.
        DatabaseError: Si hay error en la base de datos.
    """
    try:
        # Validar parámetros
        supervisor_id = validar_id(supervisor_id)
        nombre = validar_nombre(nombre)
        fecha_alta = validar_fecha(fecha_alta, "fecha_alta", requerida=False)
        fecha_baja = validar_fecha(fecha_baja, "fecha_baja", requerida=False)
        
        # Verificar que existe el supervisor
        supervisor_actual = obtener_supervisor(supervisor_id)
        
        # Usar valores actuales si no se proporcionan
        if fecha_alta is None:
            fecha_alta = supervisor_actual.fecha_alta
        if fecha_baja is None:
            fecha_baja = supervisor_actual.fecha_baja
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE supervisores
                SET nombre = ?, fecha_alta = ?, fecha_baja = ?
                WHERE id = ?
            """, (nombre, fecha_alta, fecha_baja, supervisor_id))
        
        # Construir objeto retorno
        supervisor = Supervisor(
            id=supervisor_id,
            nombre=nombre,
            fecha_alta=fecha_alta,
            fecha_baja=fecha_baja,
            actualizado_en=datetime.now().isoformat()
        )
        
        # Notificar cambio
        notificar_cambio("supervisores", "UPDATE", {
            "id": supervisor_id,
            "nombre": nombre,
            "fecha_alta": fecha_alta,
            "fecha_baja": fecha_baja
        })
        
        invalidar_supervisores()
        
        logger.info(f"Supervisor actualizado: {nombre} (ID: {supervisor_id})")
        return supervisor
        
    except (ValidationError, SupervisorError) as e:
        logger.error(f"Error actualizando supervisor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("UPDATE", str(e))


# =============================================================================
# FUNCIONES DE BAJA Y REACTIVACIÓN
# =============================================================================

def dar_de_baja_supervisor(
    supervisor_id: int,
    fecha_baja: Optional[str] = None
) -> Supervisor:
    """Marca un supervisor como inactivo (soft delete).
    
    Args:
        supervisor_id: ID del supervisor a dar de baja.
        fecha_baja: Fecha de baja. Si no se proporciona, usa fecha actual.
    
    Returns:
        Objeto Supervisor actualizado con fecha de baja.
    
    Raises:
        ValidationError: Si los parámetros no son válidos.
        SupervisorNoEncontrado: Si no existe el supervisor.
        DatabaseError: Si hay error en la base de datos.
    """
    try:
        supervisor_id = validar_id(supervisor_id)
        
        if fecha_baja is None:
            fecha_baja = datetime.now().strftime('%Y-%m-%d')
        else:
            fecha_baja = validar_fecha(fecha_baja, "fecha_baja", requerida=True)
        
        # Obtener supervisor actual
        supervisor = obtener_supervisor(supervisor_id)
        
        if not supervisor.es_activo():
            logger.warning(f"Supervisor ya estaba inactivo: {supervisor.nombre}")
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE supervisores SET fecha_baja = ? WHERE id = ?",
                (fecha_baja, supervisor_id)
            )
        
        # Notificar cambio
        notificar_cambio("supervisores", "UPDATE", {
            "id": supervisor_id,
            "fecha_baja": fecha_baja
        })
        
        invalidar_supervisores()
        
        logger.info(f"Supervisor dado de baja: {supervisor.nombre} (ID: {supervisor_id})")
        
        # Retornar objeto actualizado
        supervisor.fecha_baja = fecha_baja
        return supervisor
        
    except (ValidationError, SupervisorError) as e:
        logger.error(f"Error dando de baja supervisor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("UPDATE", str(e))


def reactivar_supervisor(supervisor_id: int) -> Supervisor:
    """Reactiva un supervisor eliminando su fecha de baja.
    
    Args:
        supervisor_id: ID del supervisor a reactivar.
    
    Returns:
        Objeto Supervisor actualizado sin fecha de baja.
    
    Raises:
        ValidationError: Si el ID no es válido.
        SupervisorNoEncontrado: Si no existe el supervisor.
        DatabaseError: Si hay error en la base de datos.
    """
    try:
        supervisor_id = validar_id(supervisor_id)
        
        # Obtener supervisor actual
        supervisor = obtener_supervisor(supervisor_id)
        
        if supervisor.es_activo():
            logger.warning(f"Supervisor ya estaba activo: {supervisor.nombre}")
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE supervisores SET fecha_baja = NULL WHERE id = ?",
                (supervisor_id,)
            )
        
        # Notificar cambio
        notificar_cambio("supervisores", "UPDATE", {
            "id": supervisor_id,
            "fecha_baja": None
        })
        
        invalidar_supervisores()
        
        logger.info(f"Supervisor reactivado: {supervisor.nombre} (ID: {supervisor_id})")
        
        # Retornar objeto actualizado
        supervisor.fecha_baja = None
        return supervisor
        
    except (ValidationError, SupervisorError) as e:
        logger.error(f"Error reactivando supervisor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("UPDATE", str(e))


# =============================================================================
# FUNCIONES AUXILIARES PRIVADAS
# =============================================================================

def _buscar_supervisor_por_nombre(nombre: str) -> Optional[Supervisor]:
    """Busca un supervisor por nombre exacto (uso interno).
    
    Args:
        nombre: Nombre del supervisor a buscar.
    
    Returns:
        Objeto Supervisor si existe, None en caso contrario.
    """
    try:
        resultado = gestor_db.ejecutar(
            "SELECT id, nombre, fecha_alta, fecha_baja FROM supervisores WHERE nombre = ?",
            (nombre,)
        )
        
        if not resultado:
            return None
        
        r = resultado[0]
        return Supervisor(
            id=r['id'],
            nombre=r['nombre'],
            fecha_alta=r['fecha_alta'],
            fecha_baja=r['fecha_baja']
        )
    except Exception:
        return None