# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de reportes - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo para la generación de reportes del sistema.

Proporciona funciones para:
- Obtener objetivos del día según schedule
- Generar reportes diarios de cumplimiento
- Generar reportes mensuales detallados
- Consultas de cobertura y estadísticas
- Análisis de cumplimiento de objetivos

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
import datetime
import calendar
from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Any

from database.gestor_db import gestor_db
from services.cache import cache_global
from .exceptions import (
    ReporteError, FechaInvalidaReporte, DatosInsuficientesReporte
)

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

TURNOS_VALIDOS = ["Mañana", "Tarde", "Noche", "Completo"]
AÑO_MINIMO = 2000
AÑO_MAXIMO = 2100


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def _validar_fecha(fecha: str) -> None:
    """Valida que la fecha tenga formato correcto YYYY-MM-DD."""
    try:
        datetime.datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise FechaInvalidaReporte(fecha)


def _validar_ano_mes(anio: int, mes: int) -> None:
    """Valida año y mes para reportes."""
    if not isinstance(anio, int) or not isinstance(mes, int):
        raise ReporteError("Año y mes deben ser números enteros")
    if not (AÑO_MINIMO <= anio <= AÑO_MAXIMO):
        raise ReporteError(f"Año debe estar entre {AÑO_MINIMO} y {AÑO_MAXIMO}")
    if not (1 <= mes <= 12):
        raise ReporteError("Mes debe estar entre 1 y 12")


def _obtener_dia_semana(fecha: str) -> int:
    """Obtiene el día de la semana (1=Lunes, 7=Domingo)."""
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    return fecha_dt.isoweekday()


def _parsear_dias_semana(dias_str: str) -> List[int]:
    """Parsea string de días en lista de enteros."""
    try:
        return [int(d.strip()) for d in dias_str.split(",") if d.strip()]
    except ValueError:
        return []


# =============================================================================
# REPORTES DIARIOS
# =============================================================================

@cache_global.auto_cache(ttl=300)
def obtener_objetivos_del_dia(fecha: str) -> List[Tuple[int, str, str]]:
    """Obtiene los objetivos que deben controlarse en una fecha específica.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD.
    
    Returns:
        Lista de tuplas (id_objetivo, nombre, dias_semana).
        
    Raises:
        FechaInvalidaReporte: Si la fecha no es válida.
        DatabaseError: Si hay error en la consulta.
    
    Note:
        Resultado cacheado por 5 minutos.
    
    Example:
        >>> objetivos = obtener_objetivos_del_dia("2026-04-27")
        >>> print(len(objetivos))
        3
    """
    try:
        _validar_fecha(fecha)
        
        # Query optimizada
        query = """
            SELECT id, nombre, dias_semana, fecha_inicio, fecha_fin
            FROM objetivos
            WHERE (fecha_inicio IS NULL OR fecha_inicio <= ?)
              AND (fecha_fin IS NULL OR fecha_fin >= ?)
        """
        
        objetivos_db = gestor_db.ejecutar(query, (fecha, fecha))
        
        if not objetivos_db:
            logger.debug(f"No hay objetivos para {fecha}")
            return []
        
        dia_semana = _obtener_dia_semana(fecha)
        resultado = []
        
        for obj in objetivos_db:
            obj_id = obj['id']
            nombre = obj['nombre']
            dias_semana_str = obj['dias_semana']
            fecha_inicio = obj['fecha_inicio']
            fecha_fin = obj['fecha_fin']
            
            # Validar fechas de inicio/fin
            if fecha_inicio and fecha < fecha_inicio:
                continue
            if fecha_fin and fecha > fecha_fin:
                continue
            
            # Verificar que sea un día válido para este objetivo
            dias = _parsear_dias_semana(dias_semana_str)
            if dia_semana not in dias:
                continue
            
            resultado.append((obj_id, nombre, dias_semana_str))
        
        logger.info(f"Objetivos del día {fecha}: {len(resultado)} encontrados")
        return resultado
        
    except FechaInvalidaReporte:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo objetivos del día {fecha}: {e}")
        raise ReporteError(f"Error obteniendo objetivos: {str(e)}")


