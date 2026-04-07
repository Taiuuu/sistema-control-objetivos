# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de generación de gráficos y estadísticas
# =============================================================================

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
from database.db import DB_PATH


def obtener_estadisticas_semana() -> dict:
    """Obtiene estadísticas de cumplimiento de la semana actual."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # Calcular rango de semana
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    estadisticas = {
        'fecha_inicio': inicio_semana.isoformat(),
        'fecha_fin': fin_semana.isoformat(),
        'dias_semana': []
    }

    for i in range(7):
        fecha = inicio_semana + timedelta(days=i)
        fecha_str = fecha.isoformat()
        
        # Total de pasadas por turno
        cursor.execute("""
            SELECT turno, COUNT(*) FROM pasadas
            WHERE fecha = ?
            GROUP BY turno
        """, (fecha_str,))
        
        pasadas_por_turno = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total de objetivos del día
        cursor.execute("""
            SELECT COUNT(DISTINCT objetivo_id) FROM pasadas
            WHERE fecha = ?
        """, (fecha_str,))
        
        objetivos_controlados = cursor.fetchone()[0]
        
        estadisticas['dias_semana'].append({
            'fecha': fecha_str,
            'dia_nombre': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha.weekday()],
            'diurno': pasadas_por_turno.get('diurno', 0),
            'nocturno': pasadas_por_turno.get('nocturno', 0),
            'objetivos_controlados': objetivos_controlados
        })

    conexion.close()
    return estadisticas


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


def obtener_promedio_cumplimiento_mensual(anio: int) -> list:
    """Retorna promedio de cumplimiento por mes del año."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    datos = []
    
    for mes in range(1, 13):
        cursor.execute("""
            SELECT COUNT(DISTINCT objetivo_id) FROM objetivos
        """)
        total_objetivos = cursor.fetchone()[0]
        
        if total_objetivos == 0:
            continue
        
        from services.reportes import generar_reporte_mensual
        reporte = generar_reporte_mensual(anio, mes)
        
        if reporte['objetivos']:
            promedio = sum(obj['cumplimiento'] for obj in reporte['objetivos']) / len(reporte['objetivos'])
        else:
            promedio = 0
        
        datos.append({
            'mes': mes,
            'mes_nombre': [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ][mes - 1],
            'promedio': round(promedio, 1)
        })
    
    conexion.close()
    return datos


def obtener_distribucion_turnos_mes(anio: int, mes: int) -> dict:
    """Retorna distribución de pasadas por turno en el mes."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Rango del mes
    from calendar import monthrange
    total_dias = monthrange(anio, mes)[1]
    fecha_inicio = f"{anio}-{mes:02d}-01"
    fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
    
    cursor.execute("""
        SELECT turno, COUNT(*) FROM pasadas
        WHERE fecha BETWEEN ? AND ?
        GROUP BY turno
    """, (fecha_inicio, fecha_fin))
    
    resultado = cursor.fetchall()
    conexion.close()
    
    return {
        'diurno': next((r[1] for r in resultado if r[0] == 'diurno'), 0),
        'nocturno': next((r[1] for r in resultado if r[0] == 'nocturno'), 0)
    }


def obtener_top_supervisores(anio: int, mes: int, limite: int = 10) -> list:
    """Retorna los supervisores con más pasadas en el mes."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    from calendar import monthrange
    total_dias = monthrange(anio, mes)[1]
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
