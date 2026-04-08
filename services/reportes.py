# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de reportes y lógica de control diario
# =============================================================================

import sqlite3
import datetime
from database.db import DB_PATH


def obtener_objetivos_del_dia(fecha: str) -> list:
    """
    Retorna los objetivos que corresponden ser controlados en una fecha dada.
    - Solo muestra objetivos cuya fecha_inicio <= fecha
    - Si tiene fecha_fin, solo muestra si fecha <= fecha_fin
    - Si no tiene fecha_fin, se muestra indefinidamente
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, dias_semana, fecha_inicio, fecha_fin
        FROM objetivos
        WHERE (fecha_inicio IS NULL OR fecha_inicio <= ?)
          AND (fecha_fin IS NULL OR fecha_fin >= ?)
    """, (fecha, fecha))

    objetivos = cursor.fetchall()
    conexion.close()

    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    dia_semana = fecha_dt.isoweekday()

    resultado = []
    for o in objetivos:
        obj_id, nombre, dias_semana_str, fecha_inicio, fecha_fin = o

        if fecha_inicio and fecha < fecha_inicio:
            continue

        if fecha_fin and fecha > fecha_fin:
            continue

        dias = [int(d) for d in dias_semana_str.split(",")]
        if dia_semana not in dias:
            continue

        resultado.append((obj_id, nombre, dias_semana_str))

    return resultado


def objetivo_corresponde(fecha: str, dias: str) -> bool:
    """
    Verifica si un objetivo debe controlarse en una fecha dada,
    según sus días de cobertura configurados.
    """
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_dt.isoweekday()
    dias_lista = [int(d) for d in dias.split(",")]
    return dia in dias_lista


def reporte_mensual(anio: int, mes: int) -> None:
    """Imprime en consola el reporte de cumplimiento mensual por objetivo."""
    import calendar

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos")
    objetivos = cursor.fetchall()

    print(f"\n=== REPORTE MENSUAL {mes}/{anio} ===\n")
    print(f"{'Objetivo':<20} {'Días esperados':<16} {'Días cumplidos':<16} {'Cumplimiento'}")
    print("-" * 70)

    total_dias = calendar.monthrange(anio, mes)[1]

    for o in objetivos:
        obj_id, nombre, inicio, fin, dias_str = o
        dias_semana = [int(d) for d in dias_str.split(",")]
        dias_esperados = 0
        dias_cumplidos = 0

        for dia in range(1, total_dias + 1):
            fecha = f"{anio}-{mes:02d}-{dia:02d}"
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")

            if inicio and fecha < inicio:
                continue
            if fin and fecha > fin:
                continue
            if fecha_dt.isoweekday() not in dias_semana:
                continue

            dias_esperados += 1

            cursor.execute("""
                SELECT COUNT(*) FROM pasadas
                WHERE fecha = ? AND objetivo_id = ?
            """, (fecha, obj_id))

            if cursor.fetchone()[0] > 0:
                dias_cumplidos += 1

        if dias_esperados > 0:
            porcentaje = (dias_cumplidos / dias_esperados) * 100
            print(f"{nombre:<20} {dias_esperados:<16} {dias_cumplidos:<16} {porcentaje:.1f}%")

    conexion.close()


def generar_reporte_mensual(anio: int, mes: int) -> dict:
    """Genera y retorna el reporte de cumplimiento mensual por objetivo."""
    import calendar
    from collections import defaultdict

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos")
    objetivos = cursor.fetchall()

    total_dias = calendar.monthrange(anio, mes)[1]
    fecha_inicio_mes = f"{anio}-{mes:02d}-01"
    fecha_fin_mes = f"{anio}-{mes:02d}-{total_dias:02d}"

    cursor.execute("""
        SELECT fecha, objetivo_id, turno, COUNT(*)
        FROM pasadas
        WHERE fecha BETWEEN ? AND ?
        GROUP BY fecha, objetivo_id, turno
    """, (fecha_inicio_mes, fecha_fin_mes))
    pasadas_raw = cursor.fetchall()

    pasadas_por_objetivo = defaultdict(lambda: defaultdict(lambda: {'diurno': 0, 'nocturno': 0}))
    for fecha, objetivo_id, turno, cantidad in pasadas_raw:
        pasadas_por_objetivo[objetivo_id][fecha][turno] = cantidad

    reporte = {
        'anio': anio,
        'mes': mes,
        'objetivos': []
    }

    for o in objetivos:
        obj_id, nombre, inicio, fin, dias_str = o
        dias_semana = [int(d.strip()) for d in dias_str.split(",") if d.strip()]
        dias_esperados = 0
        dias_con_dia = 0
        dias_con_noche = 0
        dias_sin_control = 0

        for dia in range(1, total_dias + 1):
            fecha = f"{anio}-{mes:02d}-{dia:02d}"
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")

            if inicio and fecha < inicio:
                continue
            if fin and fecha > fin:
                continue
            if fecha_dt.isoweekday() not in dias_semana:
                continue

            dias_esperados += 1
            turno_data = pasadas_por_objetivo[obj_id][fecha]
            tuvo_dia = turno_data['diurno'] > 0
            tuvo_noche = turno_data['nocturno'] > 0

            if tuvo_dia:
                dias_con_dia += 1
            if tuvo_noche:
                dias_con_noche += 1
            if not tuvo_dia and not tuvo_noche:
                dias_sin_control += 1

        if dias_esperados > 0:
            porcentaje = (dias_esperados - dias_sin_control) / dias_esperados * 100
            reporte['objetivos'].append({
                'id': obj_id,
                'nombre': nombre,
                'dias_esperados': dias_esperados,
                'dias_con_dia': dias_con_dia,
                'dias_con_noche': dias_con_noche,
                'dias_sin_control': dias_sin_control,
                'cumplimiento': round(porcentaje, 1)
            })

    conexion.close()
    return reporte


def generar_reporte_diario(fecha: str) -> dict:
    """Genera y retorna el reporte diario de pasadas."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    """, (fecha,))

    pasadas = cursor.fetchall()
    conexion.close()

    return {
        'fecha': fecha,
        'pasadas': [{
            'id': p[0],
            'hora': p[1],
            'turno': p[2],
            'objetivo': p[3],
            'supervisor': p[4]
        } for p in pasadas],
        'total': len(pasadas)
    }