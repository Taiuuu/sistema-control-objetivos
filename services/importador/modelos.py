"""
Modelos de datos base usados en todo el pipeline del importador universal.

Estos son los "contratos" entre fases: parser.py produce PasadaCruda,
normalizador.py + matcher.py transforman eso en PasadaNormalizada,
validador.py + duplicados.py producen Problema, y todo se junta en
ResultadoAnalisis para la pantalla de análisis (Fase 10-11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Datos crudos (tal cual salen del Excel, sin normalizar)
# ---------------------------------------------------------------------------

@dataclass
class PasadaCruda:
    """
    Representa una celda de "pasada" leída directamente del Excel,
    antes de cualquier normalización o validación.

    Se genera una por cada uno de los 3 bloques de tabla (bloque_tabla
    1, 2 o 3), por cada fila de objetivo, en cada hoja. Puede estar
    "vacía" (sin turno/movil/hora/supervisor) si esa pasada no ocurrió.
    """

    hoja: str
    bloque_tabla: Literal[1, 2, 3]
    objetivo_texto: str
    turno_texto: Optional[str]
    movil_texto: Optional[str]
    hora_texto: Optional[object]  # puede ser str, int, float o datetime.time
    supervisor_texto: Optional[str]
    fila_excel: int  # número de fila real en la hoja, para trazabilidad de errores

    def esta_vacia(self) -> bool:
        """
        Una pasada se considera vacía si no tiene ningún dato operativo
        cargado (turno, móvil, hora, supervisor), más allá de tener
        nombre de objetivo (el objetivo se repite en las 3 tablas
        aunque no haya habido pasada).
        """
        return not any(
            [self.turno_texto, self.movil_texto, self.hora_texto, self.supervisor_texto]
        )


# ---------------------------------------------------------------------------
# Datos normalizados (después de parser + normalizador + matcher)
# ---------------------------------------------------------------------------

@dataclass
class PasadaNormalizada:
    """
    Pasada ya normalizada y con matching de objetivo/supervisor resuelto
    (o pendiente, ver objetivo_id/supervisor_id en None).

    Esta es la unidad que viaja por duplicados.py, validador.py y
    finalmente se inserta en la tabla `pasadas` en importacion.py.
    """

    hoja: str
    bloque_tabla: Literal[1, 2, 3]

    objetivo_texto: str
    objetivo_id: Optional[int]  # None si todavía no fue matcheado/creado

    supervisor_texto: Optional[str]
    supervisor_id: Optional[int]  # None si todavía no fue matcheado/creado

    turno: Optional[Literal["D", "N"]]
    hora: Optional[time]
    fecha_operativa: Optional[date]
    fecha_calendario: Optional[date]

    movil_texto: Optional[str]

    fila_excel: int

    # Metadata útil para el reporte / advertencias, no para persistir en BD
    hora_fue_normalizada: bool = False
    supervisor_fue_inferido: bool = False


# ---------------------------------------------------------------------------
# Problemas detectados (errores, advertencias, matching pendiente)
# ---------------------------------------------------------------------------

TipoProblema = Literal["error_critico", "advertencia", "matching_pendiente"]


@dataclass
class Problema:
    """
    Un hallazgo del análisis, clasificado para saber si bloquea la
    importación (error_critico), si es informativo pero permite seguir
    (advertencia), o si requiere una decisión del usuario antes de
    poder confirmar (matching_pendiente).
    """

    tipo: TipoProblema
    descripcion: str
    hoja: str
    objetivo: Optional[str] = None
    valor_problema: Optional[object] = None
    sugerencias: list = field(default_factory=list)  # ej: candidatos de matching

    # Referencia para poder aplicar una corrección puntual desde la UI
    fila_excel: Optional[int] = None
    bloque_tabla: Optional[Literal[1, 2, 3]] = None

    # Se completa cuando el usuario resuelve el problema en la pantalla
    # de revisión (Fase 12). No se persiste hasta la confirmación final.
    resuelto: bool = False
    valor_corregido: Optional[object] = None


# ---------------------------------------------------------------------------
# Resultado del análisis completo (lo que arma reporte.py / Fase 10)
# ---------------------------------------------------------------------------

@dataclass
class ResultadoAnalisis:
    """
    Salida de analizar_excel(): todo lo que necesita la pantalla de
    análisis (Fase 11) y la pantalla de resolución (Fase 12) para
    mostrarse, sin haber tocado la base de datos todavía.
    """

    pasadas_listas: list[PasadaNormalizada] = field(default_factory=list)
    pasadas_ya_existentes: list[PasadaNormalizada] = field(default_factory=list)
    duplicados_descartados: list[PasadaNormalizada] = field(default_factory=list)
    problemas: list[Problema] = field(default_factory=list)

    def problemas_de_tipo(self, tipo: TipoProblema) -> list[Problema]:
        return [p for p in self.problemas if p.tipo == tipo]

    def tiene_bloqueantes_sin_resolver(self) -> bool:
        """
        True si hay errores críticos o matching pendiente sin resolver.
        Se usa para habilitar/deshabilitar el botón "Continuar".
        """
        return any(
            p.tipo in ("error_critico", "matching_pendiente") and not p.resuelto
            for p in self.problemas
        )

    def resumen(self) -> dict:
        return {
            "pasadas_detectadas": (
                len(self.pasadas_listas)
                + len(self.pasadas_ya_existentes)
                + len(self.duplicados_descartados)
            ),
            "pasadas_nuevas": len(self.pasadas_listas),
            "pasadas_ya_existentes": len(self.pasadas_ya_existentes),
            "duplicados": len(self.duplicados_descartados),
            "objetivos_no_reconocidos": len(
                [p for p in self.problemas_de_tipo("matching_pendiente") if "objetivo" in p.descripcion.lower()]
            ),
            "supervisores_no_reconocidos": len(
                [p for p in self.problemas_de_tipo("matching_pendiente") if "supervisor" in p.descripcion.lower()]
            ),
            "errores_criticos": len(self.problemas_de_tipo("error_critico")),
            "advertencias": len(self.problemas_de_tipo("advertencia")),
        }