"""
modelos.py

Estructuras de datos compartidas por el pipeline de importación
(parser.py, normalizador.py, matcher.py, y las próximas etapas de validación).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
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
# FASE 7 — Pasada normalizada (resultado de unir Fases 4/5/6)
# ---------------------------------------------------------------------------

AccionPasada = Literal["nueva", "actualizar", "omitir"]


@dataclass
class PasadaNormalizada:
    """Una pasada ya lista para persistir, resultado de combinar:

    - Fase 1-3 (parser.py): hoja, fila_excel, bloque_tabla, movil.
    - Fase 4 (normalizador.py): hora ya normalizada a datetime.time.
    - Fase 5 (normalizador.py): turno normalizado ("D"/"N"), fecha_operativa
      y fecha_calendario ya resueltas.
    - Fase 6 (matcher.py): objetivo_id y supervisor_id ya resueltos contra
      el catálogo de la base (o None si a esa altura del pipeline todavía
      no hay match confirmado por el usuario — ver validador.py, Fase 9,
      que marca esos casos como "matching_pendiente").

    `accion` no se completa en esta fase: queda en None hasta que
    duplicados.py (Fase 8) la usa para marcar si la pasada es "nueva",
    hay que "actualizar" una existente, o hay que "omitir"la por ser
    duplicado/ya importada sin cambios.
    """

    # Trazabilidad (de dónde salió esta pasada en el Excel original)
    hoja: str
    fila_excel: int
    bloque_tabla: int

    # Fecha y turno (Fase 5)
    fecha_operativa: date
    fecha_calendario: date
    turno: str  # "D" | "N"

    # Hora (Fase 4)
    hora: time

    # Móvil (dato crudo, no pasa por matching)
    movil: Optional[str] = None

    # Objetivo (Fase 6)
    objetivo_nombre: str = ""
    objetivo_id: Optional[Any] = None

    # Supervisor (Fase 6)
    supervisor_nombre: Optional[str] = None
    supervisor_id: Optional[Any] = None

    # Usado por duplicados.py (Fase 8) para indicar qué hacer con esta
    # pasada al persistir. None hasta que detectar_pasadas_existentes
    # la clasifica.
    accion: Optional[AccionPasada] = None


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