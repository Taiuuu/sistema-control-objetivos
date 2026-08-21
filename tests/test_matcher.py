from matcher import matchear_objetivo, matchear_supervisor, inferir_supervisor_faltante

CATALOGO = [
    "BARRIO EL FLORIDO",
    "BARRIO JARDINES DE SARAVI",
    "C. D. I. VILLA DE MAYO",
    "CAM - CENTRO ATENCIÓN MUNICIPAL",
    "CONCEJO DELIBERANTE",
    "CORRALÓN - GARITA",
    "CORRALÓN - PORTÓN",
    "CORTIJO - RUTA 202",
    "CORTIJO - RUTA 8",
    "OBRA CONESA (EX JCP)",
    "OBRA OMBU - GRAND BOURG",
    "OBRA R1003 (P1) MERLO",
    "OBRA R1003 (P2) MERLO",
    "POLI - GRAND BOURG",
    "POLI - A. SOURDEAUX",
    "POLI - NOGUES",
]


def test_match_exacto_case_insensitive_y_trim():
    r = matchear_objetivo("  cortijo - ruta 8  ", CATALOGO)
    assert r.tipo == "exacto"
    assert r.objetivo_exacto.nombre == "CORTIJO - RUTA 8"
    assert r.permite_crear_nuevo is False


def test_match_exacto_con_tildes_distintas():
    r = matchear_objetivo("CAM - CENTRO ATENCION MUNICIPAL", CATALOGO)
    assert r.tipo == "exacto"
    assert r.objetivo_exacto.nombre == "CAM - CENTRO ATENCIÓN MUNICIPAL"


def test_sufijo_desambigua_ruta_202_vs_ruta_8():
    # sin match exacto (falta el guion), pero el sufijo "RUTA 8" debe
    # priorizarse sobre "RUTA 202" aunque el texto completo sea parecido.
    r = matchear_objetivo("CORTIJO RUTA 8", CATALOGO)
    assert r.tipo == "sugerencias"
    assert r.sugerencias[0].objetivo.nombre == "CORTIJO - RUTA 8"
    assert r.sugerencias[0].coincide_sufijo is True
    nombres = [s.objetivo.nombre for s in r.sugerencias]
    assert "CORTIJO - RUTA 202" in nombres  # aparece, pero no primero


def test_sufijo_desambigua_p1_vs_p2():
    r = matchear_objetivo("OBRA R1003 P2 MERLO", CATALOGO)
    assert r.tipo == "sugerencias"
    assert r.sugerencias[0].objetivo.nombre == "OBRA R1003 (P2) MERLO"
    assert r.sugerencias[0].coincide_sufijo is True


def test_maximo_5_sugerencias():
    catalogo_grande = [f"POLI - BARRIO {i}" for i in range(20)]
    r = matchear_objetivo("POLI - BARRIO 1", catalogo_grande)
    assert r.tipo in ("exacto", "sugerencias")
    if r.tipo == "sugerencias":
        assert len(r.sugerencias) <= 5


def test_sin_candidatos_razonables_es_no_reconocido():
    r = matchear_objetivo("ESCUELA N 15", CATALOGO)
    assert r.tipo == "no_reconocido"
    assert r.permite_crear_nuevo is True
    assert r.nombre_sugerido_nuevo == "ESCUELA N 15"
    assert r.fecha_inicio_sugerida is not None


def test_no_escribe_nada_en_la_base():
    # matchear_objetivo es de solo lectura: no debe mutar el catálogo
    # recibido ni el objeto que devuelve depender de writes externos.
    catalogo_copia = list(CATALOGO)
    matchear_objetivo("CORTIJO RUTA 8", catalogo_copia)
    assert catalogo_copia == CATALOGO


def test_acepta_catalogo_como_dicts():
    catalogo_dicts = [{"id": 1, "nombre": "CORTIJO - RUTA 8"}]
    r = matchear_objetivo("cortijo - ruta 8", catalogo_dicts)
    assert r.tipo == "exacto"
    assert r.objetivo_exacto.id == 1


