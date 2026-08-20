"""
modelos.py

Estructuras de datos compartidas por el pipeline de importación
(parser.py, normalizador.py, y las próximas etapas de validación).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

TipoProblema = Literal["error_critico", "advertencia"]


@dataclass
class Problema:
    """Un error o advertencia detectado durante el parseo/normalización.

    - error_critico: bloquea el import hasta que se resuelva.
    - advertencia: no bloquea, pero se muestra en la pantalla de revisión.
    """

    tipo: TipoProblema
    descripcion: str
    hoja: Optional[str] = None
    objetivo: Optional[str] = None
    valor_problema: Optional[Any] = None
    fila_excel: Optional[int] = None