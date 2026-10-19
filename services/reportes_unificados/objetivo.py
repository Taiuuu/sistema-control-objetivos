"""Cálculo del reporte por objetivo usando las reglas de pasadas compartidas."""

from __future__ import annotations

import calendar
import datetime
import sqlite3
from contextlib import closing
from pathlib import Path

from database.db import DB_PATH
from services.pasadas.calculo_pasadas import (
    fecha_de_turno,
    fecha_hora_desde_fecha_turno,
    indexar_pasadas_por_objetivo,
    normalizar_turno,
    rango_datetime_de_mes,
)
from services.reportes import clasificar_cumplimiento, objetivo_corresponde


def calcular_reporte_objetivo(
    anio: int,
    mes: int,
    objetivo_id: int,
    supervisor_id: int | None = None,
    turno: str | None = None,
    estado_filtro: str = "Todos",
    supervisor_ids: list[int] | None = None,
    turnos: list[str] | None = None,
    equipo_id: int | None = None,
    ruta_db: str | Path = DB_PATH,
) -> dict:
    """Calcula el reporte diario de un objetivo para el mes seleccionado."""
    with closing(sqlite3.connect(ruta_db)) as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT nombre, fecha_inicio, fecha_fin, dias_semana
            FROM objetivos WHERE id = ?
            """,
            (objetivo_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No se encontró el objetivo con id {objetivo_id}")

        nombre, inicio, fin, dias_str = row
        total_dias = calendar.monthrange(anio, mes)[1]
        periodos = cursor.execute(
            """
            SELECT fecha_inicio, fecha_fin FROM objetivo_periodos
            WHERE objetivo_id = ? ORDER BY fecha_inicio
            """,
            (objetivo_id,),
        ).fetchall()
        rango_inicio, rango_fin = rango_datetime_de_mes(
            anio, mes, turno_noche_cruza=True
        )
        fecha_inicio_turno = rango_inicio.date().isoformat()
        fecha_fin_turno = (
            rango_fin.date() - datetime.timedelta(days=1)
        ).isoformat()
        filas_pasadas = cursor.execute(
            """
            SELECT COALESCE(p.fecha_operativa, p.fecha) AS fecha_turno,
                   p.hora, p.turno, p.objetivo_id,
                   p.supervisor_id, s.nombre
            FROM pasadas p
            JOIN supervisores s ON p.supervisor_id = s.id
            WHERE COALESCE(p.fecha_operativa, p.fecha) BETWEEN ? AND ?
              AND p.objetivo_id = ?
              AND (? IS NULL OR p.supervisor_id = ?)
            ORDER BY p.fecha, p.hora, p.turno, s.nombre
            """,
            (
                fecha_inicio_turno,
                fecha_fin_turno,
                objetivo_id,
                supervisor_id,
                supervisor_id,
            ),
        ).fetchall()
        supervisores_seleccionados = (
            set(supervisor_ids) if supervisor_ids is not None else None
        )
        turnos_seleccionados = (
            {normalizar_turno(valor) for valor in turnos}
            if turnos is not None
            else None
        )
        equipos_por_fecha_turno = {}
        if equipo_id is not None:
            equipos = cursor.execute(
                """
                SELECT fecha, turno, supervisor1_id, supervisor2_id, supervisor3_id
                FROM equipos WHERE id = ?
                """,
                (equipo_id,),
            ).fetchall()
            for equipo in equipos:
                equipos_por_fecha_turno[
                    (str(equipo[0]), normalizar_turno(str(equipo[1])))
                ] = {identificador for identificador in equipo[2:] if identificador}

        filas_filtradas = []
        for fila in filas_pasadas:
            fecha_hora = fecha_hora_desde_fecha_turno(fila[0], fila[1], fila[2])
            turno_pasada = normalizar_turno(fila[2])
            fecha_pasada = fecha_de_turno(fecha_hora, turno_pasada).isoformat()
            if (
                supervisores_seleccionados is not None
                and fila[4] not in supervisores_seleccionados
            ):
                continue
            if (
                turnos_seleccionados is not None
                and turno_pasada not in turnos_seleccionados
            ):
                continue
            if equipo_id is not None and fila[4] not in equipos_por_fecha_turno.get(
                (fecha_pasada, turno_pasada), set()
            ):
                continue
            filas_filtradas.append(fila)

        registros_pasadas = [
            {
                "fecha_hora": fecha_hora_desde_fecha_turno(
                    fila[0], fila[1], fila[2]
                ),
                "turno": fila[2],
                "objetivo_id": fila[3],
                "supervisor_id": fila[4],
            }
            for fila in filas_filtradas
        ]
        fechas_pasadas = indexar_pasadas_por_objetivo(
            registros_pasadas, anio, mes, supervisor_id
        ).get(objetivo_id, {"diurno": set(), "nocturno": set()})
        nombres_por_fecha_turno: dict[tuple[datetime.date, str], list[str]] = {}
        for fila in filas_filtradas:
            fecha_hora = fecha_hora_desde_fecha_turno(
                fila[0], fila[1], fila[2]
            )
            turno_pasada = normalizar_turno(fila[2])
            fecha_pasada = fecha_de_turno(fecha_hora, turno_pasada)
            if (fecha_pasada.year, fecha_pasada.month) != (anio, mes):
                continue
            nombres_por_fecha_turno.setdefault(
                (fecha_pasada, turno_pasada), []
            ).append(fila[5])

        nombres_dia = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        dias = []
        dias_esperados = 0
        dias_con_dia = 0
        dias_con_noche = 0
        dias_sin_control = 0
        for dia in range(1, total_dias + 1):
            fecha = f"{anio}-{mes:02d}-{dia:02d}"
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
            activo = any(
                periodo_inicio <= fecha
                and (periodo_fin is None or periodo_fin >= fecha)
                for periodo_inicio, periodo_fin in periodos
            ) if periodos else (
                (not inicio or fecha >= inicio) and (not fin or fecha <= fin)
            )
            if not activo or not objetivo_corresponde(fecha, dias_str):
                continue

            dias_esperados += 1
            fecha_objetivo = fecha_dt.date()
            nombres_diurnos = nombres_por_fecha_turno.get(
                (fecha_objetivo, "diurno"), []
            )
            nombres_nocturnos = nombres_por_fecha_turno.get(
                (fecha_objetivo, "nocturno"), []
            )
            diurno_texto = ", ".join(nombres_diurnos) if nombres_diurnos else "✘"
            nocturno_texto = ", ".join(nombres_nocturnos) if nombres_nocturnos else "✘"
            tuvo_dia = fecha_objetivo in fechas_pasadas["diurno"]
            tuvo_noche = fecha_objetivo in fechas_pasadas["nocturno"]
            dias_con_dia += int(tuvo_dia)
            dias_con_noche += int(tuvo_noche)
            dias_sin_control += int(not tuvo_dia and not tuvo_noche)

            if tuvo_dia and tuvo_noche:
                estado = "Completo"
            elif tuvo_dia:
                estado = "Solo diurno"
            elif tuvo_noche:
                estado = "Solo nocturno"
            else:
                estado = "Sin control"
            if turno == "diurno" and not tuvo_dia:
                continue
            if turno == "nocturno" and not tuvo_noche:
                continue
            if estado_filtro != "Todos" and estado != estado_filtro:
                continue
            dias.append(
                {
                    "fecha": f"{dia:02d}/{mes:02d}/{anio}",
                    "dia_semana": nombres_dia[fecha_dt.weekday()],
                    "diurno": diurno_texto,
                    "nocturno": nocturno_texto,
                    "estado": estado,
                }
            )

    porcentaje = (
        (dias_esperados - dias_sin_control) / dias_esperados * 100
        if dias_esperados
        else 0.0
    )
    return {
        "nombre": nombre,
        "dias": dias,
        "resumen": {
            "dias_esperados": dias_esperados,
            "dias_con_dia": dias_con_dia,
            "dias_con_noche": dias_con_noche,
            "dias_sin_control": dias_sin_control,
            "porcentaje": porcentaje,
            "estado_cumplimiento": clasificar_cumplimiento(porcentaje)[0],
        },
    }
