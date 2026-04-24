# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de reportes y lógica de control diario OPTIMIZADO
# =============================================================================

import datetime
import calendar
from collections import defaultdict
from database.gestor_db import gestor_db
from services.cache import cache_global


def obtener_objetivos_del_dia(fecha: str) -> list:
    """
    Retorna los objetivos que corresponden ser controlados en una fecha dada.
    OPTIMIZADO: Usa gestor_db y cache.
    """
    # Intentar obtener del cache
    cache_key = f"objetivos_dia:{fecha}"
    resultado_cache = cache_global.get(cache_key)
    if resultado_cache is not None:
        return resultado_cache
    
    # Query optimizada
    query = """
        SELECT id, nombre, dias_semana, fecha_inicio, fecha_fin
        FROM objetivos
        WHERE (fecha_inicio IS NULL OR fecha_inicio <= ?)
          AND (fecha_fin IS NULL OR fecha_fin >= ?)
    """
    
    objetivos = gestor_db.ejecutar(query, (fecha, fecha))

    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    dia_semana = fecha_dt.isoweekday()

    resultado = []
    for o in objetivos:
        obj_id = o['id']
        nombre = o['nombre']
        dias_semana_str = o['dias_semana']
        fecha_inicio = o['fecha_inicio']
        fecha_fin = o['fecha_fin']

        if fecha_inicio and fecha < fecha_inicio:
            continue

        if fecha_fin and fecha > fecha_fin:
            continue

        dias = [int(d) for d in dias_semana_str.split(",")]
        if dia_semana not in dias:
            continue

        resultado.append((obj_id, nombre, dias_semana_str))

    # Cachear por 5 minutos
    cache_global.set(cache_key, resultado, 300)
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
    """
    Imprime en consola el reporte de cumplimiento mensual por objetivo.
    OPTIMIZADO: Usa bulk queries.
    """
    total_dias = calendar.monthrange(anio, mes)[1]
    fecha_inicio_mes = f"{anio}-{mes:02d}-01"
    fecha_fin_mes = f"{anio}-{mes:02d}-{total_dias:02d}"

    # Obtener todos los objetivos en una sola query
    objetivos = gestor_db.ejecutar("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos")

    # Obtener todas las pasadas del mes en una sola query
    query_pasadas = """
        SELECT fecha, objetivo_id, turno, COUNT(*) as total
        FROM pasadas
        WHERE fecha BETWEEN ? AND ?
        GROUP BY fecha, objetivo_id, turno
    """
    pasadas_raw = gestor_db.ejecutar(query_pasadas, (fecha_inicio_mes, fecha_fin_mes))

    # Indexar pasadas por objetivo y fecha
    pasadas_por_objetivo = defaultdict(lambda: defaultdict(lambda: {'diurno': 0, 'nocturno': 0}))
    for p in pasadas_raw:
        pasadas_por_objetivo[p['objetivo_id']][p['fecha']][p['turno']] = p['total']

    print(f"\n=== REPORTE MENSUAL {mes}/{anio} ===\n")
    print(f"{'Objetivo':<20} {'Días esperados':<16} {'Días cumplidos':<16} {'Cumplimiento'}")
    print("-" * 70)

    for o in objetivos:
        obj_id = o['id']
        nombre = o['nombre']
        inicio = o['fecha_inicio']
        fin = o['fecha_fin']
        dias_str = o['dias_semana']
        
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
            
            # Usar índice precalculado en lugar de query
            turno_data = pasadas_por_objetivo[obj_id][fecha]
            if turno_data['diurno'] > 0 or turno_data['nocturno'] > 0:
                dias_cumplidos += 1

        if dias_esperados > 0:
            porcentaje = (dias_cumplidos / dias_esperados) * 100
            print(f"{nombre:<20} {dias_esperados:<16} {dias_cumplidos:<16} {porcentaje:.1f}%")


@cache_global.auto_cache(ttl=600)
def generar_reporte_mensual(anio: int, mes: int) -> dict:
    """
    Genera y retorna el reporte de cumplimiento mensual por objetivo.
    OPTIMIZADO: Bulk queries + cache (10 min).
    """
    # Validar parámetros
    if not isinstance(anio, int) or not isinstance(mes, int):
        raise ValueError("Año y mes deben ser números enteros")
    if not (1 <= mes <= 12):
        raise ValueError("Mes debe estar entre 1 y 12")
    if not (2000 <= anio <= 2100):
        raise ValueError("Año debe estar entre 2000 y 2100")

    try:
        total_dias = calendar.monthrange(anio, mes)[1]
        fecha_inicio_mes = f"{anio}-{mes:02d}-01"
        fecha_fin_mes = f"{anio}-{mes:02d}-{total_dias:02d}"

        # Obtener objetivos en una sola query
        objetivos = gestor_db.ejecutar(
            "SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos"
        )

        # Obtener todas las pasadas del mes en una sola query
        query_pasadas = """
            SELECT fecha, objetivo_id, turno, COUNT(*) as total
            FROM pasadas
            WHERE fecha BETWEEN ? AND ?
            GROUP BY fecha, objetivo_id, turno
        """
        pasadas_raw = gestor_db.ejecutar(query_pasadas, (fecha_inicio_mes, fecha_fin_mes))

        # Indexar pasadas por objetivo y fecha
        pasadas_por_objetivo = defaultdict(lambda: defaultdict(lambda: {'diurno': 0, 'nocturno': 0}))
        for p in pasadas_raw:
            pasadas_por_objetivo[p['objetivo_id']][p['fecha']][p['turno']] = p['total']

        reporte = {
            'anio': anio,
            'mes': mes,
            'objetivos': []
        }

        for o in objetivos:
            obj_id = o['id']
            nombre = o['nombre']
            inicio = o['fecha_inicio']
            fin = o['fecha_fin']
            dias_str = o['dias_semana']
            
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
                
                # Usar índice precalculado
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
            else:
                porcentaje = 0.0

            reporte['objetivos'].append({
                'id': obj_id,
                'nombre': nombre,
                'dias_esperados': dias_esperados,
                'dias_con_dia': dias_con_dia,
                'dias_con_noche': dias_con_noche,
                'dias_sin_control': dias_sin_control,
                'cumplimiento': round(porcentaje, 1)
            })

        return reporte

    except Exception as e:
        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        try:
            registrar_accion(get_usuario_id(), f"Error generando reporte mensual {mes}/{anio}: {str(e)}")
        except Exception:
            pass
        raise RuntimeError(f"Error al generar reporte: {str(e)}")


def generar_reporte_diario(fecha: str) -> dict:
    """
    Genera y retorna el reporte diario de pasadas.
    OPTIMIZADO: Usa gestor_db.
    """
    query = """
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    """

    pasadas = gestor_db.ejecutar(query, (fecha,))

    return {
        'fecha': fecha,
        'pasadas': [{
            'id': p['id'],
            'hora': p['hora'],
            'turno': p['turno'],
            'objetivo': p['o.nombre'],
            'supervisor': p['s.nombre']
        } for p in pasadas],
        'total': len(pasadas)
    }