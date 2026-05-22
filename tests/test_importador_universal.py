import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.importador_universal import ImportadorUniversal


def test_parsear_nombre_sheet_acepta_barra():
    importador = ImportadorUniversal()

    resultado = importador._parsear_nombre_sheet("27/5 (D)")

    assert resultado == (date.today().replace(month=5, day=27), "diurno")


def test_parsear_hoja_control_recorridos_limpia_texto():
    importador = ImportadorUniversal()
    wb = Workbook()
    ws = wb.active
    ws.title = "27-5 (D)"

    ws["A1"] = "Objetivo"
    ws["B1"] = "Supervisor"
    ws["C1"] = "Hora"
    ws["D1"] = "Veces"
    ws["E1"] = "Notas"

    ws["A2"] = "Revisar\nplaca"
    ws["B2"] = "Juan   Perez"
    ws["C2"] = "08:30"
    ws["D2"] = "1"
    ws["E2"] = "sin observaciones"

    registros = importador._parsear_hoja_control_recorridos(ws, date(2026, 5, 27), "diurno")

    assert len(registros) == 1
    assert registros[0].objetivo == "Revisar placa"
    assert registros[0].supervisor == "Juan Perez"
    assert registros[0].notas == "sin observaciones"