def objetivo_corresponde(fecha: str, dias_semana_str: str) -> bool:
    """Verifica si un objetivo debe controlarse en una fecha.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD.
        dias_semana_str: String con días (ej: "1,2,3").
    
    Returns:
        True si el objetivo corresponde controlar en esa fecha.
    """
    try:
        _validar_fecha(fecha)
        
        dia = _obtener_dia_semana(fecha)
        dias = _parsear_dias_semana(dias_semana_str)
        
        return dia in dias
        
    except Exception as e:
        logger.error(f"Error verificando correspondencia: {e}")
        return False


@cache_global.auto_cache(ttl=600)
def generar_reporte_diario(fecha: str) -> Dict[str, Any]:
    """Genera reporte detallado de pasadas de un día.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD.
    
    Returns:
        Diccionario con estructura:
        {
            'fecha': str,
            'pasadas': [
                {
                    'id': int,
                    'hora': str,
                    'turno': str,
                    'objetivo': str,
                    'supervisor': str
                }
            ],
            'total': int,
            'cumplimiento_porcentaje': float
        }
    
    Raises:
        FechaInvalidaReporte: Si la fecha no es válida.
        DatabaseError: Si hay error en la consulta.
        
    Note:
        Resultado cacheado por 10 minutos.
    """
    try:
        _validar_fecha(fecha)
        
        query = """
            SELECT p.id, p.hora, p.turno, o.nombre as objetivo, s.nombre as supervisor
            FROM pasadas p
            JOIN objetivos o ON p.objetivo_id = o.id
            JOIN supervisores s ON p.supervisor_id = s.id
            WHERE p.fecha = ?
            ORDER BY p.hora, p.turno
        """
        
        pasadas = gestor_db.ejecutar(query, (fecha,))
        
        pasadas_list = [
            {
                'id': p['id'],
                'hora': p['hora'],
                'turno': p['turno'],
                'objetivo': p['objetivo'],
                'supervisor': p['supervisor']
            }
            for p in pasadas
        ]
        
        total_pasadas = len(pasadas_list)
        
        # Calcular cumplimiento (simplista: % de objetivos con pasada)
        objetivos_dia = obtener_objetivos_del_dia(fecha)
        cumplimiento = 0.0
        if objetivos_dia:
            objetivos_con_pasada = set()
            for pasada in pasadas_list:
                for obj in objetivos_dia:
                    if obj[1] == pasada['objetivo']:
                        objetivos_con_pasada.add(obj[0])
            cumplimiento = (len(objetivos_con_pasada) / len(objetivos_dia)) * 100
        
        reporte = {
            'fecha': fecha,
            'pasadas': pasadas_list,
            'total': total_pasadas,
            'cumplimiento_porcentaje': round(cumplimiento, 1)
        }
        
        logger.info(f"Reporte diario generado para {fecha}: {total_pasadas} pasadas")
        return reporte
        
    except FechaInvalidaReporte:
        raise
    except Exception as e:
        logger.error(f"Error generando reporte diario {fecha}: {e}")
        raise ReporteError(f"Error generando reporte: {str(e)}")


# =============================================================================
# REPORTES MENSUALES
# =============================================================================

