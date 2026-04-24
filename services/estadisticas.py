# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de generación de gráficos y estadísticas OPTIMIZADO
# =============================================================================

from datetime import datetime, timedelta
from collections import defaultdict
from database.gestor_db import gestor_db
from services.cache import cache_global


@cache_global.auto_cache(ttl=300)
def obtener_estadisticas_semana() -> dict:
    """
    Obtiene estadísticas de cumplimiento de la semana actual.
    OPTIMIZADO: 1 sola query para toda la semana (antes: 14 queries).
    """
    # Calcular rango de semana
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    # UNA SOLA QUERY para toda la semana
    query = """
        SELECT 
            fecha,
            turno,
            COUNT(*) as total_pasadas,
            COUNT(DISTINCT objetivo_id) as objetivos_controlados
        FROM pasadas
        WHERE fecha BETWEEN ? AND ?
        GROUP BY fecha, turno
        ORDER BY fecha
    """
    
    resultados = gestor_db.ejecutar(query, (inicio_semana.isoformat(), fin_semana.isoformat()))
    
    # Indexar resultados por fecha
    datos_por_fecha = defaultdict(lambda: {'diurno': 0, 'nocturno': 0, 'objetivos': 0})
    for r in resultados:
        fecha = r['fecha']
        turno = r['turno']
        datos_por_fecha[fecha][turno] = r['total_pasadas']
        # El máximo de objetivos entre turnos (puede haber objetivos en ambos)
        datos_por_fecha[fecha]['objetivos'] = max(
            datos_por_fecha[fecha]['objetivos'], 
            r['objetivos_controlados']
        )
    
    # Construir respuesta
    estadisticas = {
        'fecha_inicio': inicio_semana.isoformat(),
        'fecha_fin': fin_semana.isoformat(),
        'dias_semana': []
    }

    for i in range(7):
        fecha = inicio_semana + timedelta(days=i)
        fecha_str = fecha.isoformat()
        datos = datos_por_fecha.get(fecha_str, {'diurno': 0, 'nocturno': 0, 'objetivos': 0})
        
        estadisticas['dias_semana'].append({
            'fecha': fecha_str,
            'dia_nombre': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha.weekday()],
            'diurno': datos['diurno'],
            'nocturno': datos['nocturno'],
            'objetivos_controlados': datos['objetivos']
        })

    return estadisticas


@cache_global.auto_cache(ttl=600)
def obtener_cumplimiento_por_objetivo(anio: int, mes: int) -> list:
    """Retorna datos de cumplimiento por objetivo para gráfico."""
    from services.reportes import generar_reporte_mensual
    
    reporte = generar_reporte_mensual(anio, mes)
    
    datos = []
    for obj in reporte['objetivos']:
        datos.append({
            'nombre': obj['nombre'],
            'cumplimiento': obj['cumplimiento'],
            'dias_esperados': obj['dias_esperados'],
            'dias_controlados': obj['dias_esperados'] - obj['dias_sin_control'],
            'cumple': obj['cumplimiento'] >= 80
        })
    
    return datos


@cache_global.auto_cache(ttl=600)
def obtener_promedio_cumplimiento_mensual(anio: int) -> list:
    """
    Retorna promedio de cumplimiento por mes del año.
    OPTIMIZADO: 1 sola query con todos los meses.
    """
    from calendar import monthrange
    
    # UNA SOLA QUERY para todo el año
    query = """
        SELECT 
            strftime('%m', fecha) as mes,
            COUNT(DISTINCT objetivo_id) as objetivos,
            COUNT(*) as total_pasadas
        FROM pasadas
        WHERE strftime('%Y', fecha) = ?
        GROUP BY strftime('%m', fecha)
        ORDER BY mes
    """
    
    resultados = gestor_db.ejecutar(query, (str(anio),))
    
    # Indexar por mes
    datos_mes = {r['mes']: {'objetivos': r['objetivos'], 'pasadas': r['total_pasadas']} for r in resultados}
    
    # Obtener objetivos activos
    objetivos = gestor_db.ejecutar("SELECT id, nombre, dias_semana FROM objetivos")
    
    datos = []
    for mes in range(1, 13):
        mes_str = f"{mes:02d}"
        datos_m = datos_mes.get(mes_str, {'objetivos': 0, 'pasadas': 0})
        
        # Calcular días esperados por objetivo
        dias_esperados = 0
        dias_controlados = 0
        
        for obj in objetivos:
            dias_semana = [int(d) for d in obj['dias_semana'].split(",") if d.strip()]
            dias_esperados += len(dias_semana)
            # Aproximación: si hay pasadas, se controló
            if datos_m['pasadas'] > 0:
                dias_controlados += min(len(dias_semana), datos_m['pasadas'])
        
        promedio = (dias_controlados / dias_esperados * 100) if dias_esperados > 0 else 0
        
        datos.append({
            'mes': mes,
            'mes_nombre': [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ][mes - 1],
            'promedio': round(promedio, 1)
        })
    
    return datos


@cache_global.auto_cache(ttl=600)
def obtener_distribucion_turnos_mes(anio: int, mes: int) -> dict:
    """Retorna distribución de pasadas por turno en el mes."""
    from calendar import monthrange
    total_dias = monthrange(anio, mes)[1]
    fecha_inicio = f"{anio}-{mes:02d}-01"
    fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
    
    # UNA SOLA QUERY
    query = """
        SELECT turno, COUNT(*) as total
        FROM pasadas
        WHERE fecha BETWEEN ? AND ?
        GROUP BY turno
    """
    
    resultados = gestor_db.ejecutar(query, (fecha_inicio, fecha_fin))
    
    return {
        'diurno': next((r['total'] for r in resultados if r['turno'] == 'diurno'), 0),
        'nocturno': next((r['total'] for r in resultados if r['turno'] == 'nocturno'), 0)
    }


@cache_global.auto_cache(ttl=600)
def obtener_top_supervisores(anio: int, mes: int, limite: int = 10) -> list:
    """Retorna los supervisores con más pasadas en el mes."""
    from calendar import monthrange
    total_dias = monthrange(anio, mes)[1]
    fecha_inicio = f"{anio}-{mes:02d}-01"
    fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
    
    # UNA SOLA QUERY con JOIN
    query = """
        SELECT 
            s.id,
            s.nombre,
            COUNT(p.id) as total_pasadas,
            COUNT(DISTINCT p.objetivo_id) as objetivos
        FROM supervisores s
        LEFT JOIN pasadas p ON s.id = p.supervisor_id 
            AND p.fecha BETWEEN ? AND ?
        WHERE s.fecha_baja IS NULL
        GROUP BY s.id, s.nombre
        ORDER BY total_pasadas DESC
        LIMIT ?
    """
    
    resultados = gestor_db.ejecutar(query, (fecha_inicio, fecha_fin, limite))
    
    return [{
        'id': r['id'],
        'nombre': r['nombre'],
        'total_pasadas': r['total_pasadas'],
        'objetivos': r['objetivos']
    } for r in resultados]
    fecha_inicio = f"{anio}-{mes:02d}-01"
    fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
    
    cursor.execute("""
        SELECT s.nombre, COUNT(p.id) as total_pasadas
        FROM pasadas p
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha BETWEEN ? AND ?
        GROUP BY s.id, s.nombre
        ORDER BY total_pasadas DESC
        LIMIT ?
    """, (fecha_inicio, fecha_fin, limite))
    
    resultado = cursor.fetchall()
    conexion.close()
    
    return [
        {'nombre': r[0], 'pasadas': r[1]}
        for r in resultado
    ]
