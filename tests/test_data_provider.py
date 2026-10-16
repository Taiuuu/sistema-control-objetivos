import sqlite3

from services.data_provider import SQLiteDataProvider


def test_supervisores_usan_fecha_baja_para_determinar_estado(db_initialized):
    conexion = sqlite3.connect(db_initialized)
    conexion.executemany(
        "INSERT INTO supervisores (nombre, fecha_alta, fecha_baja) VALUES (?, ?, ?)",
        [
            ("Supervisor activo", "2026-01-01", None),
            ("Supervisor dado de baja", "2025-01-01", "2026-01-01"),
        ],
    )
    conexion.commit()
    conexion.close()

    provider = SQLiteDataProvider()

    activos = provider.get_supervisores()
    buscados = provider.buscar_supervisores("Supervisor")

    assert [supervisor.nombre for supervisor in activos] == ["Supervisor activo"]
    assert {supervisor.nombre: supervisor.activo for supervisor in buscados} == {
        "Supervisor activo": True,
        "Supervisor dado de baja": False,
    }
