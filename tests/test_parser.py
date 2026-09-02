from pathlib import Path

import openpyxl

from services.importador.parser import leer_pasadas_crudas


_ENCABEZADOS = ["NO", "OBJETIVO", "TURNO", "MOVIL", "HORA", "SUPERVISOR"]


def test_lee_pasada_de_bloque_siguiente_si_el_primero_esta_vacio(tmp_path: Path):
    ruta = tmp_path / "recorridos.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "1-8 (D)"

    for indice, encabezado in enumerate(_ENCABEZADOS, start=1):
        hoja.cell(row=1, column=indice, value=encabezado)
        hoja.cell(row=1, column=indice + 7, value=encabezado)

    hoja.cell(row=2, column=8, value=1)
    hoja.cell(row=2, column=9, value="Objetivo B")
    hoja.cell(row=2, column=10, value="D")
    hoja.cell(row=2, column=11, value="M-2")
    hoja.cell(row=2, column=12, value="08:00")
    hoja.cell(row=2, column=13, value="Supervisor")
    libro.save(ruta)

    pasadas = leer_pasadas_crudas(str(ruta), "1-8 (D)")

    no_vacias = [pasada for pasada in pasadas if not pasada.esta_vacia()]
    assert len(no_vacias) == 1
    assert no_vacias[0].bloque_tabla == 2
    assert no_vacias[0].objetivo == "Objetivo B"
