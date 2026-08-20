"""
Lectura cruda del Excel de control de recorridos.

Responsabilidad exclusiva de este archivo: leer el .xlsx tal cual está
y devolver estructuras de datos crudas (PasadaCruda), sin normalizar
horas, turnos ni hacer matching de objetivos/supervisores. Eso es
trabajo de normalizador.py y matcher.py.

Se implementa en la Fase 2 y Fase 3.
"""

from __future__ import annotations

from datetime import date

from .modelos import PasadaCruda


def leer_hojas_de_datos(path) -> list[str]:
    """
    Devuelve los nombres de las hojas que contienen pasadas,
    excluyendo la hoja de catálogo/listado (turnos, móviles,
    supervisores de referencia).

    Se implementa en la Fase 2.
    """
    pass


def leer_pasadas_crudas(path, nombre_hoja: str) -> list[PasadaCruda]:
    """
    Lee una hoja de datos y devuelve la lista de PasadaCruda: una por
    cada bloque de tabla (1, 2 o 3) y por cada fila de objetivo,
    incluyendo las vacías (el filtrado de vacías es responsabilidad de
    fases posteriores).

    Se implementa en la Fase 2.
    """
    pass


def parsear_nombre_hoja(nombre_hoja: str, anio: int) -> tuple[date, str]:
    """
    Parsea el nombre de una hoja (ej. "1-7 (D)", "6-7(N)") a una fecha
    y un turno normalizado ("D" o "N").

    Se implementa en la Fase 3.
    """
    pass