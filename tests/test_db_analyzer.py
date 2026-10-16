import sqlite3

import pytest

from database import db as db_module
from services.db_analyzer import AnalisisBD


@pytest.fixture
def analyzer(tmp_path, monkeypatch):
    database_path = tmp_path / "analysis.db"
    connection = sqlite3.connect(database_path)
    connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
    connection.commit()
    connection.close()

    monkeypatch.setattr(db_module, "DB_PATH", str(database_path))
    return AnalisisBD()


def test_crear_indice_valida_y_crea_el_indice(analyzer):
    assert analyzer.crear_indice("sample", ["value"], "idx_sample_value")

    indices = analyzer.obtener_indices("sample")
    assert any(index["nombre"] == "idx_sample_value" for index in indices)


def test_reporte_maneja_indices_con_expresiones(analyzer):
    connection = sqlite3.connect(db_module.DB_PATH)
    connection.execute(
        "CREATE INDEX idx_sample_lower_value ON sample (lower(value))"
    )
    connection.commit()
    connection.close()

    report = analyzer.generar_reporte()

    assert "(expresión)" in report


@pytest.mark.parametrize(
    ("table", "index"),
    [
        ("sample; DROP TABLE sample;--", "idx_sample_value"),
        ("sample", "idx_sample_value; DROP TABLE sample;--"),
    ],
)
def test_rechaza_identificadores_sql_no_validos_sin_alterar_la_tabla(
    analyzer, table, index
):
    if table != "sample":
        assert not analyzer.crear_indice(table, ["value"], index)
    else:
        assert not analyzer.eliminar_indice(index)

    assert analyzer.obtener_esquema_tabla("sample")
