# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de usuarios y contraseñas - VERSIÓN PROFESIONAL
# =============================================================================
import logging
from typing import Dict, List, Optional

import bcrypt
from database.gestor_db import gestor_db
from services.encriptacion import validar_contrasena_fuerte, generar_contrasena_segura
from services.permisos import ROLES_DISPONIBLES
from services.sincronizacion import notificar_cambio

from .exceptions import (
    UsuarioError, UsuarioYaExiste, ContraseñaInvalida,
    CredencialesIncorrectas, PermisoDenegado
)

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCIONES DE AUTENTICACIÓN
# =============================================================================

def autenticar_usuario(username: str, password: str) -> Dict[str, any]:
    """Autentica un usuario con username y contraseña.
    
    Args:
        username: Nombre de usuario.
        password: Contraseña en texto plano.
    
    Returns:
        Diccionario con datos del usuario autenticado:
        {
            'id': int,
            'username': str,
            'rol': str,
            'debe_cambiar_password': bool
        }
    
    Raises:
        CredencialesIncorrectas: Si username o password son incorrectos.
        DatabaseError: Si hay error en la base de datos.
    
    Example:
        >>> usuario = autenticar_usuario("admin", "pass123")
        >>> print(usuario['rol'])
        'admin'
    """
    try:
        resultado = gestor_db.ejecutar(
            "SELECT id, password, rol, debe_cambiar_password FROM usuarios WHERE username = ?",
            (username,)
        )
        
        if not resultado:
            logger.warning(f"Intento de login con usuario inexistente: {username}")
            raise CredencialesIncorrectas()
        
        usuario_data = resultado[0]
        password_hash = usuario_data['password']
        
        # Verificar contraseña
        try:
            if not bcrypt.checkpw(password.encode(), password_hash.encode()):
                logger.warning(f"Login fallido: contraseña incorrecta para {username}")
                raise CredencialesIncorrectas()
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            raise CredencialesIncorrectas()
        
        usuario_info = {
            'id': usuario_data['id'],
            'username': username,
            'rol': usuario_data['rol'],
            'debe_cambiar_password': bool(usuario_data['debe_cambiar_password'])
        }
        
        logger.info(f"Usuario autenticado: {username} (rol: {usuario_info['rol']})")
        return usuario_info
        
    except CredencialesIncorrectas:
        raise
    except Exception as e:
        logger.error(f"Error en autenticación: {e}")
        raise CredencialesIncorrectas()


# =============================================================================
# FUNCIONES DE ALTA (CREATE)
# =============================================================================

def crear_usuario(
    username: str,
    password: str,
    rol: str = "operador",
    debe_cambiar_password: bool = True
) -> Dict[str, any]:
    """Crea un nuevo usuario en el sistema.
    
    Args:
        username: Nombre de usuario único (requerido).
        password: Contraseña en texto plano (será hasheada).
        rol: Rol del usuario ('admin', 'supervisor', 'operador', etc).
        debe_cambiar_password: Si True, usuario debe cambiar pass en primer login.
    
    Returns:
        Diccionario con datos del usuario creado:
        {
            'id': int,
            'username': str,
            'rol': str,
            'debe_cambiar_password': bool
        }
    
    Raises:
        ContraseñaInvalida: Si la contraseña no cumple requisitos.
        UsuarioYaExiste: Si el username ya está registrado.
        DatabaseError: Si hay error en la base de datos.
    
    Example:
        >>> usuario = crear_usuario("juan", "Pass@123", rol="supervisor")
        >>> print(usuario['id'])
        5
    """
    try:
        # Validar rol
        if rol not in ROLES_DISPONIBLES:
            raise PermisoDenegado("crear_usuario", f"roles: {list(ROLES_DISPONIBLES.keys())}")
        
        # Validar contraseña
        es_valida, mensaje = validar_contrasena_fuerte(password)
        if not es_valida:
            logger.warning(f"Contraseña débil para nuevo usuario {username}: {mensaje}")
            raise ContraseñaInvalida(mensaje)
        
        # Hash de contraseña
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Insertar en base de datos
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, rol, 1 if debe_cambiar_password else 0))
            
            usuario_id = cursor.lastrowid
        
        # Construir respuesta
        usuario_info = {
            'id': usuario_id,
            'username': username,
            'rol': rol,
            'debe_cambiar_password': debe_cambiar_password
        }
        
        # Notificar cambio
        notificar_cambio("usuarios", "INSERT", {
            "id": usuario_id,
            "username": username,
            "rol": rol
        })
        
        logger.info(f"Usuario creado: {username} (ID: {usuario_id}, Rol: {rol})")
        return usuario_info
        
    except (ContraseñaInvalida, UsuarioError, PermisoDenegado) as e:
        logger.error(f"Error creando usuario {username}: {e}")
        raise
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.warning(f"Usuario duplicado: {username}")
            raise UsuarioYaExiste(username)
        logger.error(f"Error inesperado al crear usuario: {e}")
        raise