def test_acepta_catalogo_como_tuplas():
    catalogo_tuplas = [(7, "CORTIJO - RUTA 8")]
    r = matchear_objetivo("cortijo - ruta 8", catalogo_tuplas)
    assert r.tipo == "exacto"
    assert r.objetivo_exacto.id == 7


# ---------------------------------------------------------------------------
# Tests de matchear_supervisor
# ---------------------------------------------------------------------------

CATALOGO_SUPERVISORES = [
    "GARCIA, JUAN",
    "LOPEZ, MARIA",
    "MARTINEZ, CARLOS",
    "RODRIGUEZ, ANA",
    "FERNANDEZ, PEDRO",
    "GONZÁLEZ, LUCÍA",
]

def test_supervisor_match_exacto_case_insensitive():
    r = matchear_supervisor("  garcia, juan  ", CATALOGO_SUPERVISORES)
    assert r.tipo == "exacto"
    assert r.supervisor_exacto.nombre == "GARCIA, JUAN"
    assert r.permite_crear_nuevo is False

def test_supervisor_match_exacto_sin_tildes():
    r = matchear_supervisor("GONZALEZ, LUCIA", CATALOGO_SUPERVISORES)
    assert r.tipo == "exacto"
    assert r.supervisor_exacto.nombre == "GONZÁLEZ, LUCÍA"

def test_supervisor_match_exacto_orden_invertido():
    """'JUAN GARCIA' debe matchear exacto con 'GARCIA, JUAN' (mismos tokens)."""
    r = matchear_supervisor("JUAN GARCIA", CATALOGO_SUPERVISORES)
    assert r.tipo == "exacto"
    assert r.supervisor_exacto.nombre == "GARCIA, JUAN"

def test_supervisor_sugerencias_por_similitud():
    # "GARCIA, JOSE" no es exacto pero se parece a "GARCIA, JUAN"
    r = matchear_supervisor("GARCIA, JOSE", CATALOGO_SUPERVISORES)
    assert r.tipo == "sugerencias"
    assert len(r.sugerencias) >= 1
    # GARCIA, JUAN debería estar entre las sugerencias (comparten apellido)
    nombres = [s.supervisor.nombre for s in r.sugerencias]
    assert "GARCIA, JUAN" in nombres

def test_supervisor_no_reconocido():
    r = matchear_supervisor("PEREZ, ROBERTO", CATALOGO_SUPERVISORES)
    assert r.tipo in ("sugerencias", "no_reconocido")
    if r.tipo == "no_reconocido":
        assert r.permite_crear_nuevo is True
        assert r.nombre_sugerido_nuevo == "PEREZ, ROBERTO"

def test_supervisor_maximo_5_sugerencias():
    catalogo_grande = [f"SUPERVISOR {i}, NOMBRE {i}" for i in range(20)]
    r = matchear_supervisor("SUPERVISOR 1, NOMBRE 1", catalogo_grande)
    assert r.tipo in ("exacto", "sugerencias")
    if r.tipo == "sugerencias":
        assert len(r.sugerencias) <= 5

def test_supervisor_acepta_catalogo_como_dicts():
    catalogo_dicts = [{"id": 10, "nombre": "GARCIA, JUAN"}]
    r = matchear_supervisor("garcia, juan", catalogo_dicts)
    assert r.tipo == "exacto"
    assert r.supervisor_exacto.id == 10

def test_supervisor_acepta_catalogo_como_tuplas():
    catalogo_tuplas = [(5, "GARCIA, JUAN")]
    r = matchear_supervisor("garcia, juan", catalogo_tuplas)
    assert r.tipo == "exacto"
    assert r.supervisor_exacto.id == 5

def test_supervisor_no_muta_catalogo():
    catalogo_copia = list(CATALOGO_SUPERVISORES)
    matchear_supervisor("GARCIA, JOSE", catalogo_copia)
    assert catalogo_copia == CATALOGO_SUPERVISORES

# ---------------------------------------------------------------------------
# Tests de inferir_supervisor_faltante
# ---------------------------------------------------------------------------

