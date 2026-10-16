# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de generación de gráficos y estadísticas OPTIMIZADO
# =============================================================================

from datetime import date, datetime, timedelta
from collections import defaultdict
from database.gestor_db import gestor_db
from services.cache import cache_global
from services.calculo_pasadas import (
    mes_de_fecha_turno,
    normalizar_turno,
    rango_datetime_de_mes,
)


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
            COALESCE(fecha_operativa, fecha) AS fecha,
            turno,
            COUNT(*) as total_pasadas,
            COUNT(DISTINCT objetivo_id) as objetivos_controlados
        FROM pasadas
        WHERE COALESCE(fecha_operativa, fecha) BETWEEN ? AND ?
        GROUP BY fecha, turno
        ORDER BY fecha
    """
    
    resultados = gestor_db.ejecutar(query, (inicio_semana.isoformat(), fin_semana.isoformat()))
    
    # Indexar resultados por fecha
    datos_por_fecha = defaultdict(lambda: {'diurno': 0, 'nocturno': 0, 'objetivos': 0})
    for r in resultados:
        fecha = r['fecha']
        turno = {'D': 'diurno', 'N': 'nocturno'}.get(r['turno'], r['turno'])
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
            'cumple': obj['cumplimiento'] >= 75
        })
    
    return datos


@cache_global.auto_cache(ttl=600)
def obtener_promedio_cumplimiento_mensual(anio: int) -> list:
    """Retorna el promedio mensual usando fechas de turno persistidas."""
    query = """
        SELECT COALESCE(fecha_operativa, fecha) AS fecha_turno
        FROM pasadas
        WHERE COALESCE(fecha_operativa, fecha) BETWEEN ? AND ?
    """
    resultados = gestor_db.ejecutar(
        query, (f"{anio:04d}-01-01", f"{anio:04d}-12-31")
    )
    datos_mes = {}
    for resultado in resultados:
        _, mes = mes_de_fecha_turno(date.fromisoformat(resultado['fecha_turno']))
        mes_str = f"{mes:02d}"
        datos_mes[mes_str] = datos_mes.get(mes_str, 0) + 1

    objetivos = gestor_db.ejecutar("SELECT id, nombre, dias_semana FROM objetivos")
    nombres_meses = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    datos = []
    for mes in range(1, 13):
        pasadas_mes = datos_mes.get(f"{mes:02d}", 0)
        dias_esperados = 0
        dias_controlados = 0
        for objetivo in objetivos:
            dias_semana = [
                int(dia) for dia in (objetivo['dias_semana'] or '').split(',')
                if dia.strip()
            ]
            dias_esperados += len(dias_semana)
            if pasadas_mes > 0:
                dias_controlados += min(len(dias_semana), pasadas_mes)
        promedio = (
            dias_controlados / dias_esperados * 100
            if dias_esperados > 0 else 0
        )
        datos.append({
            'mes': mes,
            'mes_nombre': nombres_meses[mes - 1],
            'promedio': round(promedio, 1),
        })
    return datos


@cache_global.auto_cache(ttl=600)
def obtener_distribucion_turnos_mes(anio: int, mes: int) -> dict:
    """Retorna distribución de pasadas por turno en el mes."""
    rango_inicio, rango_fin = rango_datetime_de_mes(
        anio, mes, turno_noche_cruza=True
    )
    fecha_inicio = rango_inicio.date().isoformat()
    fecha_fin = (rango_fin.date() - timedelta(days=1)).isoformat()
    
    # UNA SOLA QUERY
    query = """
        SELECT turno, COUNT(*) as total
        FROM pasadas
        WHERE COALESCE(fecha_operativa, fecha) BETWEEN ? AND ?
        GROUP BY turno
    """
    
    resultados = gestor_db.ejecutar(query, (fecha_inicio, fecha_fin))
    
    distribucion = {'diurno': 0, 'nocturno': 0}
    for resultado in resultados:
        distribucion[normalizar_turno(resultado['turno'])] += resultado['total']
    return distribucion


@cache_global.auto_cache(ttl=600)
def obtener_top_supervisores(anio: int, mes: int, limite: int = 10) -> list:
    """Retorna los supervisores con más pasadas en el mes."""
    rango_inicio, rango_fin = rango_datetime_de_mes(
        anio, mes, turno_noche_cruza=True
    )
    fecha_inicio = rango_inicio.date().isoformat()
    fecha_fin = (rango_fin.date() - timedelta(days=1)).isoformat()
    
    # UNA SOLA QUERY con JOIN
    query = """
        SELECT 
            s.id,
            s.nombre,
            COUNT(p.id) as total_pasadas,
            COUNT(DISTINCT p.objetivo_id) as objetivos
        FROM supervisores s
        LEFT JOIN pasadas p ON s.id = p.supervisor_id 
            AND COALESCE(p.fecha_operativa, p.fecha) BETWEEN ? AND ?
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
