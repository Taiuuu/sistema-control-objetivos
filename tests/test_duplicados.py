from datetime import date, time

from services.importador.duplicados import detectar_duplicados_internos, detectar_pasadas_existentes
from services.importador.importacion import _persistir_pasadas
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


def test_reimportacion_cuenta_solo_las_pasadas_del_excel_actual():
    conexion = sqlite3.connect(":memory:")
    conexion.executescript(
        """
        CREATE TABLE pasadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, hora TEXT, turno TEXT, objetivo_id INTEGER,
            supervisor_id INTEGER, notas TEXT, fecha_operativa TEXT
        );
        CREATE TABLE auditoria (
            fecha TEXT, hora TEXT, usuario_id INTEGER, tipo_operacion TEXT,
            tabla TEXT, registro_id INTEGER, valores_anteriores TEXT,
            valores_nuevos TEXT, detalles TEXT, estado TEXT
        );
        """
    )
    agosto = PasadaNormalizada(
        hoja="15-8 (D)", fila_excel=3, bloque_tabla=1,
        fecha_operativa=date(2026, 8, 15), fecha_calendario=date(2026, 8, 15),
        turno="D", hora=time(8, 0), objetivo_id=5, supervisor_id=9,
        accion="nueva",
    )

    assert _persistir_pasadas(conexion, type("Analisis", (), {"pasadas": [agosto]})(), None) == (1, 0, 0)

    agosto_reimportado = PasadaNormalizada(
        hoja=agosto.hoja, fila_excel=agosto.fila_excel, bloque_tabla=agosto.bloque_tabla,
        fecha_operativa=agosto.fecha_operativa, fecha_calendario=agosto.fecha_calendario,
        turno=agosto.turno, hora=agosto.hora, objetivo_id=agosto.objetivo_id,
        supervisor_id=agosto.supervisor_id, accion="nueva",
    )
    assert _persistir_pasadas(
        conexion, type("Analisis", (), {"pasadas": [agosto_reimportado]})(), None
    ) == (0, 0, 1)


def test_estado_de_una_importacion_no_contamina_otra_fecha():
    conexion = sqlite3.connect(":memory:")
    conexion.execute(
        "CREATE TABLE pasadas (fecha_operativa TEXT, turno TEXT, objetivo_id INTEGER, hora TEXT, supervisor_id INTEGER)"
    )
    julio = _pasada(2, 5)
    julio.fecha_operativa = date(2026, 7, 15)
    agosto = _pasada(3, 5)
    agosto.fecha_operativa = date(2026, 8, 15)
    detectar_pasadas_existentes([julio], conexion)
    nuevas, existentes = detectar_pasadas_existentes([agosto], conexion)
    assert nuevas == [agosto]
    assert existentes == []