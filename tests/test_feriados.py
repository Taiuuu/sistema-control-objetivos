import sqlite3

from services.feriados import (
    eliminar_feriado,
    es_feriado,
    obtener_feriados_mes,
    registrar_feriado,
)
from services.reportes import obtener_objetivos_del_dia


def test_feriados_registran_y_consultan(db_initialized):
    registrar_feriado("2026-01-01", "Año nuevo")

    assert es_feriado("2026-01-01") is True
    assert es_feriado("2026-01-02") is False

    feriados = obtener_feriados_mes(2026, 1)
    assert len(feriados) == 1
    assert feriados[0]["descripcion"] == "Año nuevo"

    eliminar_feriado("2026-01-01")
    assert es_feriado("2026-01-01") is False


def test_objetivos_con_feriados_se_evaluan_en_dias_holiday(db_initialized):
    conn = sqlite3.connect(db_initialized)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO objetivos (nombre, dias_semana) VALUES (?, ?)",
        ("Solo feriados", "8"),
    )
    conn.commit()
    conn.close()

    registrar_feriado("2026-01-01")

    objetivos = obtener_objetivos_del_dia("2026-01-01")

    assert len(objetivos) == 1
    assert objetivos[0][1] == "Solo feriados"