def test_inferir_lista_forward_pass():
    """El supervisor se propaga hacia adelante en la lista."""
    pasadas = [
        {"supervisor": "GARCIA"},
        {"supervisor": None},
        {"supervisor": ""},
        {"supervisor": "LOPEZ"},
        {"supervisor": None},
    ]
    resultado = inferir_supervisor_faltante(pasadas)
    assert resultado[0]["supervisor"] == "GARCIA"
    assert resultado[1]["supervisor"] == "GARCIA"
    assert resultado[2]["supervisor"] == "GARCIA"
    assert resultado[3]["supervisor"] == "LOPEZ"
    assert resultado[4]["supervisor"] == "LOPEZ"

def test_inferir_lista_backward_pass():
    """Las pasadas iniciales sin supervisor se rellenan con el primero encontrado."""
    pasadas = [
        {"supervisor": None},
        {"supervisor": ""},
        {"supervisor": "MARTINEZ"},
        {"supervisor": None},
    ]
    resultado = inferir_supervisor_faltante(pasadas)
    assert resultado[0]["supervisor"] == "MARTINEZ"
    assert resultado[1]["supervisor"] == "MARTINEZ"
    assert resultado[2]["supervisor"] == "MARTINEZ"
    assert resultado[3]["supervisor"] == "MARTINEZ"

def test_inferir_lista_vacia():
    resultado = inferir_supervisor_faltante([])
    assert resultado == []

def test_inferir_lista_todos_vacios():
    """Si ninguna pasada tiene supervisor, no se puede inferir nada."""
    pasadas = [
        {"supervisor": None},
        {"supervisor": ""},
        {"supervisor": "  "},
    ]
    resultado = inferir_supervisor_faltante(pasadas)
    # No hay supervisor que propagar, quedan como estaban
    assert resultado[0]["supervisor"] is None
    assert resultado[1]["supervisor"] == ""
    assert resultado[2]["supervisor"] == "  "

def test_inferir_lista_con_objetos():
    """Funciona con objetos que tienen atributo .supervisor (ej. PasadaCruda)."""
    from dataclasses import dataclass

    @dataclass
    class FakePasada:
        supervisor: str = None

    pasadas = [FakePasada(), FakePasada(supervisor="RODRIGUEZ"), FakePasada()]
    resultado = inferir_supervisor_faltante(pasadas)
    assert resultado[0].supervisor == "RODRIGUEZ"  # backward
    assert resultado[1].supervisor == "RODRIGUEZ"
    assert resultado[2].supervisor == "RODRIGUEZ"  # forward

def test_inferir_valor_puntual_presente():
    assert inferir_supervisor_faltante("GARCIA") == "GARCIA"

def test_inferir_valor_puntual_con_espacios():
    assert inferir_supervisor_faltante("  GARCIA  ") == "GARCIA"

def test_inferir_valor_puntual_vacio_usa_anterior():
    assert inferir_supervisor_faltante(None, supervisor_anterior="LOPEZ") == "LOPEZ"
    assert inferir_supervisor_faltante("", supervisor_anterior="LOPEZ") == "LOPEZ"

def test_inferir_valor_puntual_vacio_usa_siguiente():
    assert inferir_supervisor_faltante(None, supervisor_siguiente="MARTINEZ") == "MARTINEZ"

def test_inferir_valor_puntual_prioridad_anterior_sobre_siguiente():
    resultado = inferir_supervisor_faltante(
        None, supervisor_anterior="LOPEZ", supervisor_siguiente="MARTINEZ"
    )
    assert resultado == "LOPEZ"

def test_inferir_valor_puntual_todo_vacio():
    assert inferir_supervisor_faltante(None) is None
    assert inferir_supervisor_faltante("") is None
    assert inferir_supervisor_faltante("   ") is None

if __name__ == "__main__":
    import sys

    tests = [(n, f) for n, f in globals().items() if n.startswith("test_")]
    fallidos = 0
    for nombre, funcion in tests:
        try:
            funcion()
            print(f"OK   {nombre}")
        except AssertionError as e:
            fallidos += 1
            print(f"FAIL {nombre}: {e}")
    print()
    print(f"{len(tests) - fallidos}/{len(tests)} tests pasaron")
    sys.exit(1 if fallidos else 0)