from pathlib import Path

import openpyxl

from services.importador.parser import leer_pasadas_crudas
from services.importador.reporte import _construir_pasadas_normalizadas


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


def test_lee_tres_bloques_normaliza_objetivo_y_corta_observaciones(tmp_path: Path):
    ruta = tmp_path / "recorridos.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "17-8 (D)"

    for inicio in (1, 8, 15):
        for indice, encabezado in enumerate(_ENCABEZADOS):
            hoja.cell(row=2, column=inicio + indice, value=encabezado)

    hoja.cell(row=3, column=1, value=1)
    hoja.cell(row=3, column=2, value="OBRA VILLA DE MAYO ")
    hoja.cell(row=3, column=3, value="D")
    hoja.cell(row=3, column=4, value="M-1")
    hoja.cell(row=3, column=5, value="09;11")
    hoja.cell(row=3, column=6, value="Supervisor")
    hoja.cell(row=3, column=10, value="D")
    hoja.cell(row=3, column=11, value="M-2")
    hoja.cell(row=3, column=12, value="10:00")
    hoja.cell(row=3, column=13, value="Supervisor")
    hoja.cell(row=3, column=18, value="D")
    hoja.cell(row=3, column=19, value="M-3")
    hoja.cell(row=3, column=20, value="11:00")
    hoja.cell(row=3, column=21, value="Supervisor")
    hoja.cell(row=4, column=1, value="OBSERVACIONES: otras labores")
    hoja.cell(row=5, column=1, value="texto libre")
    libro.save(ruta)

    pasadas = [
        pasada
        for pasada in leer_pasadas_crudas(str(ruta), hoja.title)
        if not pasada.esta_vacia()
    ]

    assert [pasada.bloque_tabla for pasada in pasadas] == [1, 2, 3]
    assert pasadas[0].objetivo == "OBRA VILLA DE MAYO"


def test_excel_agosto_conserva_todas_las_pasadas_reales():
    ruta = Path(__file__).parents[1] / "CONTROL RECORRIDOS AGOSTO 2026 (2).xlsx"

    pasadas, problemas, hojas, detectadas = _construir_pasadas_normalizadas(
        str(ruta), 2026
    )

    assert hojas == 62
    assert detectadas == 1430
    assert len(pasadas) == 1422
    assert sum("no cargó la hora" in problema.descripcion for problema in problemas) == 8
