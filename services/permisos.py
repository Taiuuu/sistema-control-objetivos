# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de permisos y roles de usuario
# =============================================================================

from typing import Dict, List, Set
from functools import wraps
from services.sesion import get_rol, get_usuario_id

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


# =============================================================================
# DECORADORES CON ERROR HANDLING
# =============================================================================

def requiere_permiso(permiso: str):
    """
    Decorador que valida que el usuario tiene un permiso específico.
    
    Args:
        permiso: Permiso requerido (ej: 'objetivos.crear')
        
    Returns:
        Decorador que verifica el permiso antes de ejecutar la función
        
    Raises:
        PermisoDenegadoError: Si el usuario no tiene el permiso
        
    Example:
        @requiere_permiso('objetivos.crear')
        def crear_objetivo(nombre: str) -> int:
            # ... código ...
            return objetivo_id
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validar que hay sesión activa
                usuario_id = get_usuario_id()
                if not usuario_id:
                    raise PermisoDenegadoError(
                        "Sesión no válida - Por favor inicia sesión",
                        codigo_error="SESION_EXPIRADA"
                    )
                
                # Validar que tiene el permiso
                if not tiene_permiso(permiso):
                    # Loguear intento de acceso denegado
                    try:
                        from services.logger import registrar_accion
                        registrar_accion(
                            usuario_id, 
                            f"❌ Intento acceso denegado a {func.__name__} - Permiso requerido: {permiso}"
                        )
                    except Exception as e:
                        print(f"⚠️ Error registrando acceso denegado: {e}")
                    
                    raise PermisoDenegadoError(
                        f"No tienes permiso para esta acción: {permiso}",
                        codigo_error="PERMISO_INSUFICIENTE",
                        permiso_requerido=permiso
                    )
                
                # Loguear acceso exitoso
                try:
                    from services.logger import registrar_accion
                    registrar_accion(usuario_id, f"✅ Acceso: {func.__name__}")
                except Exception:
                    pass  # No interrumpir si logging falla
                
                # Ejecutar función
                return func(*args, **kwargs)
                
            except PermisoDenegadoError:
                raise  # Re-lanzar errores de permiso
            except Exception as e:
                print(f"❌ Error en decorador @requiere_permiso: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        return wrapper
    return decorador


def requiere_rol(rol_requerido: str):
    """
    Decorador que valida que el usuario tiene un rol específico.
    
    Args:
        rol_requerido: Rol requerido (ej: 'admin', 'supervisor')
        
    Returns:
        Decorador que verifica el rol antes de ejecutar la función
        
    Raises:
        PermisoDenegadoError: Si el usuario no tiene el rol
        
    Example:
        @requiere_rol('admin')
        def eliminar_usuario(usuario_id: int) -> bool:
            # ... código ...
            return True
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                usuario_id = get_usuario_id()
                if not usuario_id:
                    raise PermisoDenegadoError(
                        "Sesión no válida",
                        codigo_error="SESION_EXPIRADA"
                    )
                
                rol_actual = get_rol()
                if rol_actual != rol_requerido:
                    # Loguear
                    try:
                        from services.logger import registrar_accion
                        registrar_accion(
                            usuario_id,
                            f"❌ Intento acceso denegado: rol requerido '{rol_requerido}', tiene '{rol_actual}'"
                        )
                    except Exception:
                        pass
                    
                    raise PermisoDenegadoError(
                        f"Se requiere rol '{rol_requerido}'",
                        codigo_error="ROL_INSUFICIENTE"
                    )
                
                # Loguear acceso
                try:
                    from services.logger import registrar_accion
                    registrar_accion(usuario_id, f"✅ Acceso: {func.__name__}")
                except Exception:
                    pass
                
                return func(*args, **kwargs)
                
            except PermisoDenegadoError:
                raise
            except Exception as e:
                print(f"❌ Error en decorador @requiere_rol: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        return wrapper
    return decorador


def requiere_alguno_de(roles_permitidos: List[str]):
    """
    Decorador que valida que el usuario tiene uno de varios roles.
    
    Args:
        roles_permitidos: Lista de roles permitidos
        
    Returns:
        Decorador que verifica que el usuario tiene uno de los roles
        
    Raises:
        PermisoDenegadoError: Si el usuario no tiene ninguno de los roles
        
    Example:
        @requiere_alguno_de(['admin', 'supervisor'])
        def ver_reportes_avanzados() -> dict:
            # ... código ...
            return reportes
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                usuario_id = get_usuario_id()
                if not usuario_id:
                    raise PermisoDenegadoError(
                        "Sesión no válida",
                        codigo_error="SESION_EXPIRADA"
                    )
                
                rol_actual = get_rol()
                if rol_actual not in roles_permitidos:
                    # Loguear
                    try:
                        from services.logger import registrar_accion
                        registrar_accion(
                            usuario_id,
                            f"❌ Intento acceso denegado: roles permitidos {roles_permitidos}, tiene '{rol_actual}'"
                        )
                    except Exception:
                        pass
                    
                    raise PermisoDenegadoError(
                        f"Se requiere uno de estos roles: {', '.join(roles_permitidos)}",
                        codigo_error="ROL_INSUFICIENTE"
                    )
                
                # Loguear acceso
                try:
                    from services.logger import registrar_accion
                    registrar_accion(usuario_id, f"✅ Acceso: {func.__name__}")
                except Exception:
                    pass
                
                return func(*args, **kwargs)
                
            except PermisoDenegadoError:
                raise
            except Exception as e:
                print(f"❌ Error en decorador @requiere_alguno_de: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        return wrapper
    return decorador


# =============================================================================
# CLASES DE EXCEPCIÓN
# =============================================================================

class PermisoDenegadoError(Exception):
    """
    Excepción lanzada cuando se deniega un permiso.
    
    Attributes:
        message: Mensaje de error
        codigo_error: Código de error para debugging
        permiso_requerido: Permiso que se requería (opcional)
    """
    
    def __init__(self, message: str, codigo_error: str = "PERMISO_DENEGADO", permiso_requerido: str = ""):
        """Inicializa la excepción de permiso denegado."""
        self.message = message
        self.codigo_error = codigo_error
        self.permiso_requerido = permiso_requerido
        super().__init__(self.message)