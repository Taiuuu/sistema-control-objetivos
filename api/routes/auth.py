# =============================================================================
# VESP Organizations - Rutas de Autenticación API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.sesion import get_usuario_id

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de login simplificado (sin validación de contraseña por ahora)."""
    data = request.get_json()
    usuario = data.get('usuario', '')

    if not usuario:
        return jsonify({'error': 'Usuario requerido'}), 400

    # Por ahora, aceptar cualquier usuario y crear token
    # TODO: Integrar con sistema de usuarios real
    access_token = create_access_token(identity=usuario)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Endpoint protegido de ejemplo."""
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hola, {current_user}!'}), 200