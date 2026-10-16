import hashlib
import json
import sqlite3
from pathlib import Path

import openpyxl
import pytest

from database import db as db_module
from services.importador import previsualizar_importacion
from services.importador.importacion import confirmar_importacion
from services.importador.importacion import _resolver_nombre_match
from services.importador.matcher import normalizar_nombre
from services.importador.modelos import (
    Problema,
    ResultadoAnalisis,
    ResultadoMatchObjetivo,
)
from services.importador.normalizador import normalizar_hora
from services.importador import parser
from services.importador.reporte import generar_reporte_detallado
from services.importador.resolucion import EstadoResolucion


FIXTURES = Path(__file__).parent / "fixtures"
ARCHIVO_DORADO = Path(__file__).parents[1] / (
    "CONTROL RECORRIDOS - SEPTIEMBRE - 2026.xlsx"
)


def _crear_conexion() -> sqlite3.Connection:
    conexion = sqlite3.connect(":memory:")
    conexion.executescript(
        """
        CREATE TABLE objetivos (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL);
        CREATE TABLE supervisores (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL);
        CREATE TABLE pasadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            hora TEXT,
            turno TEXT,
            objetivo_id INTEGER,
            supervisor_id INTEGER,
            notas TEXT,
            fecha_operativa TEXT
        );
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, username TEXT UNIQUE);
        CREATE TABLE auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            usuario_id INTEGER,
            tipo_operacion TEXT NOT NULL,
            tabla TEXT,
            registro_id INTEGER,
            valores_anteriores TEXT,
            valores_nuevos TEXT,
            detalles TEXT,
            estado TEXT
        );
        """
    )
    for nombre in ("OBJETIVO A", "OBJETIVO B", "OBJETIVO C", "OBJETIVO D", "OBJETIVO E"):
        conexion.execute("INSERT INTO objetivos (nombre) VALUES (?)", (nombre,))
    conexion.execute("INSERT INTO supervisores (nombre) VALUES ('SUPERVISOR')")
    conexion.execute("INSERT INTO supervisores (nombre) VALUES ('SUPERVISORA')")
    conexion.commit()
    return conexion


def _analizar(nombre: str, conexion: sqlite3.Connection) -> ResultadoAnalisis:
    return previsualizar_importacion(
        str(FIXTURES / nombre),
        2026,
        conexion,
    )


def test_formatos_horarios_mixtos_se_interpretan_sin_cambiar_entrada():
    conexion = _crear_conexion()
    analisis = _analizar("formatos_hora.xlsx", conexion)
    assert {
        pasada.hora.strftime("%H:%M") for pasada in analisis.pasadas
    } == {"08:05", "08:00", "20:05"}
    assert analisis.filas_rechazadas == 0
    for valor, esperado in (
        ("08:05", "08:05"),
        ("08.05", "08:05"),
        ("08;05", "08:05"),
        ("08;05;", "08:05"),
        (8, "08:00"),
        ("8:5", "08:05"),
        ("8:05 PM", "20:05"),
    ):
        hora, _, error = normalizar_hora(valor)
        assert hora.strftime("%H:%M") == esperado
        assert error is None
    assert normalizar_hora("8 AM").hora.strftime("%H:%M") == "08:00"
    conexion.close()


def test_hora_corrupta_se_rechaza_con_fila_y_severidad():
    conexion = _crear_conexion()
    analisis = _analizar("hora_corrupta.xlsx", conexion)

    problema = next(p for p in analisis.problemas if p.tipo == "error_critico")
    assert analisis.pasadas_detectadas == 1
    assert analisis.filas_rechazadas == 1
    assert problema.fila_excel == 2
    assert problema.severidad == "error"
    conexion.close()


def test_cambio_de_mes_se_rechaza_y_concilia():
    conexion = _crear_conexion()
    analisis = previsualizar_importacion(
        str(FIXTURES / "CONTROL RECORRIDOS - OCTUBRE - 2026.xlsx"),
        2026,
        conexion,
    )

    assert analisis.mes_archivo == 10
    assert analisis.pasadas_detectadas == 2
    assert analisis.filas_a_insertar == 1
    assert analisis.filas_rechazadas == 1
    assert (
        analisis.pasadas_detectadas
        == analisis.filas_a_insertar
        + analisis.filas_duplicadas
        + analisis.filas_rechazadas
    )
    assert any("fuera del mes del archivo" in p.descripcion for p in analisis.problemas)
    conexion.close()


