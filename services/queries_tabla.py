# =============================================================================
# VESP Organizations - Queries para Tabla Principal OPTIMIZADAS
# Consultas a BD con pool de conexiones, caching y batching
# =============================================================================

from database.gestor_db import gestor_db, con_cache
from database.db import DB_PATH
import sqlite3


def contar_pasadas(fecha: str, objetivo_id: int, turno: str = None, supervisor_id: int = None) -> int:
    """
    Cuenta pasadas registradas para un objetivo en una fecha.
    OPTIMIZADO: Usa gestor_db con cacheo de resultados frecuentes.
    """
    # Construir query dinámicamente
    query = 'SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?'
    params = [fecha, objetivo_id]
    
    if turno:
        query += ' AND turno = ?'
        params.append(turno)
    if supervisor_id:
        query += ' AND supervisor_id = ?'
        params.append(supervisor_id)
    
    # Usar cache para consultas frecuentes (30 segundos para counts)
    return gestor_db.ejecutar_scalar(query, tuple(params))


def obtener_equipo(fecha: str, turno: str) -> str:
    """
    Obtiene los supervisores asignados a un turno en una fecha.
    OPTIMIZADO: Query optimizada con JOINs eficientes.
    """
    query = """
        SELECT s1.nombre, s2.nombre,
               CASE WHEN e.supervisor3_id IS NOT NULL THEN s3.nombre ELSE NULL END
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        LEFT JOIN supervisores s3 ON e.supervisor3_id = s3.id
        WHERE e.fecha = ? AND e.turno = ?
    """
    
    resultado = gestor_db.ejecutar(query, (fecha, turno))
    
    if not resultado:
        return "—"
    
    # Extraer valores del dict
    fila = resultado[0]
    nombres = [n for n in [fila['s1.nombre'], fila['s2.nombre'], fila.get('CASE WHEN e.supervisor3_id IS NOT NULL THEN s3.nombre ELSE NULL END')] if n is not None]
    
    if len(nombres) == 0:
        return "—"
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


@con_cache(ttl=60)
def cargar_supervisores() -> list:
    """
    Carga lista de (id, nombre) de supervisores.
    OPTIMIZADO: Cacheado por 60 segundos.
    """
    query = 'SELECT id, nombre FROM supervisores WHERE fecha_baja IS NULL ORDER BY nombre'
    resultados = gestor_db.ejecutar(query)
    return [(r['id'], r['nombre']) for r in resultados]


def obtener_todas_pasadas_por_turno(fecha: str, supervisor_id: int = None) -> tuple:
    """
    Obtiene conteo de pasadas por objetivo y turno.
    OPTIMIZADO: Una sola query en lugar de múltiples.
    Retorna (pasadas_dia, pasadas_noche) donde cada una es un dict {objetivo_id: count}.
    """
    query = """
        SELECT objetivo_id, turno, COUNT(*) as total
        FROM pasadas 
        WHERE fecha = ?
    """
    params = [fecha]
    
    if supervisor_id:
        query += " AND supervisor_id = ?"
        params.append(supervisor_id)
    
    query += " GROUP BY objetivo_id, turno"
    
    resultados = gestor_db.ejecutar(query, tuple(params))
    
    pasadas_dia = {}
    pasadas_noche = {}
    
    for fila in resultados:
        obj_id = fila['objetivo_id']
        turno = fila['turno']
        count = fila['total']
        
        if turno == "diurno":
            pasadas_dia[obj_id] = count
        elif turno == "nocturno":
            pasadas_noche[obj_id] = count
    
    return pasadas_dia, pasadas_noche


# =============================================================================
# NUEVAS FUNCIONES OPTIMIZADAS
# =============================================================================

