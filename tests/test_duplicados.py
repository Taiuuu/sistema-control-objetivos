from datetime import date, time

from services.importador.duplicados import detectar_duplicados_internos, detectar_pasadas_existentes
from services.importador.modelos import PasadaNormalizada
import sqlite3


def _pasada(fila_excel: int, objetivo_id):
    return PasadaNormalizada(
        hoja="12-7 (D)",
        fila_excel=fila_excel,
        bloque_tabla=1,
        fecha_operativa=date(2026, 1, 15),
        fecha_calendario=date(2026, 1, 15),
        turno="D",
        hora=time(8, 0),
        objetivo_id=objetivo_id,
    )


def test_detectar_duplicados_acepta_objetivo_none_y_entero():
    pasadas = [
        _pasada(2, 5),
        _pasada(1, None),
    ]

    finales, descartadas = detectar_duplicados_internos(pasadas)

    assert len(finales) == 2
    assert descartadas == []
    assert {pasada.objetivo_id for pasada in finales} == {None, 5}


def test_pasadas_de_meses_distintos_son_nuevas():
    conexion = sqlite3.connect(":memory:")
    conexion.execute("CREATE TABLE pasadas (fecha_operativa TEXT, turno TEXT, objetivo_id INTEGER, hora TEXT, supervisor_id INTEGER)")
    conexion.execute(
        "INSERT INTO pasadas VALUES (?, ?, ?, ?, ?)",
        ("2026-07-15", "D", 5, "08:00:00", 9),
    )
    agosto = PasadaNormalizada(
        hoja="15-8 (D)", fila_excel=3, bloque_tabla=1,
        fecha_operativa=date(2026, 8, 15), fecha_calendario=date(2026, 8, 15),
        turno="D", hora=time(8, 0), objetivo_id=5, supervisor_id=9,
    )

    nuevas, existentes = detectar_pasadas_existentes([agosto], conexion)

    assert nuevas == [agosto]
    assert existentes == []


def test_mismo_dia_mes_y_anio_es_duplicado():
    conexion = sqlite3.connect(":memory:")
    conexion.execute("CREATE TABLE pasadas (fecha_operativa TEXT, turno TEXT, objetivo_id INTEGER, hora TEXT, supervisor_id INTEGER)")
    conexion.execute(
        "INSERT INTO pasadas VALUES (?, ?, ?, ?, ?)",
        ("2026-08-15", "D", 5, "08:00:00", 9),
    )
    agosto = PasadaNormalizada(
        hoja="15-8 (D)", fila_excel=3, bloque_tabla=1,
        fecha_operativa=date(2026, 8, 15), fecha_calendario=date(2026, 8, 15),
        turno="D", hora=time(8, 0), objetivo_id=5, supervisor_id=9,
    )

    nuevas, existentes = detectar_pasadas_existentes([agosto], conexion)

    assert nuevas == []
    assert existentes == [agosto]


def test_mismo_dia_mes_pero_anio_distinto_es_nuevo():
    conexion = sqlite3.connect(":memory:")
    conexion.execute("CREATE TABLE pasadas (fecha_operativa TEXT, turno TEXT, objetivo_id INTEGER, hora TEXT, supervisor_id INTEGER)")
    conexion.execute(
        "INSERT INTO pasadas VALUES (?, ?, ?, ?, ?)",
        ("2025-08-15", "D", 5, "08:00:00", 9),
    )
    pasada = PasadaNormalizada(
        hoja="15-8 (D)", fila_excel=3, bloque_tabla=1,
        fecha_operativa=date(2026, 8, 15), fecha_calendario=date(2026, 8, 15),
        turno="D", hora=time(8, 0), objetivo_id=5, supervisor_id=9,
    )

    nuevas, existentes = detectar_pasadas_existentes([pasada], conexion)

    assert nuevas == [pasada]
    assert existentes == []