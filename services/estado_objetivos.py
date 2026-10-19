"""Reglas compartidas para determinar la vigencia efectiva de un objetivo."""

from datetime import date

from models.types import Objetivo


def objetivo_esta_activo(
    objetivo: Objetivo, *, hoy: date | None = None
) -> bool:
    """Indica si el objetivo sigue vigente en la fecha de referencia.

    Una fecha de fin igual a hoy se considera finalizada; la vigencia termina
    al comenzar ese día para evitar mostrar como activo un objetivo que vence hoy.
    """
    if objetivo.es_placeholder:
        return False
    if objetivo.fecha_fin is None:
        return True

    fecha_fin = date.fromisoformat(objetivo.fecha_fin)
    return fecha_fin > (hoy or date.today())
