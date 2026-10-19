"""Construcción de informes unificados a partir de filtros de exportación."""

from __future__ import annotations

import calendar
from dataclasses import replace
from datetime import date
from typing import Any, Mapping

from services.reportes_unificados.datos import (
    crear_datos_detalle,
    crear_datos_mensuales,
)
from services.reportes_unificados.modelos import ReporteDatos


def crear_datos_para_exportar(seleccion: Mapping[str, Any]) -> ReporteDatos:
    """Genera una instantánea compartida aplicando período y filtros seleccionados."""
    inicio = _fecha(seleccion["fecha_inicio"])
    fin = _fecha(seleccion["fecha_fin"])
    if fin < inicio:
        raise ValueError("La fecha final no puede ser anterior a la inicial")

    pantalla = dict(seleccion.get("filtros_pantalla") or {})
    filtros = {
        **pantalla,
        "objetivo_ids": seleccion.get("objetivo_ids"),
        "supervisor_ids": seleccion.get("supervisor_ids"),
        "turnos": seleccion.get("turnos"),
        "equipo_id": seleccion.get("equipo_id"),
        "agrupacion": seleccion.get("agrupacion", "ninguna"),
    }
    filtros = {
        clave: valor
        for clave, valor in filtros.items()
        if valor is not None and valor != ""
    }
    tipo = str(seleccion["tipo_informe"])
    incluir_notas = bool(seleccion.get("incluir_notas", False))

    if tipo in {"detalle", "diario"}:
        datos = crear_datos_detalle(inicio, fin, filtros, incluir_notas)
        datos = _agrupar_detalle(datos, str(seleccion.get("agrupacion", "ninguna")))
        if tipo == "diario":
            metadatos = replace(
                datos.metadatos,
                tipo_informe="diario",
                titulo="Reporte diario",
            )
            datos = replace(datos, metadatos=metadatos)
        return datos

    if tipo != "mensual":
        raise ValueError(f"No se puede crear el informe solicitado: {tipo}")
    ultimo_dia = date(
        inicio.year,
        inicio.month,
        calendar.monthrange(inicio.year, inicio.month)[1],
    )
    if inicio != inicio.replace(day=1) or fin != ultimo_dia:
        raise ValueError(
            "El resumen mensual requiere el mes calendario completo."
        )

    from services.reportes import generar_reporte_mensual

    estado = str(pantalla.get("estado") or "Todos")
    reporte = generar_reporte_mensual(
        inicio.year,
        inicio.month,
        estado=estado,
        supervisor_ids=_ids(filtros.get("supervisor_ids")),
        turnos=_turnos(filtros.get("turnos")),
        objetivo_ids=_ids(filtros.get("objetivo_ids")),
        equipo_id=filtros.get("equipo_id"),
    )
    detalle = crear_datos_detalle(
        inicio,
        fin,
        filtros,
        incluir_notas,
    )
    detalle = _agrupar_detalle(
        detalle,
        str(seleccion.get("agrupacion", "ninguna")),
    )
    return crear_datos_mensuales(
        reporte,
        filtros,
        filas_detalle=detalle.filas,
        conteos_por_objetivo=detalle.totales["por_objetivo"],
        notas=detalle.notas,
        subtotales=detalle.subtotales,
    )


def _agrupar_detalle(datos: ReporteDatos, agrupacion: str) -> ReporteDatos:
    """Ordena el detalle y calcula una vez los subtotales por dimensión."""
    claves = {
        "objetivo": "objetivo",
        "supervisor": "supervisor",
        "dia": "fecha",
    }
    clave = claves.get(agrupacion)
    if clave is None:
        if agrupacion != "ninguna":
            raise ValueError(f"Agrupación no reconocida: {agrupacion}")
        return datos
    filas = tuple(sorted(datos.filas, key=lambda fila: (fila.get(clave), fila.get("hora"))))
    cantidades: dict[Any, int] = {}
    for fila in filas:
        valor = fila.get(clave)
        cantidades[valor] = cantidades.get(valor, 0) + 1
    subtotales = tuple(
        {
            "agrupacion": agrupacion,
            "valor": valor,
            "etiqueta": valor.strftime("%d/%m/%Y")
            if isinstance(valor, date)
            else str(valor or "Sin dato"),
            "pasadas": cantidad,
        }
        for valor, cantidad in cantidades.items()
    )
    return replace(datos, filas=filas, subtotales=subtotales)


def _fecha(valor: Any) -> date:
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor))


def _ids(valor: Any) -> list[int] | None:
    if valor is None:
        return None
    return [int(identificador) for identificador in valor]


def _turnos(valor: Any) -> list[str] | None:
    if valor is None:
        return None
    return [str(turno) for turno in valor]
