"""
Matching de objetivos y supervisores contra la base de datos, e
inferencia de supervisor faltante a partir del móvil.

Se implementa en la Fase 6 (objetivos) y Fase 7 (supervisores +
inferencia por móvil).
"""

from __future__ import annotations

from typing import Optional

from .modelos import PasadaNormalizada


def matchear_objetivo(nombre_excel: str, objetivos_bd: list) -> dict:
    """
    Busca coincidencia de un nombre de objetivo del Excel contra el
    catálogo de objetivos de la base de datos.

    Devuelve un diccionario con el resultado del match: si hay match
    exacto, id del objetivo; si no, una lista de hasta 5 sugerencias
    ordenadas por similitud (nunca se decide automáticamente cuál es
    "el correcto" cuando no hay match exacto).

    Se implementa en la Fase 6.
    """
    pass


def matchear_supervisor(nombre_excel: str, supervisores_bd: list) -> dict:
    """
    Igual que matchear_objetivo pero para supervisores (formato
    "APELLIDO, NOMBRE").

    Se implementa en la Fase 7.
    """
    pass


def inferir_supervisor_faltante(
    pasadas_de_la_hoja: list[PasadaNormalizada],
) -> list[PasadaNormalizada]:
    """
    Completa el supervisor de pasadas que tienen móvil pero no
    supervisor, usando la asociación móvil -> supervisor observada en
    otras pasadas de la misma hoja (mismo día + turno).

    Si un móvil aparece asociado a más de un supervisor distinto
    dentro de la misma hoja, no infiere nada (queda para que lo
    resuelva el usuario como advertencia de ambigüedad).

    Se implementa en la Fase 7.
    """
    pass