@cache_global.auto_cache(ttl=1800)
def generar_reporte_mensual(anio: int, mes: int) -> Dict[str, Any]:
    """Genera reporte mensual detallado de cumplimiento.
    
    Args:
        anio: Año (ej: 2026).
        mes: Mes (1-12).
    
    Returns:
        Diccionario con estructura:
        {
            'anio': int,
            'mes': int,
            'periodo': str,
            'total_dias': int,
            'objetivos': [
                {
                    'id': int,
                    'nombre': str,
                    'dias_esperados': int,
                    'dias_con_pasada': int,
                    'dias_sin_pasada': int,
                    'cumplimiento_porcentaje': float
                }
            ],
            'cumplimiento_total': float
        }
    
    Raises:
        ReporteError: Si hay error validando parámetros.
        DatabaseError: Si hay error en consultas.
        
    Note:
        Resultado cacheado por 30 minutos.
    """
    try:
        _validar_ano_mes(anio, mes)
        
        total_dias = calendar.monthrange(anio, mes)[1]
        fecha_inicio = f"{anio}-{mes:02d}-01"
        fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
        
        # Obtener todos los objetivos
        objetivos = gestor_db.ejecutar(
            """SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana 
               FROM objetivos ORDER BY nombre"""
        )
        
        if not objetivos:
            logger.warning(f"No hay objetivos para reporte {mes}/{anio}")
            raise DatosInsuficientesReporte("No hay objetivos en el sistema")
        
        # Obtener todas las pasadas del mes en una sola query (optimización)
        query_pasadas = """
            SELECT fecha, objetivo_id, COUNT(*) as total
            FROM pasadas
            WHERE fecha BETWEEN ? AND ?
            GROUP BY fecha, objetivo_id
        """
        pasadas_raw = gestor_db.ejecutar(query_pasadas, (fecha_inicio, fecha_fin))
        
        # Indexar pasadas por objetivo y fecha
        pasadas_por_objetivo = defaultdict(set)
        for p in pasadas_raw:
            pasadas_por_objetivo[p['objetivo_id']].add(p['fecha'])
        
        reporte = {
            'anio': anio,
            'mes': mes,
            'periodo': f"{mes:02d}/{anio}",
            'total_dias': total_dias,
            'objetivos': [],
            'cumplimiento_total': 0.0
        }
        
        total_cumplimiento_ponderado = 0.0
        total_objetivos_esperados = 0
        
        for obj in objetivos:
            obj_id = obj['id']
            nombre = obj['nombre']
            inicio = obj['fecha_inicio']
            fin = obj['fecha_fin']
            dias_str = obj['dias_semana']
            
            dias_semana = _parsear_dias_semana(dias_str)
            dias_esperados = 0
            dias_con_pasada = 0
            
            # Contar días esperados y con pasada
            for dia in range(1, total_dias + 1):
                fecha = f"{anio}-{mes:02d}-{dia:02d}"
                fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
                
                # Validar fechas de inicio/fin
                if inicio and fecha < inicio:
                    continue
                if fin and fecha > fin:
                    continue
                
                # Verificar que sea un día válido
                if fecha_dt.isoweekday() not in dias_semana:
                    continue
                
                dias_esperados += 1
                
                # Verificar si hay pasada para este día
                if fecha in pasadas_por_objetivo[obj_id]:
                    dias_con_pasada += 1
            
            # Calcular cumplimiento
            cumplimiento = 0.0
            if dias_esperados > 0:
                cumplimiento = (dias_con_pasada / dias_esperados) * 100
                total_cumplimiento_ponderado += cumplimiento
                total_objetivos_esperados += 1
            
            reporte['objetivos'].append({
                'id': obj_id,
                'nombre': nombre,
                'dias_esperados': dias_esperados,
                'dias_con_pasada': dias_con_pasada,
                'dias_sin_pasada': dias_esperados - dias_con_pasada,
                'cumplimiento_porcentaje': round(cumplimiento, 1)
            })
        
        # Cumplimiento total
        if total_objetivos_esperados > 0:
            reporte['cumplimiento_total'] = round(
                total_cumplimiento_ponderado / total_objetivos_esperados,
                1
            )
        
        logger.info(f"Reporte mensual generado {mes}/{anio}: "
                   f"{len(reporte['objetivos'])} objetivos, "
                   f"Cumplimiento: {reporte['cumplimiento_total']}%")
        
        return reporte
        
    except (ReporteError, DatosInsuficientesReporte):
        raise
    except Exception as e:
        logger.error(f"Error generando reporte mensual {mes}/{anio}: {e}")
        raise ReporteError(f"Error generando reporte: {str(e)}")


def imprimir_reporte_mensual(anio: int, mes: int) -> None:
    """Imprime el reporte mensual en formato tabla en consola.
    
    Args:
        anio: Año.
        mes: Mes.
    """
    try:
        reporte = generar_reporte_mensual(anio, mes)
        
        print(f"\n{'='*80}")
        print(f"REPORTE MENSUAL {reporte['periodo']}")
        print(f"{'='*80}\n")
        
        print(f"{'Objetivo':<30} {'Esperados':<12} {'Cumplidos':<12} {'Cumplimiento':<12}")
        print("-" * 80)
        
        for obj in reporte['objetivos']:
            print(
                f"{obj['nombre']:<30} "
                f"{obj['dias_esperados']:<12} "
                f"{obj['dias_con_pasada']:<12} "
                f"{obj['cumplimiento_porcentaje']:<12.1f}%"
            )
        
        print("-" * 80)
        print(f"{'CUMPLIMIENTO TOTAL':<54} {reporte['cumplimiento_total']:.1f}%")
        print(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"Error imprimiendo reporte: {e}")
        print(f"Error al generar reporte: {e}")