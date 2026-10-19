"""Pruebas del contrato común de datos para los informes exportables."""

import datetime
import sqlite3

import pytest

from services.reportes_unificados.datos import (
    crear_datos_diarios,
    crear_datos_detalle,
    crear_datos_mensuales,
    crear_datos_objetivo,
)
from services.reportes_unificados.modelos import (
    ColumnaReporte,
    MetadatosReporte,
    ReporteDatos,
)


def test_datos_mensuales_conservan_cifras_y_calculan_totales_una_vez():
    reporte = {
        "anio": 2026,
        "mes": 10,
        "cumplimiento_total": 50.0,
        "objetivos": [
            {
                "nombre": "Objetivo A",
                "dias_esperados": 4,
                "dias_con_pasada": 3,
                "dias_sin_pasada": 1,
                "cumplimiento_porcentaje": 75.0,
            },
            {
                "nombre": "Objetivo B",
                "dias_esperados": 2,
                "dias_con_pasada": 0,
                "dias_sin_pasada": 2,
                "cumplimiento_porcentaje": 0.0,
            },
        ],
    }

    datos = crear_datos_mensuales(reporte, {"turno": "Todos"})

    assert datos.filas[0]["cumplimiento"] == 0.75
    assert datos.filas[1]["dias_con_pasada"] == 0
    assert datos.totales == {
        "objetivos": 2,
        "dias_esperados": 6,
        "dias_con_pasada": 3,
        "dias_sin_pasada": 3,
        "cumplimiento_total": 0.5,
    }
    assert datos.metadatos.filtros_aplicados == {"turno": "Todos"}
    assert datos.metadatos.tipo_informe == "mensual"


def test_datos_diarios_preservan_filas_y_total_del_servicio():
    datos = crear_datos_diarios(
        {
            "fecha": "2026-10-31",
            "pasadas": [
                {
                    "hora": "23:50",
                    "turno": "nocturno",
                    "objetivo": "Objetivo Ñ",
                    "supervisor": "Muñoz",
                }
            ],
            "total": 1,
            "cumplimiento_porcentaje": 100.0,
        }
    )

    assert datos.filas[0]["fecha"] == datetime.date(2026, 10, 31)
    assert datos.filas[0]["hora"] == datetime.time(23, 50)
    assert datos.totales["pasadas"] == 1
    assert datos.filas[0]["objetivo"] == "Objetivo Ñ"


def test_datos_por_objetivo_usan_todos_los_totales_del_calculo():
    datos = crear_datos_objetivo(
        2026,
        10,
        {
            "nombre": "Objetivo de prueba",
            "dias": [
                {
                    "fecha": "31/10/2026",
                    "dia_semana": "Sáb",
                    "diurno": "A. Pérez",
                    "nocturno": "✘",
                    "estado": "Solo diurno",
                }
            ],
            "resumen": {
                "dias_esperados": 1,
                "dias_con_dia": 1,
                "dias_con_noche": 0,
                "dias_sin_control": 0,
                "porcentaje": 100.0,
            },
        },
    )

    assert datos.filas[0]["diurno"] == "A. Pérez"
    assert datos.totales["dias_con_noche"] == 0
    assert datos.metadatos.periodo == "2026-10"


def test_reporte_rechaza_ids_de_columna_duplicados():
    metadatos = MetadatosReporte(
        titulo="Prueba",
        tipo_informe="diario",
        periodo="2026-10-31",
        filtros_aplicados={},
        criterio_conteo_turnos="Criterio",
        generado_en=datetime.datetime(2026, 10, 31, 9, 0),
        usuario="Prueba",
        version_aplicacion="1.0",
    )
    columna = ColumnaReporte("fecha", "Fecha", "fecha", "dd/mm/aaaa", 14)

    with pytest.raises(ValueError, match="IDs de columna repetidos"):
        ReporteDatos(metadatos, (columna, columna), ())


def test_detalle_atribuye_madrugada_al_mes_de_turno(
    db_initialized, test_objetivo, test_supervisor
):
    conexion = sqlite3.connect(db_initialized)
    conexion.execute(
        """
        INSERT INTO pasadas
            (fecha, hora, turno, objetivo_id, supervisor_id, fecha_operativa)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-11-01",
            "02:00",
            "nocturno",
            test_objetivo["id"],
            test_supervisor["id"],
            "2026-10-31",
        ),
    )
    conexion.commit()
    conexion.close()

    datos = crear_datos_detalle(
        datetime.date(2026, 10, 31),
        datetime.date(2026, 10, 31),
    )

    assert len(datos.filas) == 1
    assert datos.filas[0]["fecha"] == datetime.date(2026, 10, 31)
    assert datos.totales == {
        "pasadas": 1,
        "pasadas_diurnas": 0,
        "pasadas_nocturnas": 1,
        "por_objetivo": {
            test_objetivo["id"]: {"diurno": 0, "nocturno": 1}
        },
    }
