# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de permisos y roles de usuario
# =============================================================================

from typing import Dict, List, Set
from services.sesion import get_rol

# =============================================================================
# DEFINICIÓN DE ROLES Y PERMISOS
# =============================================================================

ROLES_DISPONIBLES = {
    'admin': 'Administrador completo del sistema',
    'supervisor': 'Supervisor de operaciones diarias',
    'operador': 'Operador básico del sistema'
}

PERMISOS_POR_ROL: Dict[str, Set[str]] = {
    'admin': {
        # Gestión de usuarios
        'usuarios.crear', 'usuarios.editar', 'usuarios.eliminar', 'usuarios.ver',
        # Gestión de objetivos
        'objetivos.crear', 'objetivos.editar', 'objetivos.eliminar', 'objetivos.ver',
        # Gestión de supervisores
        'supervisores.crear', 'supervisores.editar', 'supervisores.eliminar', 'supervisores.ver',
        # Operaciones diarias
        'pasadas.crear', 'pasadas.editar', 'pasadas.eliminar', 'pasadas.ver',
        'equipos.crear', 'equipos.editar', 'equipos.eliminar', 'equipos.ver',
        # Reportes y análisis
        'reportes.ver', 'reportes.exportar',
        # Configuración del sistema
        'config.backup', 'config.restore', 'config.logs',
        # Auditoría
        'auditoria.ver'
    },
    'supervisor': {
        # Gestión limitada de objetivos
        'objetivos.ver', 'objetivos.editar',
        # Gestión de supervisores
        'supervisores.ver',
        # Operaciones diarias completas
        'pasadas.crear', 'pasadas.editar', 'pasadas.eliminar', 'pasadas.ver',
        'equipos.crear', 'equipos.editar', 'equipos.eliminar', 'equipos.ver',
        # Reportes limitados
        'reportes.ver',
        # Notas
        'notas.crear', 'notas.editar', 'notas.ver'
    },
    'operador': {
        # Solo operaciones básicas
        'objetivos.ver',
        'supervisores.ver',
        'pasadas.crear', 'pasadas.ver',
        'equipos.ver',
        'notas.ver'
    }
}

# =============================================================================
# FUNCIONES DE VERIFICACIÓN DE PERMISOS
# =============================================================================

def tiene_permiso(permiso: str) -> bool:
    """
    Verifica si el usuario actual tiene un permiso específico.
    Args:
        permiso: String del permiso a verificar (ej: 'objetivos.crear')
    Returns:
        True si tiene el permiso, False si no
    """
    rol_actual = get_rol()
    if not rol_actual:
        return False

    permisos_rol = PERMISOS_POR_ROL.get(rol_actual, set())
    return permiso in permisos_rol


def verificar_permisos_requeridos(permisos_requeridos: List[str]) -> bool:
    """
    Verifica si el usuario tiene al menos uno de los permisos requeridos.
    Args:
        permisos_requeridos: Lista de permisos, al menos uno debe tenerse
    Returns:
        True si tiene al menos uno, False si ninguno
    """
    return any(tiene_permiso(permiso) for permiso in permisos_requeridos)


def obtener_permisos_rol(rol: str) -> Set[str]:
    """
    Retorna todos los permisos de un rol específico.
    Args:
        rol: Nombre del rol
    Returns:
        Set con todos los permisos del rol
    """
    return PERMISOS_POR_ROL.get(rol, set())


def es_admin() -> bool:
    """Verifica si el usuario actual es administrador."""
    return get_rol() == 'admin'


def es_supervisor() -> bool:
    """Verifica si el usuario actual es supervisor."""
    return get_rol() == 'supervisor'


def es_operador() -> bool:
    """Verifica si el usuario actual es operador."""
    return get_rol() == 'operador'