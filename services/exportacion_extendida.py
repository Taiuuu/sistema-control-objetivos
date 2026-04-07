# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de exportación extendida (CSV, JSON)
# =============================================================================

import sqlite3
import json
import csv
from datetime import datetime
from database.db import DB_PATH


def exportar_pasadas_csv(anio: int, mes: int, ruta: str) -> None:
    """Exporta todas las pasadas del mes a CSV."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Rango del mes
    from calendar import monthrange
    total_dias = monthrange(anio, mes)[1]
    fecha_inicio = f"{anio}-{mes:02d}-01"
    fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
    
    cursor.execute("""
        SELECT p.fecha, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha BETWEEN ? AND ?
        ORDER BY p.fecha, p.hora
    """, (fecha_inicio, fecha_fin))
    
    pasadas = cursor.fetchall()
    conexion.close()
    
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Fecha', 'Hora', 'Turno', 'Objetivo', 'Supervisor'])
        
        for p in pasadas:
            writer.writerow(p)


def exportar_reporte_json(anio: int, mes: int, ruta: str) -> None:
    """Exporta el reporte mensual completo a JSON."""
    from services.reportes import generar_reporte_mensual
    from services.estadisticas import obtener_distribucion_turnos_mes, obtener_top_supervisores
    
    reporte = generar_reporte_mensual(anio, mes)
    distribucion = obtener_distribucion_turnos_mes(anio, mes)
    top_supervisores = obtener_top_supervisores(anio, mes)
    
    datos_completos = {
        'fecha_generacion': datetime.now().isoformat(),
        'periodo': f"{anio}-{mes:02d}",
        'resumen': {
            'total_objetivos': len(reporte['objetivos']),
            'objetivos_cumplen': sum(1 for o in reporte['objetivos'] if o['cumplimiento'] >= 80),
            'cumplimiento_promedio': round(
                sum(o['cumplimiento'] for o in reporte['objetivos']) / len(reporte['objetivos'])
                if reporte['objetivos'] else 0, 1
            ),
            'distribucion_turnos': distribucion
        },
        'objetivos': reporte['objetivos'],
        'top_supervisores': top_supervisores
    }
    
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos_completos, f, ensure_ascii=False, indent=2)


def exportar_supervisor_mes_csv(supervisor_id: int, anio: int, mes: int, ruta: str) -> None:
    """Exporta todas las pasadas de un supervisor en el mes a CSV."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    from calendar import monthrange
    total_dias = monthrange(anio, mes)[1]
    fecha_inicio = f"{anio}-{mes:02d}-01"
    fecha_fin = f"{anio}-{mes:02d}-{total_dias:02d}"
    
    # Obtener nombre del supervisor
    cursor.execute("SELECT nombre FROM supervisores WHERE id = ?", (supervisor_id,))
    resultado = cursor.fetchone()
    supervisor_nombre = resultado[0] if resultado else "Desconocido"
    
    # Obtener pasadas
    cursor.execute("""
        SELECT p.fecha, p.hora, p.turno, o.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        WHERE p.supervisor_id = ? AND p.fecha BETWEEN ? AND ?
        ORDER BY p.fecha, p.hora
    """, (supervisor_id, fecha_inicio, fecha_fin))
    
    pasadas = cursor.fetchall()
    conexion.close()
    
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Supervisor', supervisor_nombre])
        writer.writerow(['Período', f"{anio}/{mes:02d}"])
        writer.writerow(['Total de pasadas', len(pasadas)])
        writer.writerow([])
        writer.writerow(['Fecha', 'Hora', 'Turno', 'Objetivo'])
        
        for p in pasadas:
            writer.writerow(p)


def exportar_base_completa_json(ruta: str) -> None:
    """Exporta toda la base de datos (objetivos, supervisores, pasadas del mes actual) a JSON."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Objetivos
    cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos")
    objetivos = [
        {
            'id': r[0],
            'nombre': r[1],
            'fecha_inicio': r[2],
            'fecha_fin': r[3],
            'dias_semana': r[4]
        }
        for r in cursor.fetchall()
    ]
    
    # Supervisores
    cursor.execute("SELECT id, nombre FROM supervisores")
    supervisores = [
        {'id': r[0], 'nombre': r[1]}
        for r in cursor.fetchall()
    ]
    
    # Último mes de pasadas
    from datetime import date
    hoy = date.today()
    cursor.execute("""
        SELECT p.fecha, p.hora, p.turno, p.objetivo_id, p.supervisor_id
        FROM pasadas p
        WHERE p.fecha >= date('now', '-30 days')
        ORDER BY p.fecha DESC, p.hora
    """)
    pasadas_recientes = [
        {
            'fecha': r[0],
            'hora': r[1],
            'turno': r[2],
            'objetivo_id': r[3],
            'supervisor_id': r[4]
        }
        for r in cursor.fetchall()
    ]
    
    conexion.close()
    
    datos = {
        'fecha_exportacion': datetime.now().isoformat(),
        'version': '1.0.0',
        'objetivos': objetivos,
        'supervisores': supervisores,
        'pasadas_ultimos_30_dias': pasadas_recientes
    }
    
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
