import json
from pathlib import Path

from tests.golden.cargador_excel import cargar_conteos_excel


RAIZ = Path(__file__).parent


def test_conteo_mensual_coincide_con_archivo_dorado_provisional():
    esperado = json.loads(
        (RAIZ / "golden" / "2026-10.json").read_text(encoding="utf-8")
    )
    calculado = cargar_conteos_excel(
        RAIZ / esperado["fuente"],
        esperado["periodo"]["anio"],
        esperado["periodo"]["mes"],
    )

    assert esperado["estado_verificacion"].startswith("SIN VERIFICAR")
    assert calculado == esperado["conteo_por_objetivo"], (
        "Cambió el conteo dorado por objetivo/turno. Revisá las diferencias "
        "contra el Excel y actualizá el JSON solo después de verificarlo a mano."
    )
