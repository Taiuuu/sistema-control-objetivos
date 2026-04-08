# =============================================================================
# VESP Organizations - Rutas de Pasadas API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models.turnos import registrar_turno, registrar_turno_ambos, listar_turnos_del_dia

pasadas_bp = Blueprint('pasadas', __name__)

@pasadas_bp.route('', methods=['POST'])
@jwt_required()
def create_pasada():
    """Crear nueva pasada."""
    try:
        data = request.get_json()
        fecha = data.get('fecha')
        hora = data.get('hora')
        turno = data.get('turno')
        objetivo_id = data.get('objetivo_id')
        supervisor_id = data.get('supervisor_id')
        supervisor2_id = data.get('supervisor2_id')  # Opcional para ambos

        if not all([fecha, turno, objetivo_id, supervisor_id]):
            return jsonify({'error': 'Campos requeridos: fecha, turno, objetivo_id, supervisor_id'}), 400

        if supervisor2_id:
            registrar_turno_ambos(fecha, hora, turno, objetivo_id, supervisor_id, supervisor2_id)
        else:
            registrar_turno(fecha, hora, turno, objetivo_id, supervisor_id)

        return jsonify({'message': 'Pasada registrada'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pasadas_bp.route('/dia/<fecha>', methods=['GET'])
@jwt_required()
def get_pasadas_dia(fecha):
    """Obtener pasadas del día."""
    try:
        pasadas = listar_turnos_del_dia(fecha)
        return jsonify([{
            'id': p[0],
            'hora': p[1],
            'turno': p[2],
            'objetivo': p[3],
            'supervisor': p[4]
        } for p in pasadas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500