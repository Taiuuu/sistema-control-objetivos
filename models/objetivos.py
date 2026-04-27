# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de objetivos - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo para la gestión completa del ciclo de vida de objetivos del sistema.

Proporciona funciones para:
- Crear nuevos objetivos
- Consultar objetivos (individuales o listados)
- Actualizar información de objetivos
- Registrar finalización de objetivos (soft delete)
- Búsqueda y filtrado avanzado

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
from datetime import datetime
from typing import List, Optional

from database.gestor_db import gestor_db
from services.cache import cache_global, invalidar_objetivos
from services.sincronizacion import notificar_cambio

from .exceptions import (
    ObjetivoError, ObjetivoNoEncontrado, ObjetivoYaExiste, DatabaseError
)
from .types import Objetivo
from .validators import (
    validar_nombre, validar_fecha, validar_id,
    validar_dias_semana
)

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCIONES DE ALTA (CREATE)
# =============================================================================

def agregar_objetivo(
    nombre: str,
    fecha_inicio: str,
    dias_semana: str,
    fecha_fin: Optional[str] = None
) -> Objetivo:
    """Registra un nuevo objetivo en el sistema.
    
    Args:
        nombre: Nombre descriptivo del objetivo (3-255 caracteres).
        fecha_inicio: Fecha de inicio en formato YYYY-MM-DD.
        dias_semana: Días de aplicación (ej: "Lunes,Martes,Miércoles").
        fecha_fin: Fecha opcional de finalización en formato YYYY-MM-DD.
    
    Returns:
        Objeto Objetivo con los datos del objetivo creado, incluyendo ID.
    
    Raises:
        ValidationError: Si algún parámetro no cumple validaciones.
        DatabaseError: Si hay error en la base de datos.
        ObjetivoYaExiste: Si ya existe un objetivo con ese nombre.
    
    Example:
        >>> obj = agregar_objetivo("Venta Q1", "2026-01-01", "Lunes,Martes")
        >>> print(obj.id)
        42
    """
    try:
        # Validar parámetros
        nombre = validar_nombre(nombre)
        fecha_inicio = validar_fecha(fecha_inicio, "fecha_inicio", requerida=True)
        fecha_fin = validar_fecha(fecha_fin, "fecha_fin", requerida=False)
        dias_semana = validar_dias_semana(dias_semana)
        
        # Verificar que no exista objetivo con el mismo nombre
        existente = _buscar_objetivo_por_nombre(nombre)
        if existente:
            logger.warning(f"Intento de crear objetivo duplicado: {nombre}")
            raise ObjetivoYaExiste(nombre)
        
        # Insertar en base de datos
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO objetivos 
                    (nombre, fecha_inicio, fecha_fin, dias_semana)
                VALUES (?, ?, ?, ?)
            """, (nombre, fecha_inicio, fecha_fin, dias_semana))
            objetivo_id = cursor.lastrowid
        
        # Construir objeto retorno
        objetivo = Objetivo(
            id=objetivo_id,
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            dias_semana=dias_semana,
            creado_en=datetime.now().isoformat()
        )
        
        # Notificar cambio para sincronización
        notificar_cambio("objetivos", "INSERT", {
            "id": objetivo_id,
            "nombre": nombre,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "dias_semana": dias_semana
        })
        
        # Invalidar caché
        invalidar_objetivos()
        
        logger.info(f"Objetivo creado: {nombre} (ID: {objetivo_id})")
        return objetivo
        
    except (ValidationError, ObjetivoError) as e:
        logger.error(f"Error validando objetivo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear objetivo: {e}")
        raise DatabaseError("INSERT", str(e))


# =============================================================================
# FUNCIONES DE CONSULTA (READ)
# =============================================================================

@cache_global.auto_cache(ttl=60)
def listar_objetivos(
    solo_activos: bool = False,
    orden: str = "nombre"
) -> List[Objetivo]:
    """Retorna todos los objetivos del sistema.
    
    Args:
        solo_activos: Si True, solo retorna objetivos sin fecha de fin.
        orden: Campo para ordenar ('nombre', 'fecha_inicio', 'fecha_fin').
    
    Returns:
        Lista de objetos Objetivo.
        
    Raises:
        DatabaseError: Si hay error en la consulta.
        
    Note:
        Resultado cacheado por 60 segundos para optimizar consultas frecuentes.
    """
    try:
        campos_validos = {'nombre', 'fecha_inicio', 'fecha_fin'}
        if orden not in campos_validos:
            orden = 'nombre'
        
        if solo_activos:
            query = f"""
                SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana,
                       datetime('now') as creado_en
                FROM objetivos
                WHERE fecha_fin IS NULL
                ORDER BY {orden}
            """
        else:
            query = f"""
                SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana,
                       datetime('now') as creado_en
                FROM objetivos
                ORDER BY CASE WHEN fecha_fin IS NULL THEN 0 ELSE 1 END,
                         {orden}
            """
        
        resultados = gestor_db.ejecutar(query)
        
        objetivos = [
            Objetivo(
                id=r['id'],
                nombre=r['nombre'],
                fecha_inicio=r['fecha_inicio'],
                fecha_fin=r['fecha_fin'],
                dias_semana=r['dias_semana'],
                creado_en=r.get('creado_en')
            )
            for r in resultados
        ]
        
        logger.debug(f"Listado de objetivos: {len(objetivos)} registros")
        return objetivos
        
    except Exception as e:
        logger.error(f"Error al listar objetivos: {e}")
        raise DatabaseError("SELECT", str(e))


def obtener_objetivo(objetivo_id: int) -> Objetivo:
    """Obtiene un objetivo específico por ID.
    
    Args:
        objetivo_id: ID del objetivo a recuperar.
    
    Returns:
        Objeto Objetivo con los datos solicitados.
    
    Raises:
        ValidationError: Si el ID no es válido.
        ObjetivoNoEncontrado: Si no existe el objetivo.
        DatabaseError: Si hay error en la consulta.
    """
    try:
        objetivo_id = validar_id(objetivo_id)
        
        resultado = gestor_db.ejecutar(
            """SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana 
               FROM objetivos WHERE id = ?""",
            (objetivo_id,)
        )
        
        if not resultado:
            logger.warning(f"Objetivo no encontrado: ID {objetivo_id}")
            raise ObjetivoNoEncontrado(objetivo_id)
        
        r = resultado[0]
        objetivo = Objetivo(
            id=r['id'],
            nombre=r['nombre'],
            fecha_inicio=r['fecha_inicio'],
            fecha_fin=r['fecha_fin'],
            dias_semana=r['dias_semana']
        )
        
        logger.debug(f"Objetivo obtenido: {objetivo.nombre}")
        return objetivo
        
    except (ValidationError, ObjetivoError) as e:
        logger.error(f"Error obteniendo objetivo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("SELECT", str(e))


def buscar_objetivos(texto: str) -> List[Objetivo]:
    """Busca objetivos por nombre (búsqueda parcial).
    
    Args:
        texto: Texto a buscar en el nombre de objetivos.
    
    Returns:
        Lista de objetivos que coinciden con la búsqueda.
    """
    try:
        texto = validar_nombre(texto, "búsqueda")
        
        resultados = gestor_db.ejecutar(
            """SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana 
               FROM objetivos 
               WHERE nombre LIKE ? 
               ORDER BY nombre""",
            (f"%{texto}%",)
        )
        
        objetivos = [
            Objetivo(
                id=r['id'],
                nombre=r['nombre'],
                fecha_inicio=r['fecha_inicio'],
                fecha_fin=r['fecha_fin'],
                dias_semana=r['dias_semana']
            )
            for r in resultados
        ]
        
        logger.info(f"Búsqueda de objetivos: '{texto}' - {len(objetivos)} resultados")
        return objetivos
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise DatabaseError("SELECT", str(e))


# =============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# =============================================================================

def actualizar_objetivo(
    objetivo_id: int,
    nombre: str,
    fecha_inicio: str,
    dias_semana: str,
    fecha_fin: Optional[str] = None
) -> Objetivo:
    """Actualiza un objetivo existente.
    
    Args:
        objetivo_id: ID del objetivo a actualizar.
        nombre: Nuevo nombre (3-255 caracteres).
        fecha_inicio: Nueva fecha de inicio (YYYY-MM-DD).
        dias_semana: Nuevos días de aplicación.
        fecha_fin: Nueva fecha de fin opcional (YYYY-MM-DD).
    
    Returns:
        Objeto Objetivo con los datos actualizados.
    
    Raises:
        ValidationError: Si algún parámetro no cumple validaciones.
        ObjetivoNoEncontrado: Si no existe el objetivo.
        DatabaseError: Si hay error en la base de datos.
    """
    try:
        # Validar parámetros
        objetivo_id = validar_id(objetivo_id)
        nombre = validar_nombre(nombre)
        fecha_inicio = validar_fecha(fecha_inicio, "fecha_inicio", requerida=True)
        fecha_fin = validar_fecha(fecha_fin, "fecha_fin", requerida=False)
        dias_semana = validar_dias_semana(dias_semana)
        
        # Verificar que existe el objetivo
        objetivo_actual = obtener_objetivo(objetivo_id)
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE objetivos 
                SET nombre = ?, fecha_inicio = ?, fecha_fin = ?, dias_semana = ?
                WHERE id = ?
            """, (nombre, fecha_inicio, fecha_fin, dias_semana, objetivo_id))
        
        # Construir objeto retorno
        objetivo = Objetivo(
            id=objetivo_id,
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            dias_semana=dias_semana,
            actualizado_en=datetime.now().isoformat()
        )
        
        # Notificar cambio
        notificar_cambio("objetivos", "UPDATE", {
            "id": objetivo_id,
            "nombre": nombre,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "dias_semana": dias_semana
        })
        
        invalidar_objetivos()
        
        logger.info(f"Objetivo actualizado: {nombre} (ID: {objetivo_id})")
        return objetivo
        
    except (ValidationError, ObjetivoError) as e:
        logger.error(f"Error actualizando objetivo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("UPDATE", str(e))


# =============================================================================
# FUNCIONES DE BAJA (SOFT DELETE)
# =============================================================================

def dar_de_baja_objetivo(
    objetivo_id: int,
    fecha_fin: Optional[str] = None
) -> Objetivo:
    """Registra la finalización de un objetivo (soft delete).
    
    La baja no elimina el registro, solo marca fecha_fin.
    
    Args:
        objetivo_id: ID del objetivo a dar de baja.
        fecha_fin: Fecha de finalización. Si no se proporciona, usa fecha actual.
    
    Returns:
        Objeto Objetivo actualizado con fecha de fin.
    
    Raises:
        ValidationError: Si los parámetros no son válidos.
        ObjetivoNoEncontrado: Si no existe el objetivo.
        DatabaseError: Si hay error en la base de datos.
    """
    try:
        objetivo_id = validar_id(objetivo_id)
        
        if fecha_fin is None:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        else:
            fecha_fin = validar_fecha(fecha_fin, "fecha_fin", requerida=True)
        
        # Obtener objetivo actual
        objetivo = obtener_objetivo(objetivo_id)
        
        if not objetivo.es_activo():
            logger.warning(f"Objetivo ya estaba inactivo: {objetivo.nombre}")
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE objetivos SET fecha_fin = ? WHERE id = ?",
                (fecha_fin, objetivo_id)
            )
        
        # Notificar cambio
        notificar_cambio("objetivos", "UPDATE", {
            "id": objetivo_id,
            "fecha_fin": fecha_fin
        })
        
        invalidar_objetivos()
        
        logger.info(f"Objetivo dado de baja: {objetivo.nombre} (ID: {objetivo_id})")
        
        # Retornar objeto actualizado
        objetivo.fecha_fin = fecha_fin
        return objetivo
        
    except (ValidationError, ObjetivoError) as e:
        logger.error(f"Error dando de baja objetivo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise DatabaseError("UPDATE", str(e))


# =============================================================================
# FUNCIONES AUXILIARES PRIVADAS
# =============================================================================

def _buscar_objetivo_por_nombre(nombre: str) -> Optional[Objetivo]:
    """Busca un objetivo por nombre exacto (uso interno).
    
    Args:
        nombre: Nombre del objetivo a buscar.
    
    Returns:
        Objeto Objetivo si existe, None en caso contrario.
    """
    try:
        resultado = gestor_db.ejecutar(
            "SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos WHERE nombre = ?",
            (nombre,)
        )
        
        if not resultado:
            return None
        
        r = resultado[0]
        return Objetivo(
            id=r['id'],
            nombre=r['nombre'],
            fecha_inicio=r['fecha_inicio'],
            fecha_fin=r['fecha_fin'],
            dias_semana=r['dias_semana']
        )
    except Exception:
        return None