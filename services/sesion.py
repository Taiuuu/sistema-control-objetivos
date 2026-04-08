# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de sesión activa
# =============================================================================

import time
from typing import Dict, Any
from services.encriptacion import encriptar_datos, desencriptar_datos

# Estado global de la sesión actual
_usuario_id_activo: int | None = None
_rol_activo: str | None = None
_sesion_iniciada: float | None = None
_token_sesion: str | None = None

# Configuración de sesión
TIEMPO_EXPIRACION_SESION = 8 * 60 * 60  # 8 horas en segundos
TIEMPO_INACTIVIDAD_MAXIMA = 2 * 60 * 60  # 2 horas de inactividad


# =============================================================================
# SESIÓN
# =============================================================================

def iniciar_sesion(usuario_id: int, rol: str) -> str:
    """
    Registra el usuario y rol que iniciaron sesión.
    Retorna un token de sesión encriptado.
    """
    global _usuario_id_activo, _rol_activo, _sesion_iniciada, _token_sesion

    _usuario_id_activo = usuario_id
    _rol_activo = rol
    _sesion_iniciada = time.time()

    # Generar token de sesión con datos encriptados
    datos_sesion = f"{usuario_id}:{rol}:{_sesion_iniciada}"
    _token_sesion = encriptar_datos(datos_sesion)

    return _token_sesion


def cerrar_sesion() -> None:
    """Limpia la sesión activa."""
    global _usuario_id_activo, _rol_activo, _sesion_iniciada, _token_sesion
    _usuario_id_activo = None
    _rol_activo = None
    _sesion_iniciada = None
    _token_sesion = None


def validar_sesion_activa() -> bool:
    """
    Valida si la sesión actual es válida (no expirada por tiempo o inactividad).
    Returns:
        True si la sesión es válida, False si expiró
    """
    if not _sesion_iniciada:
        return False

    tiempo_actual = time.time()
    tiempo_sesion = tiempo_actual - _sesion_iniciada

    # Verificar expiración por tiempo total
    if tiempo_sesion > TIEMPO_EXPIRACION_SESION:
        cerrar_sesion()
        return False

    # Verificar inactividad (esto requeriría actualizar timestamp en cada acción)
    # Por ahora, solo validamos tiempo total
    return True


def actualizar_actividad_sesion() -> None:
    """Actualiza el timestamp de última actividad (llamar en cada acción del usuario)."""
    global _sesion_iniciada
    if _sesion_iniciada:
        _sesion_iniciada = time.time()


def verificar_token_sesion(token: str) -> bool:
    """
    Verifica si un token de sesión es válido.
    Args:
        token: Token de sesión a verificar
    Returns:
        True si es válido, False si no
    """
    try:
        datos_desencriptados = desencriptar_datos(token)
        usuario_id, rol, timestamp_inicio = datos_desencriptados.split(':')

        # Verificar que coincida con la sesión actual
        if (int(usuario_id) == _usuario_id_activo and
            rol == _rol_activo and
            abs(float(timestamp_inicio) - (_sesion_iniciada or 0)) < 1):
            return True

    except Exception:
        pass

    return False


def get_usuario_id() -> int | None:
    """Retorna el ID del usuario actualmente logueado."""
    if not validar_sesion_activa():
        return None
    return _usuario_id_activo


def get_rol() -> str | None:
    """Retorna el rol del usuario actualmente logueado."""
    if not validar_sesion_activa():
        return None
    return _rol_activo


def get_token_sesion() -> str | None:
    """Retorna el token de sesión actual."""
    return _token_sesion


def tiempo_restante_sesion() -> int:
    """
    Retorna los segundos restantes antes de que expire la sesión.
    Returns:
        Segundos restantes, 0 si ya expiró
    """
    if not _sesion_iniciada:
        return 0

    tiempo_actual = time.time()
    tiempo_sesion = tiempo_actual - _sesion_iniciada
    tiempo_restante = TIEMPO_EXPIRACION_SESION - tiempo_sesion

    return max(0, int(tiempo_restante))