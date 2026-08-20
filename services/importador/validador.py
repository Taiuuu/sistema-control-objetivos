"""
Validación y clasificación de problemas detectados durante el
análisis: errores críticos (bloquean), advertencias (no bloquean) y
matching pendiente (bloquea hasta que el usuario decide).

Se implementa en la Fase 9.
"""

from __future__ import annotations

from .modelos import PasadaNormalizada, Problema


def validar(pasadas_normalizadas: list[PasadaNormalizada], contexto: dict) -> list[Problema]:
    """
    Recorre las pasadas normalizadas (y el contexto del análisis, ej.
    resultados de matching y de detección de tabla incorrecta) y
    genera la lista completa de Problema, clasificados en:

    - error_critico: datos parciales inconsistentes, objetivo sin
      nombre, hora inválida no corregida, turno inválido.
    - advertencia: hora normalizada, posible pasada en tabla
      incorrecta, hora fuera de rango del turno, inconsistencia entre
      turno de celda y turno de hoja, ambigüedad móvil-supervisor.
    - matching_pendiente: objetivo o supervisor no reconocido.

    Se implementa en la Fase 9.
    """
    pass