def test_importa_filas_validas_y_rechaza_solo_las_fuera_de_mes(monkeypatch, tmp_path):
    from services.importador import importacion

    conexion = _crear_conexion()
    monkeypatch.setattr(importacion, "crear_backup", lambda *args, **kwargs: tmp_path / "backup.db")
    monkeypatch.setattr(importacion, "_exportar_pasadas_seguridad", lambda *args: None)
    analisis = previsualizar_importacion(
        str(FIXTURES / "CONTROL RECORRIDOS - OCTUBRE - 2026.xlsx"),
        2026,
        conexion,
    )

    resultado = confirmar_importacion(
        analisis, EstadoResolucion(usuario="operador"), None, conexion
    )

    assert resultado["filas_leidas"] == 2
    assert resultado["filas_insertadas"] == 1
    assert resultado["filas_duplicadas"] == 0
    assert resultado["filas_rechazadas"] == 1
    assert conexion.execute("SELECT COUNT(*) FROM pasadas").fetchone()[0] == 1
    conexion.close()


def test_mismo_horario_en_objetivos_distintos_es_advertencia_importable():
    conexion = _crear_conexion()
    analisis = _analizar("objetivos_misma_hora.xlsx", conexion)

    problema = next(p for p in analisis.problemas if "misma hora" in p.descripcion)
    assert problema.severidad == "advertencia"
    assert analisis.filas_a_insertar == 2
    assert analisis.filas_rechazadas == 0
    conexion.close()


def test_supervisor_distinto_forma_parte_de_la_clave_natural():
    conexion = _crear_conexion()
    analisis = _analizar("supervisor_distinto.xlsx", conexion)

    assert analisis.filas_a_insertar == 2
    assert analisis.filas_duplicadas == 0
    assert analisis.filas_rechazadas == 0
    conexion.close()


def test_orden_cronologico_dudoso_es_advertencia_no_bloqueante():
    conexion = _crear_conexion()
    analisis = _analizar("orden_cronologico.xlsx", conexion)

    assert any("Orden cronológico dudoso" in p.descripcion for p in analisis.problemas)
    assert analisis.filas_a_insertar == 2
    assert analisis.filas_rechazadas == 0
    conexion.close()


def test_normalizacion_de_nombres_detecta_colision_y_no_adivina():
    conexion = _crear_conexion()
    conexion.execute("INSERT INTO objetivos (nombre) VALUES ('Obra Ámbigua')")
    conexion.execute("INSERT INTO objetivos (nombre) VALUES ('OBRA AMBIGUA')")
    conexion.execute("INSERT INTO supervisores (nombre) VALUES ('José Núñez')")
    conexion.execute("INSERT INTO supervisores (nombre) VALUES ('JOSE NUNEZ')")

    assert normalizar_nombre("  José   Núñez ") == "JOSE NUNEZ"
    analisis = _analizar("ambiguedad.xlsx", conexion)
    pendientes = [p for p in analisis.problemas if p.tipo == "para_revisar"]

    assert len(pendientes) == 2
    assert all(p.severidad == "error" for p in pendientes)
    assert all("ambigua" in p.descripcion.lower() for p in pendientes)
    assert all("ID:" in p.descripcion for p in pendientes)
    assert analisis.filas_rechazadas == 1
    conexion.close()


def test_sugerencia_ambigua_se_resuelve_por_id_sin_elegir_por_nombre():
    conexion = _crear_conexion()
    cursor = conexion.execute(
        "INSERT INTO objetivos (nombre) VALUES ('OBRA AMBIGUA')"
    )
    elegido = cursor.lastrowid
    problema = Problema(
        tipo="para_revisar",
        descripcion="ambigüedad",
        objetivo="Obra Ambigua",
        valor_problema=ResultadoMatchObjetivo(
            nombre_excel="Obra Ambigua",
            tipo="sugerencias",
            ambiguo=True,
        ),
    )
    nombre, objetivo_id = _resolver_nombre_match(
        conexion,
        problema,
        type("Resolucion", (), {
            "valor_despues": f"[ID:{elegido}] OBRA AMBIGUA",
            "tipo": "match_existente",
        })(),
        None,
    )

    assert nombre == "OBRA AMBIGUA"
    assert objetivo_id == elegido
    conexion.close()


