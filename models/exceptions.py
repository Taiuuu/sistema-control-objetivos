# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Excepciones personalizadas para el módulo de modelos
# =============================================================================
"""
Módulo de excepciones personalizadas para validación y manejo de errores
en las operaciones de bases de datos y modelos.

Define excepciones específicas del dominio para proporcionar mayor claridad
en el manejo de errores y facilitar el debugging.
"""


class ModelError(Exception):
    """Excepción base para errores en modelos."""
    pass


class ValidationError(ModelError):
    """Se lanza cuando los datos no cumplen las reglas de validación."""
    def __init__(self, campo: str, mensaje: str):
        self.campo = campo
        self.mensaje = mensaje
        super().__init__(f"Validación fallida en '{campo}': {mensaje}")


class ObjetivoError(ModelError):
    """Excepciones específicas para operaciones con objetivos."""
    pass


class ObjetivoNoEncontrado(ObjetivoError):
    """Se lanza cuando no existe un objetivo con el ID especificado."""
    def __init__(self, objetivo_id: int):
        self.objetivo_id = objetivo_id
        super().__init__(f"Objetivo con ID {objetivo_id} no encontrado")


class ObjetivoYaExiste(ObjetivoError):
    """Se lanza cuando se intenta crear un objetivo que ya existe."""
    def __init__(self, nombre: str):
        self.nombre = nombre
        super().__init__(f"Objetivo '{nombre}' ya existe en el sistema")


class SupervisorError(ModelError):
    """Excepciones específicas para operaciones con supervisores."""
    pass


class SupervisorNoEncontrado(SupervisorError):
    """Se lanza cuando no existe un supervisor con el ID especificado."""
    def __init__(self, supervisor_id: int):
        self.supervisor_id = supervisor_id
        super().__init__(f"Supervisor con ID {supervisor_id} no encontrado")


class SupervisorYaExiste(SupervisorError):
    """Se lanza cuando se intenta crear un supervisor que ya existe."""
    def __init__(self, nombre: str):
        self.nombre = nombre
        super().__init__(f"Supervisor '{nombre}' ya existe en el sistema")


class SupervisorInactivo(SupervisorError):
    """Se lanza cuando se intenta operar con un supervisor inactivo."""
    def __init__(self, supervisor_id: int):
        self.supervisor_id = supervisor_id
        super().__init__(f"Supervisor {supervisor_id} está inactivo (tiene fecha de baja)")


class TurnoError(ModelError):
    """Excepciones específicas para operaciones con turnos/pasadas."""
    pass


class TurnoNoEncontrado(TurnoError):
    """Se lanza cuando no existe un turno con el ID especificado."""
    def __init__(self, turno_id: int):
        self.turno_id = turno_id
        super().__init__(f"Turno con ID {turno_id} no encontrado")


class TurnoYaRegistrado(TurnoError):
    """Se lanza cuando se intenta registrar un turno duplicado."""
    def __init__(self, fecha: str, objetivo_id: int, supervisor_id: int):
        super().__init__(
            f"Turno ya registrado para {fecha} en objetivo {objetivo_id} con supervisor {supervisor_id}"
        )


class EquipoError(ModelError):
    """Excepciones específicas para operaciones con equipos."""
    pass


class EquipoNoEncontrado(EquipoError):
    """Se lanza cuando no existe un equipo con el ID especificado."""
    def __init__(self, equipo_id: int):
        self.equipo_id = equipo_id
        super().__init__(f"Equipo con ID {equipo_id} no encontrado")


class DatabaseError(ModelError):
    """Se lanza cuando hay un error en operaciones de base de datos."""
    def __init__(self, operacion: str, mensaje: str):
        self.operacion = operacion
        super().__init__(f"Error en {operacion}: {mensaje}")
