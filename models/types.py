# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Tipos de datos y constantes para el módulo de modelos
# =============================================================================
"""
Módulo que define tipos de datos, dataclasses y enumeraciones utilizadas
en toda la capa de modelos para mayor type-safety y claridad.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


# =============================================================================
# ENUMERACIONES
# =============================================================================

class TurnoEnum(str, Enum):
    """Tipos de turnos disponibles en el sistema."""
    MAÑANA = "Mañana"
    TARDE = "Tarde"
    NOCHE = "Noche"
    COMPLETO = "Completo"
    
    @classmethod
    def values(cls) -> list[str]:
        """Retorna lista de valores válidos."""
        return [t.value for t in cls]
    
    @classmethod
    def is_valid(cls, turno: str) -> bool:
        """Valida si un turno es válido."""
        return turno in cls.values()


class DiasSemana(str, Enum):
    """Días de la semana."""
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class EstadoSupervisor(str, Enum):
    """Estados posibles de un supervisor."""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class Objetivo:
    """Representa un objetivo del sistema.
    
    Attributes:
        id: Identificador único en la base de datos.
        nombre: Nombre descriptivo del objetivo.
        fecha_inicio: Fecha de inicio (YYYY-MM-DD).
        fecha_fin: Fecha de finalización opcional (YYYY-MM-DD).
        dias_semana: Días aplicables, formato "Lunes,Martes,..." o JSON.
        creado_en: Timestamp de creación.
        actualizado_en: Timestamp de última actualización.
    """
    nombre: str
    fecha_inicio: str
    dias_semana: str
    id: Optional[int] = None
    fecha_fin: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    
    def es_activo(self) -> bool:
        """Verifica si el objetivo está activo (no tiene fecha fin)."""
        return self.fecha_fin is None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Objetivo):
            return False
        return self.id == other.id


@dataclass
class Supervisor:
    """Representa un supervisor del sistema.
    
    Attributes:
        id: Identificador único en la base de datos.
        nombre: Nombre completo del supervisor.
        fecha_alta: Fecha de alta en el sistema (YYYY-MM-DD).
        fecha_baja: Fecha de baja, None si está activo (YYYY-MM-DD).
        creado_en: Timestamp de creación.
        actualizado_en: Timestamp de última actualización.
    """
    nombre: str
    fecha_alta: str
    id: Optional[int] = None
    fecha_baja: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    
    def es_activo(self) -> bool:
        """Verifica si el supervisor está activo (no tiene fecha de baja)."""
        return self.fecha_baja is None
    
    def get_estado(self) -> EstadoSupervisor:
        """Retorna el estado actual del supervisor."""
        if self.fecha_baja is None:
            return EstadoSupervisor.ACTIVO
        return EstadoSupervisor.INACTIVO
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Supervisor):
            return False
        return self.id == other.id


@dataclass
class Pasada:
    """Representa un turno registrado (pasada).
    
    Attributes:
        id: Identificador único en la base de datos.
        fecha: Fecha del turno (YYYY-MM-DD).
        turno: Tipo de turno (Mañana, Tarde, Noche, Completo).
        objetivo_id: ID del objetivo asociado.
        supervisor_id: ID del supervisor que realizó la pasada.
        hora: Hora opcional del registro (HH:MM:SS).
        observaciones: Notas adicionales sobre la pasada.
        creado_en: Timestamp de creación.
        actualizado_en: Timestamp de última actualización.
    """
    fecha: str
    turno: str
    objetivo_id: int
    supervisor_id: int
    id: Optional[int] = None
    hora: Optional[str] = None
    observaciones: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    
    def es_valida(self) -> bool:
        """Verifica si la pasada tiene datos válidos."""
        return (
            self.fecha and 
            TurnoEnum.is_valid(self.turno) and 
            self.objetivo_id > 0 and 
            self.supervisor_id > 0
        )
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Pasada):
            return False
        return self.id == other.id


@dataclass
class Equipo:
    """Representa un equipo del sistema.
    
    Attributes:
        id: Identificador único en la base de datos.
        nombre: Nombre del equipo.
        descripcion: Descripción detallada del equipo.
        estado: Estado actual (activo/inactivo).
        creado_en: Timestamp de creación.
        actualizado_en: Timestamp de última actualización.
    """
    nombre: str
    descripcion: Optional[str] = None
    id: Optional[int] = None
    estado: str = "activo"
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    
    def es_activo(self) -> bool:
        """Verifica si el equipo está activo."""
        return self.estado == "activo"
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Equipo):
            return False
        return self.id == other.id


# =============================================================================
# CONSTANTES
# =============================================================================

# Límites y restricciones
NOMBRE_MINIMO = 3
NOMBRE_MAXIMO = 255

DIAS_SEMANA_VALIDOS = [
    "Lunes", "Martes", "Miércoles", "Jueves", 
    "Viernes", "Sábado", "Domingo"
]

TURNOS_VALIDOS = TurnoEnum.values()

# Configuración de validación
REGEX_FECHA = r"^\d{4}-\d{2}-\d{2}$"  # YYYY-MM-DD
REGEX_HORA = r"^\d{2}:\d{2}(:\d{2})?$"  # HH:MM o HH:MM:SS

# Mensajes de error
MENSAJE_CAMPO_REQUERIDO = "Campo requerido"
MENSAJE_NOMBRE_CORTO = f"El nombre debe tener al menos {NOMBRE_MINIMO} caracteres"
MENSAJE_NOMBRE_LARGO = f"El nombre no puede exceder {NOMBRE_MAXIMO} caracteres"
MENSAJE_TURNO_INVALIDO = f"Turno debe ser uno de: {', '.join(TURNOS_VALIDOS)}"
MENSAJE_FECHA_INVALIDA = "La fecha debe tener formato YYYY-MM-DD"
MENSAJE_HORA_INVALIDA = "La hora debe tener formato HH:MM o HH:MM:SS"