@pytest.mark.parametrize(
    ("nombre", "mensaje"),
    [
        ("vacio.xlsx", "está vacío"),
        ("columnas_faltantes.xlsx", "encabezados obligatorios"),
    ],
)
def test_archivo_vacio_o_sin_columnas_se_rechaza_sin_filas(nombre, mensaje):
    conexion = _crear_conexion()
    analisis = _analizar(nombre, conexion)

    assert analisis.pasadas_detectadas == 0
    assert analisis.filas_leidas_ids == []
    assert any(mensaje in p.descripcion for p in analisis.problemas)
    assert (
        analisis.pasadas_detectadas
        == analisis.filas_a_insertar
        + analisis.filas_duplicadas
        + analisis.filas_rechazadas
    )
    conexion.close()


def test_dry_run_no_escribe_en_sqlite_y_exporta_informe_xlsx():
    conexion = _crear_conexion()
    antes = conexion.total_changes
    analisis = _analizar("orden_cronologico.xlsx", conexion)
    contenido = generar_reporte_detallado(analisis)
    libro = openpyxl.load_workbook(__import__("io").BytesIO(contenido), data_only=True)

    assert conexion.total_changes == antes
    assert libro["Problemas"]["A1"].value == "Severidad"
    assert libro["Problemas"]["D2"].value == 2
    libro.close()
    conexion.close()


def test_reimportar_archivo_no_duplica_y_concilia(monkeypatch, tmp_path):
    from services.importador import importacion

    conexion = _crear_conexion()
    monkeypatch.setattr(importacion, "crear_backup", lambda *args, **kwargs: tmp_path / "backup.db")
    monkeypatch.setattr(importacion, "_exportar_pasadas_seguridad", lambda *args: None)
    ruta = str(FIXTURES / "reimportacion.xlsx")
    resoluciones = EstadoResolucion(usuario="operador")

    primera = previsualizar_importacion(ruta, 2026, conexion)
    resultado_primero = confirmar_importacion(primera, resoluciones, None, conexion)
    segunda = previsualizar_importacion(ruta, 2026, conexion)
    resultado_segundo = confirmar_importacion(segunda, resoluciones, None, conexion)

    assert resultado_primero["filas_leidas"] == 1
    assert resultado_primero["filas_insertadas"] == 1
    assert resultado_segundo["filas_insertadas"] == 0
    assert resultado_segundo["filas_duplicadas"] == 1
    assert resultado_segundo["filas_rechazadas"] == 0
    assert conexion.execute("SELECT COUNT(*) FROM pasadas").fetchone()[0] == 1
    assert conexion.execute(
        "SELECT COUNT(*) FROM auditoria WHERE tipo_operacion = 'IMPORTACION_COMPLETA'"
    ).fetchone()[0] == 2
    conexion.close()


def test_error_de_conciliacion_revierte_y_audita_el_fallo(monkeypatch, tmp_path):
    from services.importador import importacion

    conexion = _crear_conexion()
    monkeypatch.setattr(importacion, "crear_backup", lambda *args, **kwargs: tmp_path / "backup.db")
    monkeypatch.setattr(importacion, "_exportar_pasadas_seguridad", lambda *args: None)
    monkeypatch.setattr(importacion, "_persistir_pasadas", lambda *args: (0, 0, 0))
    analisis = _analizar("reimportacion.xlsx", conexion)

    with pytest.raises(RuntimeError, match="conciliación"):
        confirmar_importacion(
            analisis, EstadoResolucion(usuario="operador"), None, conexion
        )

    assert conexion.execute("SELECT COUNT(*) FROM pasadas").fetchone()[0] == 0
    assert conexion.execute(
        "SELECT estado FROM auditoria WHERE tipo_operacion = 'IMPORTACION_COMPLETA'"
    ).fetchone()[0] == "FALLIDO"
    conexion.close()


