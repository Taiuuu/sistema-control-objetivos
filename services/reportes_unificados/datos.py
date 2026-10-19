"""Adaptadores de los reportes de negocio al objeto único de exportación."""

from __future__ import annotations

import datetime
from contextlib import closing
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.reportes_unificados.modelos import (
    ColumnaReporte,
    MetadatosReporte,
    ReporteDatos,
)
from services.pasadas.calculo_pasadas import (
    contar_pasadas_por_objetivo_en_fecha,
    fecha_de_turno,
    fecha_hora_desde_fecha_turno,
    normalizar_turno,
)

CRITERIO_CONTEO = (
    "Una o más pasadas en la fecha operativa cuentan como un día cubierto; "
    "el detalle conserva cada pasada registrada. El conteo no implica una "
    "expectativa por turno."
)

COLUMNAS_MENSUALES = (
    ColumnaReporte("objetivo", "Objetivo", "texto", None, 34),
    ColumnaReporte("dias_esperados", "Días esperados", "entero", "0", 16, "centro"),
    ColumnaReporte("dias_con_pasada", "Días con pasada", "entero", "0", 16, "centro"),
    ColumnaReporte("dias_sin_pasada", "Días sin pasada", "entero", "0", 16, "centro"),
    ColumnaReporte("pasadas_diurnas", "Pasadas DIA", "entero", "0", 13, "centro"),
    ColumnaReporte("pasadas_nocturnas", "Pasadas NOCHE", "entero", "0", 14, "centro"),
    ColumnaReporte("pasadas_totales", "Total de pasadas", "entero", "0", 15, "centro"),
    ColumnaReporte("cumplimiento", "Cumplimiento", "porcentaje", "0.0%", 16, "centro"),
    ColumnaReporte("estado", "Estado", "texto", None, 18),
)

COLUMNAS_DIARIAS = (
    ColumnaReporte("fecha", "Fecha", "fecha", "dd/mm/yyyy", 14),
    ColumnaReporte("hora", "Hora", "hora", "hh:mm", 10, "centro"),
    ColumnaReporte("turno", "Turno", "texto", None, 13, "centro"),
    ColumnaReporte("objetivo", "Objetivo", "texto", None, 34),
    ColumnaReporte("supervisor", "Supervisor", "texto", None, 28),
    ColumnaReporte("notas", "Observaciones", "texto_largo", None, 42),
)

COLUMNAS_OBJETIVO = (
    ColumnaReporte("fecha", "Fecha", "fecha_texto", "dd/mm/yyyy", 14),
    ColumnaReporte("dia_semana", "Día", "texto", None, 12, "centro"),
    ColumnaReporte("diurno", "Diurno", "texto", None, 32),
    ColumnaReporte("nocturno", "Nocturno", "texto", None, 32),
    ColumnaReporte("estado", "Estado", "texto", None, 18),
)


