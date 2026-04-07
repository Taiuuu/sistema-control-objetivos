# =============================================================================
# VESP Organizations - Rutas de Supervisores API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models.supervisores import (
    agregar_supervisor, listar_supervisores, obtener_supervisor,
    actualizar_supervisor, dar_de_baja_supervisor
)

supervisores_bp = Blueprint('supervisores', __name__)

@supervisores_bp.route('', methods=['GET'])
@jwt_required()
def get_supervisores():
    """Obtener lista de supervisores."""
    try:
        supervisores = listar_supervisores()
        return jsonify([{
            'id': sup[0],
            'nombre': sup[1],
            'activo': sup[2]
        } for sup in supervisores]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@supervisores_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_supervisor(id):
    """Obtener supervisor por ID."""
    try:
        sup = obtener_supervisor(id)
        if sup:
            return jsonify({
                'id': sup[0],
                'nombre': sup[1],
                'activo': sup[2]
            }), 200
        return jsonify({'error': 'Supervisor no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@supervisores_bp.route('', methods=['POST'])
@jwt_required()
def create_supervisor():
    """Crear nuevo supervisor."""
    try:
        data = request.get_json()
        nombre = data.get('nombre')

        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400

        agregar_supervisor(nombre)
        return jsonify({'message': 'Supervisor creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@supervisores_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_supervisor(id):
    """Actualizar supervisor."""
    try:
        data = request.get_json()
        nombre = data.get('nombre')

        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400

        actualizar_supervisor(id, nombre)
        return jsonify({'message': 'Supervisor actualizado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@supervisores_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_supervisor(id):
    """Dar de baja supervisor."""
    try:
        dar_de_baja_supervisor(id)
        return jsonify({'message': 'Supervisor dado de baja'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500