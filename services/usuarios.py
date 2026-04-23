# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de usuarios y contraseñas
# =============================================================================

import sqlite3
import bcrypt
from database.db import DB_PATH
from services.encriptacion import validar_contrasena_fuerte, generar_contrasena_segura
from services.permisos import ROLES_DISPONIBLES, obtener_permisos_rol
from services.sincronizacion import notificar_cambio


# =============================================================================
# GESTIÓN DE USUARIOS
# =============================================================================

def get_username_by_id(usuario_id: int) -> str:
    """
    Obtiene el nombre de usuario por su ID.
    Args:
        usuario_id: ID del usuario
    Returns:
        Nombre de usuario o None si no existe
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('SELECT username FROM usuarios WHERE id = ?', (usuario_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] if resultado else None


def crear_usuario(username: str, password: str, rol: str = 'operador', debe_cambiar_password: bool = True) -> int:
    """
    Crea un nuevo usuario en el sistema.
    Args:
        username: Nombre de usuario único
        password: Contraseña en texto plano
        rol: Rol del usuario (admin, supervisor, operador)
        debe_cambiar_password: Si debe cambiar contraseña en primer login
    Returns:
        ID del usuario creado
    Raises:
        ValueError: Si el usuario ya existe o la contraseña no es válida
    """
    # Validar rol
    if rol not in ROLES_DISPONIBLES:
        raise ValueError(f"Rol inválido. Roles disponibles: {list(ROLES_DISPONIBLES.keys())}")

    # Validar contraseña
    es_valida, mensaje = validar_contrasena_fuerte(password)
    if not es_valida:
        raise ValueError(f"Contraseña inválida: {mensaje}")

    # Hash de contraseña
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol, debe_cambiar_password)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, rol, 1 if debe_cambiar_password else 0))

        usuario_id = cursor.lastrowid
        conexion.commit()

        # Notificar cambio
        notificar_cambio("usuarios", "INSERT", {
            "id": usuario_id,
            "username": username,
            "rol": rol
        })

        return usuario_id

    except sqlite3.IntegrityError:
        raise ValueError("El nombre de usuario ya existe")
    finally:
        conexion.close()


def cambiar_contrasena_usuario(usuario_id: int, contrasena_actual: str, nueva_contrasena: str) -> None:
    """
    Cambia la contraseña de un usuario.
    Args:
        usuario_id: ID del usuario
        contrasena_actual: Contraseña actual
        nueva_contrasena: Nueva contraseña
    Raises:
        ValueError: Si la contraseña actual es incorrecta o la nueva no es válida
    """
    # Validar nueva contraseña
    es_valida, mensaje = validar_contrasena_fuerte(nueva_contrasena)
    if not es_valida:
        raise ValueError(f"Nueva contraseña inválida: {mensaje}")

    # Verificar contraseña actual
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT password FROM usuarios WHERE id = ?", (usuario_id,))
    resultado = cursor.fetchone()

    if not resultado:
        conexion.close()
        raise ValueError("Usuario no encontrado")

    try:
        if not bcrypt.checkpw(contrasena_actual.encode(), resultado[0].encode()):
            raise ValueError("Contraseña actual incorrecta")
    except Exception:
        raise ValueError("Error al verificar contraseña actual")

    # Hash de nueva contraseña
    nueva_password_hash = bcrypt.hashpw(nueva_contrasena.encode(), bcrypt.gensalt()).decode()

    # Actualizar en BD
    cursor.execute("""
        UPDATE usuarios SET password = ?, debe_cambiar_password = 0
        WHERE id = ?
    """, (nueva_password_hash, usuario_id))
    conexion.commit()
    conexion.close()

    # Notificar cambio
    notificar_cambio("usuarios", "UPDATE", {
        "id": usuario_id,
        "cambio": "password"
    })


def cambiar_rol_usuario(usuario_id: int, nuevo_rol: str) -> None:
    """
    Cambia el rol de un usuario.
    Args:
        usuario_id: ID del usuario
        nuevo_rol: Nuevo rol
    Raises:
        ValueError: Si el rol es inválido
    """
    if nuevo_rol not in ROLES_DISPONIBLES:
        raise ValueError(f"Rol inválido. Roles disponibles: {list(ROLES_DISPONIBLES.keys())}")

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (nuevo_rol, usuario_id))
    conexion.commit()
    conexion.close()

    # Notificar cambio
    notificar_cambio("usuarios", "UPDATE", {
        "id": usuario_id,
        "nuevo_rol": nuevo_rol
    })


def eliminar_usuario(usuario_id: int) -> None:
    """
    Elimina un usuario del sistema.
    Args:
        usuario_id: ID del usuario a eliminar
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conexion.commit()
    conexion.close()

    # Notificar cambio
    notificar_cambio("usuarios", "DELETE", {
        "id": usuario_id
    })


def listar_usuarios() -> list:
    """
    Retorna lista de todos los usuarios (sin contraseñas).
    Returns:
        Lista de diccionarios con datos de usuarios
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, username, rol, debe_cambiar_password
        FROM usuarios ORDER BY username
    """)
    usuarios = cursor.fetchall()
    conexion.close()

    return [{
        'id': u[0],
        'username': u[1],
        'rol': u[2],
        'debe_cambiar_password': bool(u[3])
    } for u in usuarios]


def obtener_usuario_por_id(usuario_id: int) -> dict | None:
    """
    Obtiene datos de un usuario por ID.
    Args:
        usuario_id: ID del usuario
    Returns:
        Diccionario con datos del usuario o None si no existe
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, username, rol, debe_cambiar_password
        FROM usuarios WHERE id = ?
    """, (usuario_id,))
    usuario = cursor.fetchone()
    conexion.close()

    if usuario:
        return {
            'id': usuario[0],
            'username': usuario[1],
            'rol': usuario[2],
            'debe_cambiar_password': bool(usuario[3])
        }
    return None


def generar_contrasena_temporal() -> str:
    """
    Genera una contraseña temporal segura para nuevos usuarios.
    Returns:
        Contraseña temporal
    """
    return generar_contrasena_segura(10)