def _usuario_actual() -> str:
    """Obtiene el nombre de sesión sin incorporar dependencias de interfaz."""
    from services.sesion import get_usuario_id
    from database import db

    usuario_id = get_usuario_id()
    if usuario_id is None:
        return "No identificado"
    with closing(db.conectar()) as conexion:
        fila = conexion.execute(
            "SELECT username FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
    if fila is None:
        raise LookupError(f"No existe el usuario de sesión {usuario_id}")
    return str(fila[0])


def _version_aplicacion() -> str:
    """Lee la versión distribuida junto con la aplicación."""
    ruta = Path(__file__).resolve().parents[2] / "version.txt"
    return ruta.read_text(encoding="utf-8").strip()


def crear_metadatos(
    tipo_informe: str,
    periodo: str,
    filtros: Mapping[str, Any] | None = None,
    titulo: str | None = None,
) -> MetadatosReporte:
    """Construye metadatos consistentes para una instantánea de datos."""
    etiquetas = {
        "mensual": "Resumen mensual por objetivo",
        "detalle": "Detalle de pasadas",
        "objetivo": "Reporte por objetivo",
        "diario": "Reporte diario",
    }
    if tipo_informe not in etiquetas:
        raise ValueError(f"Tipo de informe no reconocido: {tipo_informe}")
    return MetadatosReporte(
        titulo=titulo or etiquetas[tipo_informe],
        tipo_informe=tipo_informe,
        periodo=periodo,
        filtros_aplicados=dict(filtros or {}),
        criterio_conteo_turnos=CRITERIO_CONTEO,
        generado_en=datetime.datetime.now(),
        usuario=_usuario_actual(),
        version_aplicacion=_version_aplicacion(),
    )


def crear_datos_mensuales(
    reporte: Mapping[str, Any],
    filtros: Mapping[str, Any] | None = None,
    filas_detalle: Sequence[Mapping[str, Any]] = (),
    conteos_por_objetivo: Mapping[int, Mapping[str, int]] | None = None,
    notas: Sequence[Mapping[str, Any]] = (),
    subtotales: Sequence[Mapping[str, Any]] = (),
) -> ReporteDatos:
    """Prepara resumen mensual y totales a partir del cálculo de reportes."""
    anio, mes = int(reporte["anio"]), int(reporte["mes"])
    from services.reportes import clasificar_cumplimiento

    filas_lista = []
    for objetivo in reporte["objetivos"]:
        objetivo_id = objetivo.get("id")
        conteos = (
            (conteos_por_objetivo or {}).get(int(objetivo_id), {})
            if objetivo_id is not None
            else {}
        )
        porcentaje = float(objetivo["cumplimiento_porcentaje"])
        filas_lista.append(
            {
                "id": int(objetivo_id) if objetivo_id is not None else None,
                "objetivo": str(objetivo["nombre"]),
                "dias_esperados": int(objetivo["dias_esperados"]),
                "dias_con_pasada": int(objetivo["dias_con_pasada"]),
                "dias_sin_pasada": int(objetivo["dias_sin_pasada"]),
                "pasadas_diurnas": int(conteos.get("diurno", 0)),
                "pasadas_nocturnas": int(conteos.get("nocturno", 0)),
                "pasadas_totales": sum(conteos.values()),
                "cumplimiento": porcentaje / 100,
                "estado": clasificar_cumplimiento(porcentaje)[0],
            }
        )
    filas = tuple(filas_lista)
    totales = {
        "objetivos": len(filas),
        "dias_esperados": sum(fila["dias_esperados"] for fila in filas),
        "dias_con_pasada": sum(fila["dias_con_pasada"] for fila in filas),
        "dias_sin_pasada": sum(fila["dias_sin_pasada"] for fila in filas),
        "cumplimiento_total": float(reporte["cumplimiento_total"]) / 100,
    }
    if conteos_por_objetivo is not None:
        totales.update(
            {
                "pasadas_diurnas": sum(
                    fila["pasadas_diurnas"] for fila in filas
                ),
                "pasadas_nocturnas": sum(
                    fila["pasadas_nocturnas"] for fila in filas
                ),
                "pasadas": sum(fila["pasadas_totales"] for fila in filas),
            }
        )
    return ReporteDatos(
        metadatos=crear_metadatos(
            "mensual", f"{anio:04d}-{mes:02d}", filtros
        ),
        columnas=(
            COLUMNAS_MENSUALES
            if conteos_por_objetivo is not None
            else tuple(
                columna
                for columna in COLUMNAS_MENSUALES
                if not columna.id.startswith("pasadas_")
            )
        ),
        filas=filas,
        totales=totales,
        columnas_detalle=COLUMNAS_DIARIAS if filas_detalle else (),
        filas_detalle=tuple(dict(fila) for fila in filas_detalle),
        notas=tuple(dict(nota) for nota in notas),
        subtotales=tuple(dict(subtotal) for subtotal in subtotales),
    )


def crear_datos_diarios(
    reporte: Mapping[str, Any],
    filtros: Mapping[str, Any] | None = None,
) -> ReporteDatos:
    """Adapta el reporte diario existente sin volver a contar sus pasadas."""
    fecha = datetime.date.fromisoformat(str(reporte["fecha"]))
    filas = tuple(
        {
            "id": pasada.get("id"),
            "fecha": fecha,
            "hora": datetime.time.fromisoformat(str(pasada["hora"])),
            "turno": str(pasada["turno"]),
            "objetivo": str(pasada["objetivo"]),
            "supervisor": str(pasada["supervisor"]),
            "notas": str(pasada.get("notas", "")),
        }
        for pasada in reporte["pasadas"]
    )
    return ReporteDatos(
        metadatos=crear_metadatos(
            "diario", fecha.strftime("%d/%m/%Y"), filtros
        ),
        columnas=COLUMNAS_DIARIAS,
        filas=filas,
        totales={
            "pasadas": int(reporte["total"]),
            "cumplimiento": float(reporte["cumplimiento_porcentaje"]) / 100,
        },
    )


def crear_datos_objetivo(
    anio: int,
    mes: int,
    reporte: Mapping[str, Any],
    filtros: Mapping[str, Any] | None = None,
) -> ReporteDatos:
    """Adapta el cálculo existente por objetivo y sus totales ya calculados."""
    resumen = reporte["resumen"]
    filas = tuple(dict(dia) for dia in reporte["dias"])
    return ReporteDatos(
        metadatos=crear_metadatos(
            "objetivo",
            f"{anio:04d}-{mes:02d}",
            filtros,
            titulo=f"Reporte por objetivo: {reporte['nombre']}",
        ),
        columnas=COLUMNAS_OBJETIVO,
        filas=filas,
        totales={
            "dias_esperados": int(resumen["dias_esperados"]),
            "dias_con_dia": int(resumen["dias_con_dia"]),
            "dias_con_noche": int(resumen["dias_con_noche"]),
            "dias_sin_control": int(resumen["dias_sin_control"]),
            "cumplimiento": float(resumen["porcentaje"]) / 100,
        },
    )


def crear_datos_detalle(
    fecha_inicio: datetime.date,
    fecha_fin: datetime.date,
    filtros: Mapping[str, Any] | None = None,
    incluir_notas: bool = False,
) -> ReporteDatos:
    """Consulta detalle por fecha operativa y atribuye cada pasada con la regla común."""
    from database import db

    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha final no puede ser anterior a la fecha inicial")

    filtro = dict(filtros or {})
    busqueda = str(filtro.get("busqueda") or "").casefold().strip()
    desde_ampliado = fecha_inicio - datetime.timedelta(days=1)
    hasta_ampliado = fecha_fin + datetime.timedelta(days=1)
    with closing(db.conectar()) as conexion:
        filas_db = conexion.execute(
            """
            SELECT p.id, COALESCE(p.fecha_operativa, p.fecha), p.hora, p.turno,
                   p.objetivo_id, o.nombre, p.supervisor_id, s.nombre, p.notas
            FROM pasadas p
            JOIN objetivos o ON o.id = p.objetivo_id
            JOIN supervisores s ON s.id = p.supervisor_id
            WHERE COALESCE(p.fecha_operativa, p.fecha) BETWEEN ? AND ?
            ORDER BY COALESCE(p.fecha_operativa, p.fecha), p.hora, o.nombre, s.nombre
            """,
            (desde_ampliado.isoformat(), hasta_ampliado.isoformat()),
        ).fetchall()

        filas = []
        registros_por_objetivo: dict[int, list[dict[str, Any]]] = {}
        for fila in filas_db:
            fecha_turno_guardada = str(fila[1])
            fecha_hora = fecha_hora_desde_fecha_turno(
                fecha_turno_guardada, str(fila[2]), str(fila[3])
            )
            fecha_turno = fecha_de_turno(fecha_hora, str(fila[3]))
            turno = normalizar_turno(str(fila[3]))
            if not fecha_inicio <= fecha_turno <= fecha_fin:
                continue
            if busqueda and busqueda not in (
                str(fila[5]).casefold() + " " + str(fila[7]).casefold()
            ):
                continue
            objetivos = filtro.get("objetivo_ids")
            if objetivos is not None and not isinstance(objetivos, (list, tuple, set)):
                objetivos = (objetivos,)
            if objetivos is not None and fila[4] not in objetivos:
                continue
            supervisores = filtro.get("supervisor_ids")
            if supervisores is not None and not isinstance(
                supervisores, (list, tuple, set)
            ):
                supervisores = (supervisores,)
            if supervisores is not None and fila[6] not in supervisores:
                continue
            turnos = filtro.get("turnos")
            if isinstance(turnos, str):
                turnos = (turnos,)
            turnos_normalizados = (
                {
                    normalizar_turno(str(turno_elegido))
                    for turno_elegido in turnos
                }
                if turnos is not None
                else None
            )
            if turnos_normalizados is not None and turno not in turnos_normalizados:
                continue
            if not _pertenece_a_equipo(
                conexion, filtro.get("equipo_id"), fecha_turno, turno, fila[6]
            ):
                continue
            registro = {
                "fecha_hora": fecha_hora,
                "turno": turno,
                "objetivo_id": fila[4],
                "supervisor_id": fila[6],
            }
            registros_por_objetivo.setdefault(int(fila[4]), []).append(registro)
            filas.append(
                {
                    "fecha": fecha_turno,
                    "hora": datetime.time.fromisoformat(str(fila[2])),
                    "turno": turno,
                    "objetivo": str(fila[5]),
                    "supervisor": str(fila[7]),
                    "notas": str(fila[8] or ""),
                }
            )

        total_por_turno = {"diurno": 0, "nocturno": 0}
        conteos_por_objetivo: dict[int, dict[str, int]] = {}
        for objetivo_id, registros in registros_por_objetivo.items():
            conteos_por_objetivo[objetivo_id] = {"diurno": 0, "nocturno": 0}
            for turno in total_por_turno:
                fecha = fecha_inicio
                while fecha <= fecha_fin:
                    conteo_fecha = contar_pasadas_por_objetivo_en_fecha(
                        registros, objetivo_id, fecha, turno
                    )
                    total_por_turno[turno] += conteo_fecha
                    conteos_por_objetivo[objetivo_id][turno] += conteo_fecha
                    fecha += datetime.timedelta(days=1)

        notas = ()
        if incluir_notas:
            notas = tuple(
                {"fecha": datetime.date.fromisoformat(str(fecha)), "nota": str(nota or "")}
                for fecha, nota in conexion.execute(
                    "SELECT fecha, nota FROM notas WHERE fecha BETWEEN ? AND ? ORDER BY fecha",
                    (fecha_inicio.isoformat(), fecha_fin.isoformat()),
                ).fetchall()
            )

    periodo = (
        fecha_inicio.isoformat()
        if fecha_inicio == fecha_fin
        else f"{fecha_inicio.isoformat()} – {fecha_fin.isoformat()}"
    )
    return ReporteDatos(
        metadatos=crear_metadatos("detalle", periodo, filtro),
        columnas=COLUMNAS_DIARIAS,
        filas=tuple(filas),
        totales={
            "pasadas": sum(total_por_turno.values()),
            "pasadas_diurnas": total_por_turno["diurno"],
            "pasadas_nocturnas": total_por_turno["nocturno"],
            "por_objetivo": conteos_por_objetivo,
        },
        notas=notas,
    )


def _pertenece_a_equipo(
    conexion: Any,
    equipo_id: int | None,
    fecha: datetime.date,
    turno: str,
    supervisor_id: int,
) -> bool:
    """Verifica la pertenencia al equipo seleccionado para ese día y turno."""
    if equipo_id is None:
        return True
    filas = conexion.execute(
        """
        SELECT turno, supervisor1_id, supervisor2_id, supervisor3_id
        FROM equipos WHERE id = ? AND fecha = ?
        """,
        (equipo_id, fecha.isoformat()),
    ).fetchall()
    return any(
        normalizar_turno(str(fila[0])) == turno
        and supervisor_id in fila[1:]
        for fila in filas
    )
