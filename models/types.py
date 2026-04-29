# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Tipos de datos y constantes para el módulo de modelos
# =============================================================================
"""
Módulo que define tipos de datos, dataclasses y enumeraciones utilizadas
en toda la capa de modelos para mayor claridad y consistencia.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# =============================================================================
# ENUMERACIONES
# =============================================================================

class TurnoEnum(str, Enum):
    """Tipos de turnos disponibles en el sistema."""
    DIURNO = "diurno"
    NOCTURNO = "nocturno"

    @classmethod
    def values(cls) -> list[str]:
        return [t.value for t in cls]

    @classmethod
    def is_valid(cls, turno: str) -> bool:
        return turno.lower() in cls.values()


class DiasSemana(str, Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class EstadoSupervisor(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class Objetivo:
    nombre: str
    fecha_inicio: str
    dias_semana: str
    id: Optional[int] = None
    fecha_fin: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None

    def es_activo(self) -> bool:
        return self.fecha_fin is None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Objetivo) and self.id == other.id


@dataclass
class Supervisor:
    nombre: str
    fecha_alta: str
    id: Optional[int] = None
    fecha_baja: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None

    def es_activo(self) -> bool:
        return self.fecha_baja is None

    def get_estado(self) -> EstadoSupervisor:
        return EstadoSupervisor.ACTIVO if self.fecha_baja is None else EstadoSupervisor.INACTIVO

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Supervisor) and self.id == other.id


@dataclass
class Pasada:
    fecha: str
    turno: str
    objetivo_id: int
    supervisor_id: int
    id: Optional[int] = None
    hora: Optional[str] = None   # HH:MM
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None

    def es_valida(self) -> bool:
        return (
            self.fecha and
            TurnoEnum.is_valid(self.turno) and
            self.objetivo_id > 0 and
            self.supervisor_id > 0
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Pasada) and self.id == other.id


@dataclass
class Equipo:
    nombre: str
    descripcion: Optional[str] = None
    id: Optional[int] = None
    estado: str = "activo"
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None

    def es_activo(self) -> bool:
        return self.estado == "activo"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Equipo) and self.id == other.id


# =============================================================================
# CONSTANTES
# =============================================================================

NOMBRE_MINIMO = 3
NOMBRE_MAXIMO = 255

DIAS_SEMANA_VALIDOS = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo"
]

TURNOS_VALIDOS = TurnoEnum.values()

# Validaciones
REGEX_FECHA = r"^\d{4}-\d{2}-\d{2}$"   # YYYY-MM-DD
REGEX_HORA = r"^\d{2}:\d{2}$"          # SOLO HH:MM

# Mensajes
MENSAJE_CAMPO_REQUERIDO = "Campo requerido"
MENSAJE_NOMBRE_CORTO = f"El nombre debe tener al menos {NOMBRE_MINIMO} caracteres"
MENSAJE_NOMBRE_LARGO = f"El nombre no puede exceder {NOMBRE_MAXIMO} caracteres"
MENSAJE_TURNO_INVALIDO = "El turno debe ser diurno o nocturno"
MENSAJE_FECHA_INVALIDA = "La fecha debe tener formato YYYY-MM-DD"
MENSAJE_HORA_INVALIDA = "La hora debe tener formato HH:MM"