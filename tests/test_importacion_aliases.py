from datetime import date, time
from types import SimpleNamespace
import sqlite3

from services.importador.importacion import (
    _aplicar_resoluciones,
    _aplicar_resoluciones_a_pasadas,
    _resolver_nombre_match,
)
from services.importador.modelos import (
    ObjetivoBD,
    PasadaNormalizada,
    Problema,
    ResultadoMatchObjetivo,
)


def test_alias_resuelto_asigna_objetivo_y_persiste_nombre_alternativo():
    conexion = sqlite3.connect(":memory:")
    conexion.executescript(
        """
        CREATE TABLE objetivos (id INTEGER PRIMARY KEY, nombre TEXT);
        CREATE TABLE objetivos_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objetivo_id INTEGER NOT NULL,
            nombre_alias TEXT NOT NULL,
            nombre_alias_normalizado TEXT NOT NULL UNIQUE
        );
        INSERT INTO objetivos VALUES (12, 'OBRA ALBUERA');
        """
    )
    pasada = PasadaNormalizada(
        hoja="15-8 (D)", fila_excel=3, bloque_tabla=1,
        fecha_operativa=date(2026, 8, 15), fecha_calendario=date(2026, 8, 15),
        turno="D", hora=time(8, 0), objetivo_nombre="OBRA ALBUERA (EX MAIPU)",
    )
    problema = Problema(
        tipo="para_revisar", descripcion="sin match",
        hoja=pasada.hoja, fila_excel=pasada.fila_excel,
        objetivo=pasada.objetivo_nombre,
        valor_problema=ResultadoMatchObjetivo(
            nombre_excel=pasada.objetivo_nombre, tipo="no_reconocido"
        ),
    )
    registro = SimpleNamespace(
        tipo="crear_alias", valor_despues="OBRA ALBUERA"
    )

    nombre, objetivo_id = _resolver_nombre_match(
        conexion, problema, registro, None
    )
    analisis = SimpleNamespace(pasadas=[pasada], problemas=[problema])
    _aplicar_resoluciones_a_pasadas(
        analisis,
        {0: {"tipo": "crear_alias", "valor": nombre, "id": objetivo_id}},
    )

    assert pasada.objetivo_id == 12
    alias = conexion.execute(
        "SELECT objetivo_id, nombre_alias_normalizado FROM objetivos_aliases"
    ).fetchone()
    assert alias == (12, "OBRA ALBUERA (EX MAIPU)")


def test_crear_objetivo_usa_fecha_del_analisis(monkeypatch):
    from services.importador import importacion

    conexion = sqlite3.connect(":memory:")
    conexion.execute("CREATE TABLE objetivos (id INTEGER PRIMARY KEY, nombre TEXT)")
    objetivo_fecha = date(2026, 9, 17)
    problema = Problema(
        tipo="para_revisar",
        descripcion="sin match",
        objetivo="OBJETIVO NUEVO",
        valor_problema=ResultadoMatchObjetivo(
            nombre_excel="OBJETIVO NUEVO", tipo="no_reconocido"
        ),
    )
    analisis = SimpleNamespace(
        pasadas=[
            SimpleNamespace(
                objetivo_nombre="OBJETIVO NUEVO", fecha_hoja=objetivo_fecha
            )
        ]
    )
    llamadas = {}

    def crear_objetivo(_conexion, nombre, _usuario, fecha_inicio=None):
        llamadas.update(nombre=nombre, fecha_inicio=fecha_inicio)
        return 41

    monkeypatch.setattr(importacion, "_crear_objetivo", crear_objetivo)
    nombre, objetivo_id = _resolver_nombre_match(
        conexion,
        problema,
        SimpleNamespace(tipo="crear_nuevo", valor_despues="(nuevo) OBJETIVO NUEVO"),
        None,
        analisis=analisis,
    )

    assert (nombre, objetivo_id) == ("OBJETIVO NUEVO", 41)
    assert llamadas == {"nombre": "OBJETIVO NUEVO", "fecha_inicio": objetivo_fecha}


def test_alias_puede_vincular_a_objetivo_nuevo_aunque_se_resuelva_antes(monkeypatch):
    from services.importador import importacion
    from services.importador.resolucion import EstadoResolucion

    conexion = sqlite3.connect(":memory:")
    conexion.executescript(
        """
        CREATE TABLE objetivos (id INTEGER PRIMARY KEY, nombre TEXT);
        CREATE TABLE objetivos_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objetivo_id INTEGER NOT NULL,
            nombre_alias TEXT NOT NULL,
            nombre_alias_normalizado TEXT NOT NULL UNIQUE
        );
        """
    )
    alias_problema = Problema(
        tipo="para_revisar",
        descripcion="alias sin match",
        objetivo="OBRA ARROYO",
        valor_problema=ResultadoMatchObjetivo(
            nombre_excel="OBRA ARROYO", tipo="no_reconocido"
        ),
    )
    nuevo_problema = Problema(
        tipo="para_revisar",
        descripcion="nuevo sin match",
        objetivo="OBRA ARROYO LAS TUNAS",
        valor_problema=ResultadoMatchObjetivo(
            nombre_excel="OBRA ARROYO LAS TUNAS", tipo="no_reconocido"
        ),
    )
    analisis = SimpleNamespace(problemas=[alias_problema, nuevo_problema], pasadas=[])
    resoluciones = EstadoResolucion(usuario="admin")
    resoluciones.registrar_alias(0, None, "OBRA ARROYO", "OBRA ARROYO LAS TUNAS")
    resoluciones.registrar_creacion(
        1, None, "OBRA ARROYO LAS TUNAS", "OBRA ARROYO LAS TUNAS"
    )

    def crear_objetivo(_conexion, nombre, _usuario, fecha_inicio=None):
        return _conexion.execute(
            "INSERT INTO objetivos (nombre) VALUES (?)", (nombre,)
        ).lastrowid

    monkeypatch.setattr(importacion, "_crear_objetivo", crear_objetivo)
    aplicadas = _aplicar_resoluciones(analisis, resoluciones, conexion, "admin")

    assert aplicadas[0]["id"] == aplicadas[1]["id"]
    assert conexion.execute(
        "SELECT nombre_alias FROM objetivos_aliases"
    ).fetchone() == ("OBRA ARROYO",)


def test_crear_objetivo_persiste_con_todas_las_columnas_requeridas():
    from services.importador import importacion

    conexion = sqlite3.connect(":memory:")
    conexion.executescript(
        """
        CREATE TABLE objetivos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            dias_semana TEXT,
            activo INTEGER,
            pendiente_revision INTEGER
        );
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        );
        INSERT INTO usuarios (username) VALUES ('admin');
        CREATE TABLE auditoria (
            id INTEGER PRIMARY KEY,
            fecha TEXT,
            hora TEXT,
            usuario_id INTEGER,
            tipo_operacion TEXT,
            tabla TEXT,
            registro_id INTEGER,
            valores_anteriores TEXT,
            valores_nuevos TEXT,
            detalles TEXT,
            estado TEXT
        );
        """
    )

    objetivo_id = importacion._crear_objetivo(
        conexion,
        "OBJETIVO REGRESION",
        usuario="admin",
    )

    fila = conexion.execute(
        "SELECT nombre, descripcion, fecha_inicio, fecha_fin, dias_semana, activo, pendiente_revision FROM objetivos WHERE id = ?",
        (objetivo_id,),
    ).fetchone()

    assert fila == (
        "OBJETIVO REGRESION",
        "",
        None,
        None,
        "1,2,3,4,5,6,7,8",
        1,
        1,
    )
