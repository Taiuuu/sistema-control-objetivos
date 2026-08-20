"""
Confirmación e importación transaccional a la base de datos, más el
registro de auditoría correspondiente.

Se implementa en la Fase 13 (transacción) y Fase 14 (auditoría).
"""

from __future__ import annotations

from .modelos import ResultadoAnalisis


def confirmar_importacion_completa(analisis: ResultadoAnalisis, resoluciones, usuario, conexion_bd) -> dict:
    """
    Ejecuta la importación real dentro de una única transacción:
    inserta las pasadas nuevas, crea los objetivos/supervisores nuevos
    decididos por el usuario, actualiza lo que corresponda sobrescribir,
    y registra todo en auditoría. Si algo falla, rollback completo.

    Esta es la función que expone __init__.py como
    `confirmar_importacion`.

    Se implementa en la Fase 13.
    """
    pass


def registrar_auditoria(evento: dict, conexion_bd) -> None:
    """
    Registra un evento de auditoría (corrección manual, alta de
    objetivo/supervisor desde importación, resumen de importación
    completa, o sobrescritura de un valor existente).

    Se implementa en la Fase 14.
    """
    pass