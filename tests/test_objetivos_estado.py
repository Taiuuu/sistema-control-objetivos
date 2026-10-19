from datetime import date

import pytest

from models.types import Objetivo
from services.estado_objetivos import objetivo_esta_activo


@pytest.mark.parametrize(
    ("fecha_fin", "esperado"),
    (
        ("2026-08-31", False),
        ("2026-09-01", False),
        (None, True),
        ("2026-09-02", True),
    ),
)
def test_vigencia_de_objetivo_segun_fecha_fin(fecha_fin, esperado):
    objetivo = Objetivo(
        nombre="Objetivo de prueba",
        fecha_inicio="2026-08-01",
        fecha_fin=fecha_fin,
        dias_semana="1,2,3,4,5",
    )

    assert objetivo_esta_activo(objetivo, hoy=date(2026, 9, 1)) is esperado


def test_objetivo_placeholder_nunca_es_vigente():
    objetivo = Objetivo(
        nombre="Ficha incompleta",
        fecha_inicio=None,
        fecha_fin=None,
        dias_semana="",
        es_placeholder=True,
    )

    assert not objetivo_esta_activo(objetivo, hoy=date(2026, 9, 1))
