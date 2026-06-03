# =============================================================================
# VESP Organizations - Rutas de Objetivos API
# =============================================================================

import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models.objetivos import (
    agregar_objetivo, listar_objetivos, obtener_objetivo,
    actualizar_objetivo, dar_de_baja_objetivo
)
from models.types import Objetivo
from services.permisos import tiene_permiso

objetivos_bp = Blueprint('objetivos', __name__)


def _objetivo_a_dict(obj: Objetivo) -> dict:
    return {
        'id': obj.id,
        'nombre': obj.nombre,
        'fecha_inicio': obj.fecha_inicio,
        'fecha_fin': obj.fecha_fin,
        'dias_semana': obj.dias_semana,
        'activo': obj.es_activo(),
    }


@objetivos_bp.route('', methods=['GET'])
@jwt_required()
def get_objetivos():
    """Obtener lista de objetivos."""
    if not tiene_permiso('objetivos.ver'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        objetivos = listar_objetivos()
        return jsonify([_objetivo_a_dict(obj) for obj in objetivos]), 200
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
        return jsonify(_objetivo_a_dict(obj)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@objetivos_bp.route('', methods=['POST'])
@jwt_required()
def create_objetivo():
    """Crear nuevo objetivo."""
    if not tiene_permiso('objetivos.crear'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        data = request.get_json() or {}
        nombre = data.get('nombre')
        fecha_inicio = data.get('fecha_inicio') or datetime.date.today().isoformat()
        fecha_fin = data.get('fecha_fin')
        dias_semana = data.get('dias_semana', '1,2,3,4,5')

        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400

        creado = agregar_objetivo(nombre, fecha_inicio, dias_semana, fecha_fin)
        return jsonify(_objetivo_a_dict(creado)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@objetivos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_objetivo(id):
    """Actualizar objetivo."""
    if not tiene_permiso('objetivos.editar'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        data = request.get_json() or {}
        nombre = data.get('nombre')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        dias_semana = data.get('dias_semana')

        if not nombre or not fecha_inicio or not dias_semana:
            return jsonify({'error': 'Nombre, fecha_inicio y dias_semana requeridos'}), 400

        actualizado = actualizar_objetivo(id, nombre, fecha_inicio, dias_semana, fecha_fin)
        return jsonify(_objetivo_a_dict(actualizado)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@objetivos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_objetivo(id):
    """Dar de baja objetivo."""
    if not tiene_permiso('objetivos.eliminar'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        baja = dar_de_baja_objetivo(id)
        return jsonify(_objetivo_a_dict(baja)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
