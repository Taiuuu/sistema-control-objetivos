# =============================================================================
# VESP Organizations - Rutas de Autenticación API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.sesion import get_usuario_id
import sqlite3
import bcrypt
from database.db import DB_PATH

auth_bp = Blueprint('auth', __name__)


def _verificar_usuario(usuario: str, contrasena: str) -> dict:
    """
    Verifica credenciales contra la base de datos.
    Returns: dict con 'valido', 'usuario_id', 'rol', 'mensaje'
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, password, rol, debe_cambiar_password 
            FROM usuarios WHERE username = ?
        """, (usuario,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return {'valido': False, 'mensaje': 'Usuario no encontrado'}
        
        usuario_id, username, password_hash, rol, debe_cambiar = resultado
        
        # Verificar contraseña con bcrypt
        if not bcrypt.checkpw(contrasena.encode(), password_hash.encode()):
            return {'valido': False, 'mensaje': 'Contraseña incorrecta'}
        
        return {
            'valido': True,
            'usuario_id': usuario_id,
            'username': username,
            'rol': rol,
            'debe_cambiar_password': bool(debe_cambiar)
        }
    finally:
        conexion.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de login con validación de contraseña.
    """
    data = request.get_json()
    usuario = data.get('usuario', '')
    contrasena = data.get('contrasena', '')

    if not usuario or not contrasena:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

    # Validar credenciales
    resultado = _verificar_usuario(usuario, contrasena)
    
    if not resultado['valido']:
        return jsonify({'error': resultado['mensaje']}), 401

    # Crear token JWT
    access_token = create_access_token(
        identity=resultado['username'],
        additional_claims={
            'usuario_id': resultado['usuario_id'],
            'rol': resultado['rol']
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'username': resultado['username'],
        'rol': resultado['rol'],
        'debe_cambiar_password': resultado['debe_cambiar_password']
    }), 200


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Endpoint protegido de ejemplo."""
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hola, {current_user}!'}), 200