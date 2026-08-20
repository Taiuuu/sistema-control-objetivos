"""
Detección de duplicados dentro del propio Excel y de pasadas que ya
existen en la base de datos (idempotencia de la importación).

Se implementa en la Fase 8.
"""

from __future__ import annotations

from .modelos import PasadaNormalizada


def detectar_duplicados_internos(
    pasadas: list[PasadaNormalizada],
) -> tuple[list[PasadaNormalizada], list[PasadaNormalizada]]:
    """
    Agrupa pasadas por (fecha_operativa, turno, objetivo_id, hora).
    Si dentro de un grupo todas comparten el mismo supervisor, es un
    duplicado real y se conserva una sola. Si hay supervisores
    distintos, no es duplicado (dos móviles pasaron a la misma hora).

    Devuelve (pasadas_finales, descartadas_por_duplicado).

    Se implementa en la Fase 8.
    """
    pass


def detectar_pasadas_existentes(
    pasadas: list[PasadaNormalizada], conexion_bd, forzar_sobrescritura: bool = False
) -> tuple[list[PasadaNormalizada], list[PasadaNormalizada]]:
    """
    Consulta la base de datos para separar las pasadas que son nuevas
    de las que ya existen, usando como clave de identidad:
    fecha_operativa + turno + objetivo_id + hora (sin supervisor).

    Si forzar_sobrescritura=True, las que ya existen pero difieren en
    campos secundarios (ej. supervisor) se marcan para actualizar en
    vez de omitirse.

    Devuelve (pasadas_nuevas, pasadas_ya_existentes).

    Se implementa en la Fase 8.
    """
    pass