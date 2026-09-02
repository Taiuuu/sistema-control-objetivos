from datetime import date, time

from services.importador.duplicados import detectar_duplicados_internos
from services.importador.modelos import PasadaNormalizada


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