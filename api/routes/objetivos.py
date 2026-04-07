# =============================================================================
# VESP Organizations - Rutas de Objetivos API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models.objetivos import (
    agregar_objetivo, listar_objetivos, obtener_objetivo,
    actualizar_objetivo, dar_de_baja_objetivo
)

objetivos_bp = Blueprint('objetivos', __name__)

@objetivos_bp.route('', methods=['GET'])
@jwt_required()
def get_objetivos():
    """Obtener lista de objetivos."""
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
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        descripcion = data.get('descripcion', '')

        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400

        agregar_objetivo(nombre, descripcion)
        return jsonify({'message': 'Objetivo creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@objetivos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_objetivo(id):
    """Actualizar objetivo."""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        descripcion = data.get('descripcion')

        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400

        actualizar_objetivo(id, nombre, descripcion)
        return jsonify({'message': 'Objetivo actualizado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@objetivos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_objetivo(id):
    """Dar de baja objetivo."""
    try:
        dar_de_baja_objetivo(id)
        return jsonify({'message': 'Objetivo dado de baja'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500