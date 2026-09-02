from datetime import date, time
from types import SimpleNamespace
import sqlite3

from services.importador.importacion import (
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
