"""
modelos.py

Estructuras de datos compartidas por el pipeline de importación.

Este módulo contiene únicamente modelos de datos. No realiza consultas
a la base de datos ni modifica información persistida.

Es utilizado por:
    - parser.py
    - normalizador.py
    - matcher.py
    - duplicados.py
    - validador.py
    - importacion.py
    - __init__.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, Literal, Optional


# ============================================================================
# TIPOS GENERALES
# ============================================================================

TipoProblema = Literal["error_critico", "advertencia"]

TipoMatch = Literal["exacto", "sugerencias", "no_reconocido"]

AccionPasada = Literal["nueva", "actualizar", "omitir"]

Turno = Literal["D", "N"]


# ============================================================================
# FASE 9 — Problemas de validación
# ============================================================================


@dataclass
class Problema:
    """Un error o advertencia detectado durante el pipeline.

    Tipos:

    - ``error_critico``:
        bloquea la importación hasta que el problema sea resuelto.

    - ``advertencia``:
        no bloquea la importación, pero debe mostrarse en la pantalla
        de revisión.

    Los campos ``hoja`` y ``fila_excel`` permiten volver directamente
    al origen del problema dentro del archivo Excel.
    """

    tipo: TipoProblema
    descripcion: str

    hoja: Optional[str] = None
    objetivo: Optional[str] = None
    valor_problema: Optional[Any] = None
    fila_excel: Optional[int] = None


# ============================================================================
# FASE 7 — Pasada normalizada
# ============================================================================


@dataclass
class PasadaNormalizada:
    """Una pasada lista para ser evaluada y posteriormente persistida.

    Es el resultado de combinar las distintas etapas del pipeline:

    - Fases 1-3:
        parser.py
        hoja, fila_excel, bloque_tabla y móvil.

    - Fase 4:
        normalizador.py
        hora normalizada a ``datetime.time``.

    - Fase 5:
        normalizador.py
        turno, fecha_operativa y fecha_calendario.

    - Fase 6:
        matcher.py
        objetivo_id y supervisor_id cuando existe un match confirmado.

    - Fase 8:
        duplicados.py
        ``accion`` indicando qué hacer con la pasada.

    ``accion`` permanece en ``None`` hasta que la etapa de detección
    de duplicados/existencias la clasifique.
    """

    # ------------------------------------------------------------------
    # Trazabilidad
    # ------------------------------------------------------------------

    hoja: str
    fila_excel: int
    bloque_tabla: int

    # ------------------------------------------------------------------
    # Fecha y turno
    # ------------------------------------------------------------------

    fecha_operativa: date
    fecha_calendario: date
    turno: Turno

    # ------------------------------------------------------------------
    # Hora
    # ------------------------------------------------------------------

    hora: time

    # ------------------------------------------------------------------
    # Móvil
    # ------------------------------------------------------------------

    movil: Optional[str] = None

    # ------------------------------------------------------------------
    # Objetivo
    # ------------------------------------------------------------------

    objetivo_nombre: str = ""
    objetivo_id: Optional[Any] = None

    # ------------------------------------------------------------------
    # Supervisor
    # ------------------------------------------------------------------

    supervisor_nombre: Optional[str] = None
    supervisor_id: Optional[Any] = None

    # ------------------------------------------------------------------
    # Acción de persistencia
    # ------------------------------------------------------------------

    accion: Optional[AccionPasada] = None


# ============================================================================
# FASE 6 — Matching de objetivos
# ============================================================================


@dataclass
class ObjetivoBD:
    """Representación mínima de un objetivo existente en la base."""

    id: Any
    nombre: str


@dataclass
class SugerenciaObjetivo:
    """Candidato de matching de objetivo.

    ``similitud`` representa la similitud textual antes de aplicar
    cualquier bonus adicional por coincidencia de sufijo.
    """

    objetivo: ObjetivoBD
    similitud: float
    coincide_sufijo: bool


@dataclass
class ResultadoMatchObjetivo:
    """Resultado de intentar matchear un objetivo del Excel.

    Esta estructura no modifica la base de datos.

    Puede representar:

    - un match exacto;
    - un nombre con sugerencias;
    - un nombre no reconocido.

    La pantalla de revisión puede utilizar este resultado para que
    el usuario confirme una sugerencia o decida crear un objetivo nuevo.
    """

    nombre_excel: str
    tipo: TipoMatch

    objetivo_exacto: Optional[ObjetivoBD] = None

    sugerencias: list[SugerenciaObjetivo] = field(
        default_factory=list
    )

    permite_crear_nuevo: bool = True

    nombre_sugerido_nuevo: Optional[str] = None

    fecha_inicio_sugerida: Optional[date] = None


# ============================================================================
# FASE 6 — Matching de supervisores
# ============================================================================


@dataclass
class SupervisorBD:
    """Representación mínima de un supervisor existente en la base."""

    id: Any
    nombre: str


@dataclass
class SugerenciaSupervisor:
    """Candidato de matching de supervisor.

    ``similitud`` representa la similitud textual antes de aplicar
    cualquier bonus adicional por coincidencia de sufijo.
    """

    supervisor: SupervisorBD
    similitud: float
    coincide_sufijo: bool


@dataclass
class ResultadoMatchSupervisor:
    """Resultado de intentar matchear un supervisor del Excel.

    Esta estructura no modifica la base de datos.

    Puede representar:

    - un match exacto;
    - un nombre con sugerencias;
    - un nombre no reconocido.

    La pantalla de revisión puede utilizar este resultado para que
    el usuario confirme una sugerencia o decida crear un supervisor nuevo.
    """

    nombre_excel: str
    tipo: TipoMatch

    supervisor_exacto: Optional[SupervisorBD] = None

    sugerencias: list[SugerenciaSupervisor] = field(
        default_factory=list
    )

    permite_crear_nuevo: bool = True

    nombre_sugerido_nuevo: Optional[str] = None


# ============================================================================
# FASE 10 — Resultado completo del análisis
# ============================================================================


@dataclass
class ResultadoAnalisis:
    """Resultado completo del análisis de un archivo Excel.

    Este objeto representa el estado del pipeline antes de confirmar
    la importación.

    IMPORTANTE:
        ``ResultadoAnalisis`` no escribe ni modifica la base de datos.

    Su objetivo es entregar a la pantalla de análisis toda la información
    necesaria para mostrar:

    - cantidad de pasadas;
    - pasadas nuevas;
    - pasadas que ya existen;
    - pasadas a omitir;
    - objetivos pendientes de matching;
    - supervisores pendientes de matching;
    - errores críticos;
    - advertencias;
    - y si la importación puede continuar.

    La escritura efectiva en la base queda reservada para
    ``confirmar_importacion()``.
    """

    # ------------------------------------------------------------------
    # Datos resultantes del pipeline
    # ------------------------------------------------------------------

    pasadas: list[PasadaNormalizada] = field(
        default_factory=list
    )

    problemas: list[Problema] = field(
        default_factory=list
    )

    # ------------------------------------------------------------------
    # Resumen de pasadas
    # ------------------------------------------------------------------

    total_pasadas: int = 0

    pasadas_nuevas: int = 0

    pasadas_actualizar: int = 0

    pasadas_omitir: int = 0

    # ------------------------------------------------------------------
    # Matching pendiente
    # ------------------------------------------------------------------

    objetivos_para_revisar: int = 0

    supervisores_para_revisar: int = 0

    # ------------------------------------------------------------------
    # Problemas
    # ------------------------------------------------------------------

    errores_criticos: int = 0

    advertencias: int = 0

    # ------------------------------------------------------------------
    # Estado derivado
    # ------------------------------------------------------------------

    @property
    def puede_continuar(self) -> bool:
        """Indica si la importación puede ser confirmada.

        La importación solamente puede continuar cuando:

        1. no existen errores críticos;
        2. no quedan objetivos pendientes de matching;
        3. no quedan supervisores pendientes de matching.

        Las advertencias no bloquean la importación.
        """

        return (
            self.errores_criticos == 0
            and self.objetivos_para_revisar == 0
            and self.supervisores_para_revisar == 0
        )

    @property
    def matching_pendiente(self) -> bool:
        """Indica si existe algún matching que todavía requiere revisión."""

        return (
            self.objetivos_para_revisar > 0
            or self.supervisores_para_revisar > 0
        )

    @property
    def tiene_errores_criticos(self) -> bool:
        """Indica si existe al menos un error crítico."""

        return self.errores_criticos > 0

    @property
    def tiene_advertencias(self) -> bool:
        """Indica si existe al menos una advertencia."""

        return self.advertencias > 0