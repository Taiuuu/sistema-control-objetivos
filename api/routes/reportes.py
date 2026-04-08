# =============================================================================
# VESP Organizations - Rutas de Reportes API
# =============================================================================

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.reportes import generar_reporte_mensual, generar_reporte_diario

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/mensual/<int:anio>/<int:mes>', methods=['GET'])
@jwt_required()
def get_reporte_mensual(anio, mes):
    """Obtener reporte mensual."""
    try:
        reporte = generar_reporte_mensual(anio, mes)
        return jsonify(reporte), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reportes_bp.route('/diario/<fecha>', methods=['GET'])
@jwt_required()
def get_reporte_diario(fecha):
    """Obtener reporte diario."""
    try:
        reporte = generar_reporte_diario(fecha)
        return jsonify(reporte), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500