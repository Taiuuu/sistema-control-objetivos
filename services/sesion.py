# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de sesión activa
# =============================================================================

import time
import threading
import atexit
from typing import Dict, Any, Optional
from services.encriptacion import encriptar_datos, desencriptar_datos

# Estado global de la sesión actual
_usuario_id_activo: int | None = None
_rol_activo: str | None = None
_sesion_iniciada: float | None = None
_ultima_actividad: float | None = None
_token_sesion: str | None = None

# Configuración de sesión
TIEMPO_EXPIRACION_SESION = 8 * 60 * 60  # 8 horas en segundos
TIEMPO_INACTIVIDAD_MAXIMA = 2 * 60 * 60  # 2 horas de inactividad
TIEMPO_LIMPIEZA_SESIONES = 30 * 60  # 30 minutos entre limpiezas

# Almacén de sesiones expiradas para limpieza
_sesiones_expiradas: Dict[str, float] = {}

# Timer para limpieza automática
_timer_limpieza: threading.Timer | None = None


def _iniciar_limpieza_automatica():
    """Inicia el timer para limpieza automática de sesiones expiradas."""
    global _timer_limpieza
    if _timer_limpieza:
        _timer_limpieza.cancel()

    _timer_limpieza = threading.Timer(TIEMPO_LIMPIEZA_SESIONES, _limpiar_sesiones_expiradas)
    _timer_limpieza.daemon = True
    _timer_limpieza.start()


def _limpiar_sesiones_expiradas():
    """Limpia sesiones expiradas del almacén global."""
    global _sesiones_expiradas
    ahora = time.time()

    # Limpiar sesiones expiradas hace más de 1 hora
    sesiones_a_limpiar = [
        token for token, expira_en in _sesiones_expiradas.items()
        if ahora > expira_en + 3600  # 1 hora adicional
    ]

    for token in sesiones_a_limpiar:
        del _sesiones_expiradas[token]

    # Reiniciar timer
    _iniciar_limpieza_automatica()


# Registrar limpieza al salir
atexit.register(_limpiar_sesiones_expiradas)


# =============================================================================
# SESIÓN
# =============================================================================

def iniciar_sesion(usuario_id: int, rol: str) -> str:
    """
    Registra el usuario y rol que iniciaron sesión.
    Retorna un token de sesión encriptado.
    """
    global _usuario_id_activo, _rol_activo, _sesion_iniciada, _ultima_actividad, _token_sesion

    ahora = time.time()
    _usuario_id_activo = usuario_id
    _rol_activo = rol
    _sesion_iniciada = ahora
    _ultima_actividad = ahora

    # Generar token de sesión con datos encriptados
    datos_sesion = f"{usuario_id}:{rol}:{_sesion_iniciada}"
    _token_sesion = encriptar_datos(datos_sesion)

    # Iniciar limpieza automática si no está activa
    if not _timer_limpieza:
        _iniciar_limpieza_automatica()

    return _token_sesion


def cerrar_sesion() -> None:
    """Limpia la sesión activa y registra en expiradas."""
    global _usuario_id_activo, _rol_activo, _sesion_iniciada, _ultima_actividad, _token_sesion

    # Registrar en sesiones expiradas para limpieza futura
    if _token_sesion:
        _sesiones_expiradas[_token_sesion] = time.time() + TIEMPO_EXPIRACION_SESION

    _usuario_id_activo = None
    _rol_activo = None
    _sesion_iniciada = None
    _ultima_actividad = None
    _token_sesion = None


def validar_sesion_activa() -> bool:
    """
    Valida si la sesión actual es válida (no expirada por tiempo o inactividad).
    Returns:
        True si la sesión es válida, False si expiró
    """
    if not _sesion_iniciada or not _ultima_actividad:
        return False

    tiempo_actual = time.time()
    tiempo_sesion = tiempo_actual - _sesion_iniciada
    tiempo_inactividad = tiempo_actual - _ultima_actividad

    # Verificar expiración por tiempo total
    if tiempo_sesion > TIEMPO_EXPIRACION_SESION:
        cerrar_sesion()
        return False

    # Verificar inactividad
    if tiempo_inactividad > TIEMPO_INACTIVIDAD_MAXIMA:
        cerrar_sesion()
        return False

    return True


def actualizar_actividad_sesion() -> None:
    """Actualiza el timestamp de última actividad."""
    global _ultima_actividad
    if _sesion_iniciada:  # Solo actualizar si hay sesión activa
        _ultima_actividad = time.time()


def verificar_token_sesion(token: str) -> bool:
    """
    Verifica si un token de sesión es válido.
    Args:
        token: Token de sesión a verificar
    Returns:
        True si es válido, False si no
    """
    # Verificar si está en sesiones expiradas
    if token in _sesiones_expiradas:
        return False

    try:
        datos_desencriptados = desencriptar_datos(token)
        usuario_id, rol, timestamp_inicio = datos_desencriptados.split(':')

        # Verificar que coincida con la sesión actual
        if (int(usuario_id) == _usuario_id_activo and
            rol == _rol_activo and
            abs(float(timestamp_inicio) - (_sesion_iniciada or 0)) < 1):
            return validar_sesion_activa()

    except Exception:
        pass

    return False


def obtener_info_sesion() -> Optional[Dict[str, Any]]:
    """
    Retorna información detallada de la sesión actual.
    Returns:
        Dict con info de sesión o None si no hay sesión
    """
    if not validar_sesion_activa():
        return None

    tiempo_actual = time.time()
    return {
        "usuario_id": _usuario_id_activo,
        "rol": _rol_activo,
        "sesion_iniciada": _sesion_iniciada,
        "ultima_actividad": _ultima_actividad,
        "tiempo_sesion": tiempo_actual - (_sesion_iniciada or 0),
        "tiempo_inactividad": tiempo_actual - (_ultima_actividad or 0),
        "expira_en": TIEMPO_EXPIRACION_SESION - (tiempo_actual - (_sesion_iniciada or 0)),
        "token": _token_sesion
    }


def forzar_cierre_sesiones_expiradas() -> int:
    """
    Fuerza la limpieza de todas las sesiones expiradas.
    Returns:
        Número de sesiones limpiadas
    """
    global _sesiones_expiradas
    ahora = time.time()
    sesiones_antes = len(_sesiones_expiradas)

    _sesiones_expiradas = {
        token: expira_en for token, expira_en in _sesiones_expiradas.items()
        if ahora < expira_en
    }

    return sesiones_antes - len(_sesiones_expiradas)


def get_usuario_id() -> int | None:
    """
    Retorna el ID del usuario actualmente logueado.
    
    Returns:
        ID del usuario si sesión es válida, None si no hay sesión o expiró
        
    Note:
        Verifica que la sesión sea válida antes de retornar
    """
    if not validar_sesion_activa():
        return None
    return _usuario_id_activo


def obtener_sesion_valida() -> tuple | None:
    """
    Obtiene información de sesión validada de forma centralizada.
    
    Returns:
        Tupla (usuario_id, rol) si sesión es válida, None si no
        
    Example:
        sesion = obtener_sesion_valida()
        if sesion:
            usuario_id, rol = sesion
            # Continuar
        else:
            # Mostrar error de sesión expirada
    """
    if not validar_sesion_activa():
        return None
    return (_usuario_id_activo, _rol_activo)


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