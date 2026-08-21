"""
modelos.py

Estructuras de datos compartidas por el pipeline de importación
(parser.py, normalizador.py, matcher.py, y las próximas etapas de validación).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
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

# ---------------------------------------------------------------------------
# FASE 6 — Matching de objetivos (y, con la misma forma, de supervisores)
# ---------------------------------------------------------------------------

TipoMatch = Literal["exacto", "sugerencias", "no_reconocido"]

@dataclass
class ObjetivoBD:
    """Representación mínima de un objetivo ya existente en la base."""

    id: Any
    nombre: str

@dataclass
class SugerenciaObjetivo:
    """Un candidato de match, con su score de similitud."""

    objetivo: ObjetivoBD
    similitud: float  # 0.0 a 1.0, similitud de texto plano (sin el bonus de sufijo)
    coincide_sufijo: bool  # True si además comparte el/los token(s) finales

@dataclass
class ResultadoMatchObjetivo:
    """Resultado de intentar matchear un nombre de objetivo del Excel
    contra el catálogo de objetivos de la base. No escribe nada en la
    base — es sólo la estructura que consume la pantalla de matching.
    """

    nombre_excel: str
    tipo: TipoMatch
    objetivo_exacto: Optional[ObjetivoBD] = None
    sugerencias: list[SugerenciaObjetivo] = field(default_factory=list)
    permite_crear_nuevo: bool = True
    nombre_sugerido_nuevo: Optional[str] = None
    fecha_inicio_sugerida: Optional[date] = None

@dataclass
class SupervisorBD:
    """Representación mínima de un supervisor ya existente en la base."""

    id: Any
    nombre: str

@dataclass
class SugerenciaSupervisor:
    """Un candidato de match para supervisor, con su score de similitud."""

    supervisor: SupervisorBD
    similitud: float  # 0.0 a 1.0, similitud de texto plano (sin el bonus de sufijo)
    coincide_sufijo: bool  # True si además comparte el/los token(s) finales

@dataclass
class ResultadoMatchSupervisor:
    """Resultado de intentar matchear un nombre de supervisor del Excel
    contra el catálogo de supervisores de la base. No escribe nada en la
    base — es sólo la estructura que consume la pantalla de matching.
    """

    nombre_excel: str
    tipo: TipoMatch
    supervisor_exacto: Optional[SupervisorBD] = None
    sugerencias: list[SugerenciaSupervisor] = field(default_factory=list)
    permite_crear_nuevo: bool = True
    nombre_sugerido_nuevo: Optional[str] = None
