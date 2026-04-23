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
    'auditor': 'Auditor con acceso de solo lectura',
    'gerente': 'Gerente con vista ejecutiva',
    'operador': 'Operador básico del sistema'
}

PERMISOS_POR_ROL: Dict[str, Set[str]] = {
    'admin': {
        # Gestión completa de usuarios
        'usuarios.crear', 'usuarios.editar', 'usuarios.eliminar', 'usuarios.ver',
        'usuarios.cambiar_rol',
        # Gestión completa de objetivos
        'objetivos.crear', 'objetivos.editar', 'objetivos.eliminar', 'objetivos.ver',
        # Gestión completa de supervisores
        'supervisores.crear', 'supervisores.editar', 'supervisores.eliminar', 'supervisores.ver',
        # Operaciones diarias completas
        'pasadas.crear', 'pasadas.editar', 'pasadas.eliminar', 'pasadas.ver',
        'equipos.crear', 'equipos.editar', 'equipos.eliminar', 'equipos.ver',
        # Reportes y análisis completos
        'reportes.ver', 'reportes.exportar',
        # Configuración completa del sistema
        'config.backup', 'config.restore', 'config.logs', 'config.sincronizacion',
        # Auditoría completa
        'auditoria.ver',
        # Notas completas
        'notas.crear', 'notas.editar', 'notas.ver',
        # Dashboard y estadísticas
        'dashboard.ver', 'estadisticas.ver'
    },
    'supervisor': {
        # Gestión limitada de objetivos
        'objetivos.ver', 'objetivos.editar', 'objetivos.crear',
        # Gestión de supervisores
        'supervisores.ver', 'supervisores.editar',
        # Operaciones diarias completas
        'pasadas.crear', 'pasadas.editar', 'pasadas.eliminar', 'pasadas.ver',
        'equipos.crear', 'equipos.editar', 'equipos.eliminar', 'equipos.ver',
        # Reportes de su área
        'reportes.ver', 'reportes.exportar',
        # Notas
        'notas.crear', 'notas.editar', 'notas.ver',
        # Dashboard básico
        'dashboard.ver'
    },
    'auditor': {
        # Solo lectura de todo
        'usuarios.ver',
        'objetivos.ver',
        'supervisores.ver',
        'pasadas.ver',
        'equipos.ver',
        'reportes.ver', 'reportes.exportar',
        'auditoria.ver',
        'notas.ver',
        'dashboard.ver', 'estadisticas.ver',
        'config.logs'
    },
    'gerente': {
        # Vista ejecutiva
        'objetivos.ver',
        'supervisores.ver',
        'pasadas.ver',
        'equipos.ver',
        'reportes.ver', 'reportes.exportar',
        'dashboard.ver', 'estadisticas.ver',
        'notas.ver'
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