# =============================================================================
# FUNCIONES DE CONSULTA (READ)
# =============================================================================

def obtener_usuario_por_id(usuario_id: int) -> Optional[Dict[str, any]]:
    """Obtiene datos de un usuario por su ID.
    
    Args:
        usuario_id: ID del usuario.
    
    Returns:
        Diccionario con datos del usuario o None si no existe.
        
    Example:
        >>> usuario = obtener_usuario_por_id(1)
        >>> print(usuario['username'])
        'admin'
    """
    try:
        resultado = gestor_db.ejecutar(
            """SELECT id, username, rol, debe_cambiar_password 
               FROM usuarios WHERE id = ?""",
            (usuario_id,)
        )
        
        if not resultado:
            logger.debug(f"Usuario no encontrado: ID {usuario_id}")
            return None
        
        usuario = resultado[0]
        return {
            'id': usuario['id'],
            'username': usuario['username'],
            'rol': usuario['rol'],
            'debe_cambiar_password': bool(usuario['debe_cambiar_password'])
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo usuario {usuario_id}: {e}")
        raise


def get_username_by_id(usuario_id: int) -> Optional[str]:
    """Obtiene el nombre de usuario por su ID.
    
    Args:
        usuario_id: ID del usuario.
    
    Returns:
        Nombre de usuario o None si no existe.
        
    Note:
        Función de compatibilidad. Prefiere obtener_usuario_por_id.
    """
    usuario = obtener_usuario_por_id(usuario_id)
    return usuario['username'] if usuario else None


def listar_usuarios() -> List[Dict[str, any]]:
    """Retorna lista de todos los usuarios del sistema.
    
    Returns:
        Lista de diccionarios con datos de usuarios (sin contraseñas).
        
    Example:
        >>> usuarios = listar_usuarios()
        >>> print(len(usuarios))
        3
    """
    try:
        resultado = gestor_db.ejecutar(
            """SELECT id, username, rol, debe_cambiar_password 
               FROM usuarios ORDER BY username"""
        )
        
        usuarios = [
            {
                'id': u['id'],
                'username': u['username'],
                'rol': u['rol'],
                'debe_cambiar_password': bool(u['debe_cambiar_password'])
            }
            for u in resultado
        ]
        
        logger.debug(f"Listado de usuarios: {len(usuarios)} registros")
        return usuarios
        
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        raise


def listar_usuarios_por_rol(rol: str) -> List[Dict[str, any]]:
    """Retorna usuarios filtrados por rol.
    
    Args:
        rol: Rol a filtrar.
    
    Returns:
        Lista de usuarios con ese rol.
    """
    try:
        if rol not in ROLES_DISPONIBLES:
            raise PermisoDenegado("filtrar", f"rol {rol} no válido")
        
        resultado = gestor_db.ejecutar(
            """SELECT id, username, rol, debe_cambiar_password 
               FROM usuarios WHERE rol = ? ORDER BY username""",
            (rol,)
        )
        
        usuarios = [
            {
                'id': u['id'],
                'username': u['username'],
                'rol': u['rol'],
                'debe_cambiar_password': bool(u['debe_cambiar_password'])
            }
            for u in resultado
        ]
        
        logger.info(f"Usuarios con rol {rol}: {len(usuarios)} registros")
        return usuarios
        
    except Exception as e:
        logger.error(f"Error listando usuarios por rol {rol}: {e}")
        raise


# =============================================================================
# FUNCIONES DE ACTUALIZACIÓN (UPDATE)
# =============================================================================

def cambiar_contrasena_usuario(
    usuario_id: int,
    contrasena_actual: str,
    nueva_contrasena: str
) -> None:
    """Cambia la contraseña de un usuario.
    
    Args:
        usuario_id: ID del usuario.
        contrasena_actual: Contraseña actual para validación.
        nueva_contrasena: Nueva contraseña (debe cumplir requisitos).
    
    Raises:
        UsuarioError: Si usuario no existe o contraseña actual es incorrecta.
        ContraseñaInvalida: Si nueva contraseña no cumple requisitos.
        DatabaseError: Si hay error en la base de datos.
        
    Example:
        >>> cambiar_contrasena_usuario(1, "pass123", "NewPass@456")
    """
    try:
        # Validar nueva contraseña
        es_valida, mensaje = validar_contrasena_fuerte(nueva_contrasena)
        if not es_valida:
            raise ContraseñaInvalida(mensaje)
        
        # Obtener usuario
        usuario = obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise UsuarioError(f"Usuario {usuario_id} no encontrado")
        
        # Verificar contraseña actual
        resultado = gestor_db.ejecutar(
            "SELECT password FROM usuarios WHERE id = ?",
            (usuario_id,)
        )
        
        if not resultado:
            raise UsuarioError(f"Usuario {usuario_id} no encontrado")
        
        try:
            password_hash = resultado[0]['password']
            if not bcrypt.checkpw(contrasena_actual.encode(), password_hash.encode()):
                logger.warning(f"Intento de cambio de contraseña fallido para usuario {usuario_id}")
                raise UsuarioError("Contraseña actual incorrecta")
        except Exception as e:
            logger.error(f"Error verificando contraseña actual: {e}")
            raise UsuarioError("Error al verificar contraseña actual")
        
        # Hash de nueva contraseña
        nueva_password_hash = bcrypt.hashpw(nueva_contrasena.encode(), bcrypt.gensalt()).decode()
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios 
                SET password = ?, debe_cambiar_password = 0
                WHERE id = ?
            """, (nueva_password_hash, usuario_id))
        
        # Notificar cambio
        notificar_cambio("usuarios", "UPDATE", {
            "id": usuario_id,
            "cambio": "password"
        })
        
        logger.info(f"Contraseña cambiada para usuario {usuario['username']}")
        
    except (UsuarioError, ContraseñaInvalida) as e:
        logger.error(f"Error cambiando contraseña: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise


def cambiar_rol_usuario(usuario_id: int, nuevo_rol: str) -> None:
    """Cambia el rol de un usuario.
    
    Args:
        usuario_id: ID del usuario.
        nuevo_rol: Nuevo rol a asignar.
    
    Raises:
        PermisoDenegado: Si el rol no es válido.
        UsuarioError: Si el usuario no existe.
        
    Example:
        >>> cambiar_rol_usuario(2, "supervisor")
    """
    try:
        if nuevo_rol not in ROLES_DISPONIBLES:
            raise PermisoDenegado("cambiar_rol", f"rol {nuevo_rol} no válido")
        
        # Verificar que existe
        usuario = obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise UsuarioError(f"Usuario {usuario_id} no encontrado")
        
        # Actualizar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET rol = ? WHERE id = ?",
                (nuevo_rol, usuario_id)
            )
        
        # Notificar
        notificar_cambio("usuarios", "UPDATE", {
            "id": usuario_id,
            "nuevo_rol": nuevo_rol
        })
        
        logger.info(f"Rol cambiado para usuario {usuario['username']}: {usuario['rol']} → {nuevo_rol}")
        
    except (PermisoDenegado, UsuarioError) as e:
        logger.error(f"Error cambiando rol: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise


# =============================================================================
# FUNCIONES DE BAJA (DELETE)
# =============================================================================

def eliminar_usuario(usuario_id: int) -> None:
    """Elimina un usuario del sistema.
    
    Args:
        usuario_id: ID del usuario a eliminar.
    
    Raises:
        UsuarioError: Si el usuario no existe.
        
    Note:
        Esta es una operación destructiva. Considera soft delete para auditoría.
    """
    try:
        # Verificar que existe
        usuario = obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise UsuarioError(f"Usuario {usuario_id} no encontrado")
        
        # Eliminar
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        
        # Notificar
        notificar_cambio("usuarios", "DELETE", {
            "id": usuario_id,
            "username": usuario['username']
        })
        
        logger.warning(f"Usuario eliminado: {usuario['username']} (ID: {usuario_id})")
        
    except UsuarioError as e:
        logger.error(f"Error eliminando usuario: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def generar_contrasena_temporal() -> str:
    """Genera una contraseña temporal segura para nuevos usuarios.
    
    Returns:
        Contraseña temporal aleatoria.
        
    Example:
        >>> temp_pass = generar_contrasena_temporal()
        >>> print(len(temp_pass))
        10
    """
    return generar_contrasena_segura(10)


def requerir_cambio_contrasena(usuario_id: int) -> None:
    """Marca un usuario para que cambie contraseña en próximo login.
    
    Args:
        usuario_id: ID del usuario.
    """
    try:
        with gestor_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET debe_cambiar_password = 1 WHERE id = ?",
                (usuario_id,)
            )
        
        logger.info(f"Usuario {usuario_id} marcado para cambiar contraseña")
        
    except Exception as e:
        logger.error(f"Error requiriendo cambio de contraseña: {e}")
        raise