def obtener_pasadas_fecha_rango(fecha_inicio: str, fecha_fin: str, objetivo_id: int = None) -> list:
    """
    Obtiene todas las pasadas en un rango de fechas.
    OPTIMIZADO: Bulk query con filtros opcionales.
    """
    query = """
        SELECT p.id, p.fecha, p.hora, p.turno, p.objetivo_id, p.supervisor_id,
               o.nombre as objetivo_nombre, s.nombre as supervisor_nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    
    if objetivo_id:
        query += " AND p.objetivo_id = ?"
        params.append(objetivo_id)
    
    query += " ORDER BY p.fecha DESC, p.hora DESC"
    
    return gestor_db.ejecutar(query, tuple(params))


def obtener_estado_cobertura_dia(fecha: str) -> dict:
    """
    Obtiene el estado de cobertura para todos los objetivos de un día.
    OPTIMIZADO: Una sola query con subconsultas.
    """
    query = """
        SELECT 
            o.id,
            o.nombre,
            COALESCE(SUM(CASE WHEN p.turno = 'diurno' THEN 1 ELSE 0 END), 0) as pasadas_diurno,
            COALESCE(SUM(CASE WHEN p.turno = 'nocturno' THEN 1 ELSE 0 END), 0) as pasadas_nocturno,
            COUNT(DISTINCT p.supervisor_id) as supervisores
        FROM objetivos o
        LEFT JOIN pasadas p ON o.id = p.objetivo_id AND p.fecha = ?
        WHERE o.fecha_fin IS NULL OR o.fecha_fin >= ?
        GROUP BY o.id, o.nombre
        ORDER BY o.nombre
    """
    
    resultados = gestor_db.ejecutar(query, (fecha, fecha))
    
    return {
        'fecha': fecha,
        'objetivos': [
            {
                'id': r['id'],
                'nombre': r['nombre'],
                'pasadas_diurno': r['pasadas_diurno'],
                'pasadas_nocturno': r['pasadas_nocturno'],
                'supervisores': r['supervisores'],
                'completo': r['pasadas_diurno'] > 0 and r['pasadas_nocturno'] > 0
            }
            for r in resultados
        ]
    }


def batch_contar_pasadas(fecha: str, objetivo_ids: list[int]) -> dict:
    """
    Cuenta pasadas para múltiples objetivos en una sola query.
    OPTIMIZADO: Bulk operation en lugar de N queries.
    """
    if not objetivo_ids:
        return {}
    
    placeholders = ','.join(['?'] * len(objetivo_ids))
    query = f"""
        SELECT objetivo_id, COUNT(*) as total
        FROM pasadas
        WHERE fecha = ? AND objetivo_id IN ({placeholders})
        GROUP BY objetivo_id
    """
    
    params = [fecha] + objetivo_ids
    resultados = gestor_db.ejecutar(query, tuple(params))
    
    return {r['objetivo_id']: r['total'] for r in resultados}


def obtener_resumen_diario(fecha: str) -> dict:
    """
    Obtiene un resumen completo del día en una sola query.
    OPTIMIZADO: Agregación en DB en lugar de Python.
    """
    query = """
        SELECT 
            COUNT(*) as total_pasadas,
            COUNT(DISTINCT objetivo_id) as objetivos_controlados,
            COUNT(DISTINCT supervisor_id) as supervisores_activos,
            COUNT(DISTINCT CASE WHEN turno = 'diurno' THEN 1 END) as pasadas_diurno,
            COUNT(DISTINCT CASE WHEN turno = 'nocturno' THEN 1 END) as pasadas_nocturno
        FROM pasadas
        WHERE fecha = ?
    """
    
    resultado = gestor_db.ejecutar_dict(query, (fecha,))
    
    if resultado:
        return {
            'fecha': fecha,
            'total_pasadas': resultado['total_pasadas'],
            'objetivos_controlados': resultado['objetivos_controlados'],
            'supervisores_activos': resultado['supervisores_activos'],
            'pasadas_diurno': resultado['pasadas_diurno'] or 0,
            'pasadas_nocturno': resultado['pasadas_nocturno'] or 0
        }
    
    return {
        'fecha': fecha,
        'total_pasadas': 0,
        'objetivos_controlados': 0,
        'supervisores_activos': 0,
        'pasadas_diurno': 0,
        'pasadas_nocturno': 0
    }