def test_migracion_archiva_duplicados_y_crea_indice_unico(tmp_path, monkeypatch):
    ruta = tmp_path / "migracion.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(ruta))
    respaldos = []
    monkeypatch.setattr(
        "services.backup.crear_backup",
        lambda motivo, conexion_origen=None: respaldos.append(motivo),
    )
    conexion = sqlite3.connect(ruta)
    conexion.executescript(
        """
        CREATE TABLE pasadas (
            id INTEGER PRIMARY KEY,
            fecha TEXT,
            hora TEXT,
            turno TEXT,
            objetivo_id INTEGER,
            supervisor_id INTEGER,
            notas TEXT,
            fecha_operativa TEXT
        );
        INSERT INTO pasadas VALUES
            (1, '2026-10-01', '08:00:00', 'diurno', 4, 8, '', '2026-10-01'),
            (2, '2026-10-01', '08:00', 'diurno', 4, 8, 'duplicada', '2026-10-01');
        """
    )
    conexion.close()

    db_module.crear_base_datos()
    conexion = sqlite3.connect(ruta)
    assert respaldos == ["pre_migracion"]
    assert conexion.execute("SELECT id FROM pasadas").fetchall() == [(1,)]
    archivo = conexion.execute(
        "SELECT pasada_original_id, pasada_conservada_id FROM pasadas_duplicados_migracion"
    ).fetchone()
    assert archivo == (2, 1)
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id, fecha_operativa)
            VALUES ('2026-10-01', '08:00', 'diurno', 4, 8, '2026-10-01')
            """
        )
    conexion.close()


def test_caso_dorado_septiembre_2026_coincide_con_el_excel_real():
    """Fija el resultado del libro real sin asumir un catálogo permanente."""
    assert ARCHIVO_DORADO.is_file()
    crudas = [
        pasada
        for hoja in parser.leer_hojas_de_datos(str(ARCHIVO_DORADO))
        for pasada in parser.leer_pasadas_crudas(str(ARCHIVO_DORADO), hoja)
        if not pasada.esta_vacia()
    ]
    parser.liberar_workbook(str(ARCHIVO_DORADO))

    conexion = _crear_conexion()
    conexion.execute("DELETE FROM objetivos")
    conexion.execute("DELETE FROM supervisores")
    objetivos = sorted(
        {
            pasada.objetivo.strip()
            for pasada in crudas
            if pasada.objetivo and pasada.objetivo.strip()
        }
    )
    supervisores = sorted(
        {
            pasada.supervisor.strip()
            for pasada in crudas
            if pasada.supervisor and pasada.supervisor.strip()
        }
    )
    conexion.executemany(
        "INSERT INTO objetivos (nombre) VALUES (?)",
        ((nombre,) for nombre in objetivos),
    )
    conexion.executemany(
        "INSERT INTO supervisores (nombre) VALUES (?)",
        ((nombre,) for nombre in supervisores),
    )
    conexion.commit()
    analisis = previsualizar_importacion(str(ARCHIVO_DORADO), 2026, conexion)
    pasadas = [
        {
            "fecha_operativa": pasada.fecha_operativa.isoformat(),
            "fecha_calendario": pasada.fecha_calendario.isoformat(),
            "turno": pasada.turno,
            "hora": pasada.hora.strftime("%H:%M"),
            "objetivo": pasada.objetivo_nombre,
            "supervisor": pasada.supervisor_nombre,
        }
        for pasada in analisis.pasadas
    ]
    contenido = json.dumps(
        pasadas, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    assert analisis.hojas_encontradas == 60
    assert analisis.mes_archivo == 9
    assert analisis.pasadas_detectadas == 1572
    assert analisis.filas_a_insertar == 1505
    assert analisis.filas_duplicadas == 3
    assert analisis.filas_rechazadas == 64
    assert analisis.advertencias == 943
    assert analisis.errores_criticos == 5
    assert (
        hashlib.sha256(contenido).hexdigest()
        == "b21c36c920f863f1c62866870ea5a21b35ffa823b3f81e96fa25fd61fcd949d5"
    )
    assert (
        analisis.pasadas_detectadas
        == analisis.filas_a_insertar
        + analisis.filas_duplicadas
        + analisis.filas_rechazadas
    )
    conexion.close()
