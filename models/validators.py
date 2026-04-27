# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Validadores para el módulo de modelos
# =============================================================================
"""
Módulo con funciones de validación reutilizables para toda la capa de modelos.
Proporciona métodos centralizados para validar datos antes de ser procesados.
"""

import re
from datetime import datetime
from typing import Optional

from .exceptions import ValidationError
from .types import (
    NOMBRE_MINIMO, NOMBRE_MAXIMO,
    REGEX_FECHA, REGEX_HORA, TURNOS_VALIDOS,
    MENSAJE_CAMPO_REQUERIDO, MENSAJE_NOMBRE_CORTO,
    MENSAJE_NOMBRE_LARGO, MENSAJE_TURNO_INVALIDO,
    MENSAJE_FECHA_INVALIDA, MENSAJE_HORA_INVALIDA
)


def validar_nombre(nombre: Optional[str], campo: str = "nombre") -> str:
    """Valida que el nombre cumpla los requisitos.
    
    Args:
        nombre: Nombre a validar.
        campo: Nombre del campo (para mensajes de error).
    
    Returns:
        El nombre validado y normalizado.
    
    Raises:
        ValidationError: Si el nombre no es válido.
    """
    if not nombre or not nombre.strip():
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
    
    nombre = nombre.strip()
    
    if len(nombre) < NOMBRE_MINIMO:
        raise ValidationError(campo, MENSAJE_NOMBRE_CORTO)
    
    if len(nombre) > NOMBRE_MAXIMO:
        raise ValidationError(campo, MENSAJE_NOMBRE_LARGO)
    
    return nombre


def validar_fecha(fecha: Optional[str], campo: str = "fecha", requerida: bool = True) -> Optional[str]:
    """Valida que la fecha tenga formato YYYY-MM-DD.
    
    Args:
        fecha: Fecha a validar.
        campo: Nombre del campo (para mensajes de error).
        requerida: Si es True, la fecha no puede ser None.
    
    Returns:
        La fecha validada o None si no es requerida.
    
    Raises:
        ValidationError: Si la fecha no es válida.
    """
    if not fecha:
        if requerida:
            raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
        return None
    
    if not re.match(REGEX_FECHA, fecha):
        raise ValidationError(campo, MENSAJE_FECHA_INVALIDA)
    
    # Validar que sea una fecha válida
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(campo, MENSAJE_FECHA_INVALIDA)
    
    return fecha


def validar_hora(hora: Optional[str], campo: str = "hora") -> Optional[str]:
    """Valida que la hora tenga formato HH:MM o HH:MM:SS.
    
    Args:
        hora: Hora a validar.
        campo: Nombre del campo (para mensajes de error).
    
    Returns:
        La hora validada o None si no se proporciona.
    
    Raises:
        ValidationError: Si la hora no es válida.
    """
    if not hora:
        return None
    
    if not re.match(REGEX_HORA, hora):
        raise ValidationError(campo, MENSAJE_HORA_INVALIDA)
    
    return hora


def validar_turno(turno: Optional[str], campo: str = "turno") -> str:
    """Valida que el turno sea uno de los tipos válidos.
    
    Args:
        turno: Tipo de turno a validar.
        campo: Nombre del campo (para mensajes de error).
    
    Returns:
        El turno validado.
    
    Raises:
        ValidationError: Si el turno no es válido.
    """
    if not turno or not turno.strip():
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
    
    turno = turno.strip()
    
    if turno not in TURNOS_VALIDOS:
        raise ValidationError(campo, MENSAJE_TURNO_INVALIDO)
    
    return turno


def validar_id(id_valor: Optional[int], campo: str = "id") -> int:
    """Valida que el ID sea un número entero positivo.
    
    Args:
        id_valor: ID a validar.
        campo: Nombre del campo (para mensajes de error).
    
    Returns:
        El ID validado.
    
    Raises:
        ValidationError: Si el ID no es válido.
    """
    if id_valor is None:
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
    
    if not isinstance(id_valor, int) or id_valor <= 0:
        raise ValidationError(campo, f"ID debe ser un número entero positivo")
    
    return id_valor


def validar_dias_semana(dias: Optional[str], campo: str = "dias_semana") -> str:
    """Valida formato de días de la semana.
    
    Acepta formato: "Lunes,Martes,Miércoles" o JSON.
    
    Args:
        dias: String con días de la semana.
        campo: Nombre del campo (para mensajes de error).
    
    Returns:
        Los días validados.
    
    Raises:
        ValidationError: Si el formato no es válido.
    """
    if not dias or not dias.strip():
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
    
    dias = dias.strip()
    
    # Simplemente verificamos que no esté vacío
    # La validación más específica depende del formato utilizado
    if len(dias) == 0:
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
    
    return dias
