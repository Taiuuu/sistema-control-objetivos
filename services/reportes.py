# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de reportes y lógica de control diario
# =============================================================================

import sqlite3
import datetime
from database.db import DB_PATH


# =============================================================================
# CONTROL DIARIO
# =============================================================================

def obtener_objetivos_del_dia(fecha: str) -> list:
    """
    Retorna los objetivos que corresponden ser controlados en una fecha dada.
    Filtra por:
      - Que la fecha esté dentro del rango de vigencia del objetivo
      - Que el día de la semana coincida con los días de cobertura configurados
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, dias_semana
        FROM objetivos
        WHERE fecha_inicio <= ? AND (fecha_fin >= ? OR fecha_fin IS NULL)
    """, (fecha, fecha))

    objetivos = cursor.fetchall()
    conexion.close()

    # Detectar qué día de la semana es (1=lunes, 7=domingo)
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    dia_semana = fecha_dt.isoweekday()

    return [
        o for o in objetivos
        if dia_semana in [int(d) for d in o[2].split(",")]
    ]


def objetivo_corresponde(fecha: str, dias: str) -> bool:
    """
    Verifica si un objetivo debe controlarse en una fecha dada,
    según sus días de cobertura configurados.
    """
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_dt.isoweekday()
    dias_lista = [int(d) for d in dias.split(",")]
    return dia in dias_lista


# =============================================================================
# REPORTE MENSUAL (consola)
# =============================================================================

def reporte_mensual(anio: int, mes: int) -> None:
    """
    Imprime en consola el reporte de cumplimiento mensual por objetivo.
    Para reportes con interfaz gráfica o exportación usar services/exportar.py
    """
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

            if fecha < inicio:
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