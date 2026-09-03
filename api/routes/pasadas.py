# =============================================================================
# VESP Organizations - Rutas de Pasadas API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models.turnos import registrar_turno, listar_turnos_del_dia

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

        if not all([fecha, turno, objetivo_id, supervisor_id]):
            return jsonify({'error': 'Campos requeridos: fecha, turno, objetivo_id, supervisor_id'}), 400

        pasada = registrar_turno(
            fecha=fecha,
            turno=turno,
            objetivo_id=objetivo_id,
            supervisor_id=supervisor_id,
            hora=hora,
        )

        return jsonify({'message': 'Pasada registrada', 'id': pasada.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pasadas_bp.route('/dia/<fecha>', methods=['GET'])
@jwt_required()
def get_pasadas_dia(fecha):
    """Obtener pasadas del día."""
    try:
        pasadas = listar_turnos_del_dia(fecha)
        return jsonify([{
            'id': p.id,
            'fecha': p.fecha,
            'hora': p.hora,
            'turno': p.turno,
            'objetivo_id': p.objetivo_id,
            'supervisor_id': p.supervisor_id,
        } for p in pasadas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500