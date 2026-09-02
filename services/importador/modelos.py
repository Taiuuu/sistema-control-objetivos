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

NOTA (FASE 10): se agregaron 3 campos a ResultadoAnalisis
(hojas_encontradas, pasadas_detectadas, pasadas_duplicadas) porque el
resumen numérico pedido para reporte.py no tenía dónde guardarse en la
versión anterior del dataclass. Todos tienen default, así que no rompen
código existente que instancie ResultadoAnalisis sin pasarlos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, Literal, Optional


# ============================================================================
# TIPOS GENERALES
# ============================================================================

TipoProblema = Literal["error_critico", "advertencia", "para_revisar"]

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
    """Una pasada lista para ser evaluada y posteriormente persistida."""

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
    """Turno FINAL ya resuelto (fase 5): el turno de la hoja define la
    identidad operativa de la pasada; la celda TURNO puede avisar una
    discrepancia pero no reemplaza al turno de la hoja. Se usa para
    identidad de la pasada (duplicados, persistencia)."""

    # ------------------------------------------------------------------
    # Hora
    # ------------------------------------------------------------------

    hora: time

    # ------------------------------------------------------------------
    # Móvil
    # ------------------------------------------------------------------

    movil: Optional[str] = None

    # ------------------------------------------------------------------
    # NUEVO (FASE 9, ajuste posterior) — turno operativo real
    # ------------------------------------------------------------------

    turno_hoja: Optional[Turno] = None
    """Turno que indica el NOMBRE de la hoja (ej. "12-7 (N)" -> "N"),
    independiente de lo que haya cargado la celda TURNO de esta fila
    puntual. Representa el turno REAL que trabajó la cuadrilla (la
    cuadrilla no cambia de turno fila por fila; una celda TURNO
    contradictoria suele ser un error de tipeo, no un cambio real de
    turno). Se conserva para validador.py y para auditoría, porque el
    turno operativo real no siempre coincide con una celda mal cargada,
    y la hoja sigue siendo la fuente de verdad para la lógica de negocio."""

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
    """Candidato de matching de objetivo."""

    objetivo: ObjetivoBD
    similitud: float
    coincide_sufijo: bool


@dataclass
class ResultadoMatchObjetivo:
    """Resultado de intentar matchear un objetivo del Excel."""

    nombre_excel: str
    tipo: TipoMatch

    objetivo_exacto: Optional[ObjetivoBD] = None

    sugerencias: list[SugerenciaObjetivo] = field(default_factory=list)

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
    """Candidato de matching de supervisor."""

    supervisor: SupervisorBD
    similitud: float
    coincide_sufijo: bool


@dataclass
class ResultadoMatchSupervisor:
    """Resultado de intentar matchear un supervisor del Excel."""

    nombre_excel: str
    tipo: TipoMatch

    supervisor_exacto: Optional[SupervisorBD] = None

    sugerencias: list[SugerenciaSupervisor] = field(default_factory=list)

    permite_crear_nuevo: bool = True

    nombre_sugerido_nuevo: Optional[str] = None


# ============================================================================
# FASE 10 — Resultado completo del análisis
# ============================================================================


@dataclass
class ResultadoAnalisis:
    """Resultado completo del análisis de un archivo Excel."""

    # ------------------------------------------------------------------
    # Datos resultantes del pipeline
    # ------------------------------------------------------------------

    pasadas: list[PasadaNormalizada] = field(default_factory=list)

    problemas: list[Problema] = field(default_factory=list)

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
    # NUEVO (FASE 10) — datos para el resumen impreso de analizar_excel()
    # ------------------------------------------------------------------

    hojas_encontradas: int = 0

    pasadas_detectadas: int = 0
    """Total de bloques NO VACÍOS leídos del Excel (Fase 2-3), antes de
    cualquier normalización/matching/dedupe. Puede ser mayor a
    total_pasadas si alguna pasada no pudo normalizarse (ej. hora
    inválida) y por lo tanto nunca llegó a convertirse en
    PasadaNormalizada."""

    pasadas_sin_hora: int = 0
    """Pasadas detectadas con turno, móvil o supervisor, pero sin hora."""

    pasadas_duplicadas: int = 0
    """Cantidad de pasadas descartadas por duplicados.detectar_duplicados_internos()."""

    # ------------------------------------------------------------------
    # Estado derivado
    # ------------------------------------------------------------------

    @property
    def puede_continuar(self) -> bool:
        return (
            self.errores_criticos == 0
            and self.objetivos_para_revisar == 0
            and self.supervisores_para_revisar == 0
        )

    @property
    def matching_pendiente(self) -> bool:
        return self.objetivos_para_revisar > 0 or self.supervisores_para_revisar > 0

    @property
    def tiene_errores_criticos(self) -> bool:
        return self.errores_criticos > 0

    @property
    def tiene_advertencias(self) -> bool:
        return self.advertencias > 0