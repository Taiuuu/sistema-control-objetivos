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


def validar_email(email: Optional[str], campo: str = "email", requerida: bool = False) -> Optional[str]:
    """Valida formato de email con regex robusto.

    Args:
        email: Email a validar.
        campo: Nombre del campo.
        requerida: Si es True, el email no puede ser None.

    Returns:
        Email validado en minúsculas o None.

    Raises:
        ValidationError: Si el email no es válido.
    """
    if not email:
        if requerida:
            raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
        return None

    email = email.strip().lower()

    # Regex más robusto para emails (RFC 5322 compliant básico)
    patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(patron_email, email):
        raise ValidationError(campo, "Formato de email inválido")

    if len(email) > 254:  # RFC 5321 límite
        raise ValidationError(campo, "Email demasiado largo")

    return email


def validar_telefono(telefono: Optional[str], campo: str = "telefono", requerida: bool = False) -> Optional[str]:
    """Valida formato de teléfono.

    Args:
        telefono: Teléfono a validar (acepta varios formatos).
        campo: Nombre del campo.
        requerida: Si es True, el teléfono no puede ser None.

    Returns:
        Teléfono normalizado o None.

    Raises:
        ValidationError: Si el teléfono no es válido.
    """
    if not telefono:
        if requerida:
            raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)
        return None

    # Remover todos los caracteres no numéricos excepto +
    telefono_limpio = re.sub(r'[^\d+]', '', telefono.strip())

    # Validar formato básico
    if not telefono_limpio:
        raise ValidationError(campo, "Teléfono inválido")

    # Debe empezar con + o dígito
    if not telefono_limpio[0] in '0123456789+':
        raise ValidationError(campo, "Teléfono debe empezar con dígito o +")

    # Longitud razonable
    if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
        raise ValidationError(campo, "Longitud de teléfono inválida")

    return telefono_limpio


def validar_password(password: str, campo: str = "password") -> str:
    """Valida fortaleza de contraseña.

    Args:
        password: Contraseña a validar.

    Returns:
        Contraseña validada.

    Raises:
        ValidationError: Si la contraseña no cumple requisitos.
    """
    if not password:
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)

    if len(password) < 8:
        raise ValidationError(campo, "La contraseña debe tener al menos 8 caracteres")

    if len(password) > 128:
        raise ValidationError(campo, "La contraseña es demasiado larga")

    # Verificar complejidad
    tiene_minuscula = bool(re.search(r'[a-z]', password))
    tiene_mayuscula = bool(re.search(r'[A-Z]', password))
    tiene_numero = bool(re.search(r'[0-9]', password))
    tiene_especial = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

    if not (tiene_minuscula and tiene_mayuscula and tiene_numero):
        raise ValidationError(campo,
            "La contraseña debe contener al menos una minúscula, una mayúscula y un número")

    # Verificar que no sea una contraseña común
    contraseñas_comunes = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]

    if password.lower() in contraseñas_comunes:
        raise ValidationError(campo, "Esta contraseña es demasiado común")

    return password


def validar_username(username: str, campo: str = "username") -> str:
    """Valida nombre de usuario.

    Args:
        username: Username a validar.

    Returns:
        Username validado en minúsculas.

    Raises:
        ValidationError: Si el username no es válido.
    """
    if not username:
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)

    username = username.strip().lower()

    if len(username) < 3:
        raise ValidationError(campo, "El nombre de usuario debe tener al menos 3 caracteres")

    if len(username) > 50:
        raise ValidationError(campo, "El nombre de usuario es demasiado largo")

    # Solo letras, números, guiones y puntos
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        raise ValidationError(campo, "El nombre de usuario solo puede contener letras, números, puntos y guiones")

    # No puede empezar ni terminar con punto o guión
    if username.startswith('.') or username.endswith('.'):
        raise ValidationError(campo, "El nombre de usuario no puede empezar ni terminar con punto")

    if username.startswith('-') or username.endswith('-'):
        raise ValidationError(campo, "El nombre de usuario no puede empezar ni terminar con guión")

    return username


def validar_longitud_texto(texto: str, campo: str, min_longitud: int = 1, max_longitud: int = 1000) -> str:
    """Valida longitud de texto con límites personalizables.

    Args:
        texto: Texto a validar.
        campo: Nombre del campo.
        min_longitud: Longitud mínima requerida.
        max_longitud: Longitud máxima permitida.

    Returns:
        Texto validado.

    Raises:
        ValidationError: Si la longitud no es válida.
    """
    if not texto:
        raise ValidationError(campo, MENSAJE_CAMPO_REQUERIDO)

    texto = texto.strip()

    if len(texto) < min_longitud:
        raise ValidationError(campo, f"Debe tener al menos {min_longitud} caracteres")

    if len(texto) > max_longitud:
        raise ValidationError(campo, f"No puede tener más de {max_longitud} caracteres")

    return texto


def sanitizar_texto(texto: str, max_longitud: int = 1000) -> str:
    """Sanitiza texto removiendo caracteres peligrosos.

    Args:
        texto: Texto a sanitizar.

    Returns:
        Texto sanitizado.
    """
    if not texto:
        return ""

    # Remover caracteres de control
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto.strip())

    # Limitar longitud
    if len(texto) > max_longitud:
        texto = texto[:max_longitud]

    return texto

def validar_hora(hora: Optional[str], campo: str = "hora") -> Optional[str]:
    """Valida que la hora tenga formato HH:MM.

    Args:
        hora: Hora a validar.
        campo: Nombre del campo (para mensajes de error).

    Returns:
        La hora validada o None si no se proporcionó.

    Raises:
        ValidationError: Si la hora no es válida.
    """
    if not hora:
        return None

    hora = hora.strip()

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
