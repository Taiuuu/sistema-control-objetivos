# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de sesión activa
# =============================================================================

# Estado global de la sesión actual
_usuario_id_activo: int | None = None
_rol_activo: str | None = None


# =============================================================================
# SESIÓN
# =============================================================================

def iniciar_sesion(usuario_id: int, rol: str) -> None:
    """Registra el usuario y rol que iniciaron sesión."""
    global _usuario_id_activo, _rol_activo
    _usuario_id_activo = usuario_id
    _rol_activo = rol


def cerrar_sesion() -> None:
    """Limpia la sesión activa."""
    global _usuario_id_activo, _rol_activo
    _usuario_id_activo = None
    _rol_activo = None


def get_usuario_id() -> int | None:
    """Retorna el ID del usuario actualmente logueado."""
    return _usuario_id_activo


def get_rol() -> str | None:
    """Retorna el rol del usuario actualmente logueado."""
    return _rol_activo