# =============================================================================
# VESP Organizations - Rutas de Objetivos API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models.objetivos import (
    agregar_objetivo, listar_objetivos, obtener_objetivo,
    actualizar_objetivo, dar_de_baja_objetivo
)
from services.permisos import tiene_permiso

objetivos_bp = Blueprint('objetivos', __name__)

@objetivos_bp.route('', methods=['GET'])
@jwt_required()
def get_objetivos():
    """Obtener lista de objetivos."""
    if not tiene_permiso('objetivos.ver'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        objetivos = listar_objetivos()
        return jsonify([{
            'id': obj[0],
            'nombre': obj[1],
            'descripcion': obj[2],
            'activo': obj[3]
        } for obj in objetivos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@objetivos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_objetivo(id):
    """Obtener objetivo por ID."""
    if not tiene_permiso('objetivos.ver'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        obj = obtener_objetivo(id)
        if obj:
            return jsonify({
                'id': obj[0],
                'nombre': obj[1],
                'descripcion': obj[2],
                'activo': obj[3]
            }), 200
        return jsonify({'error': 'Objetivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@objetivos_bp.route('', methods=['POST'])
@jwt_required()
def create_objetivo():
    """Crear nuevo objetivo."""
    if not tiene_permiso('objetivos.crear'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        data = request.get_json()
        nombre = data.get('nombre')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        dias_semana = data.get('dias_semana', '1,2,3,4,5')  # Default L-V

        if not nombre or not fecha_inicio:
            return jsonify({'error': 'Nombre y fecha_inicio requeridos'}), 400

        agregar_objetivo(nombre, fecha_inicio, fecha_fin, dias_semana)
        return jsonify({'message': 'Objetivo creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@objetivos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_objetivo(id):
    """Actualizar objetivo."""
    if not tiene_permiso('objetivos.editar'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        data = request.get_json()
        nombre = data.get('nombre')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        dias_semana = data.get('dias_semana')

        if not nombre or not fecha_inicio:
            return jsonify({'error': 'Nombre y fecha_inicio requeridos'}), 400

        actualizar_objetivo(id, nombre, fecha_inicio, fecha_fin, dias_semana)
        return jsonify({'message': 'Objetivo actualizado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@objetivos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_objetivo(id):
    """Dar de baja objetivo."""
    if not tiene_permiso('objetivos.eliminar'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        dar_de_baja_objetivo(id)
        return jsonify({'message': 'Objetivo dado de baja'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500