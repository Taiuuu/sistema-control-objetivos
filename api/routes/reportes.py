# =============================================================================
# VESP Organizations - Rutas de Reportes API
# =============================================================================

import calendar
from datetime import date

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.reportes import generar_reporte_mensual, generar_reporte_diario
from services.permisos import tiene_permiso
from services.reportes_unificados.consultas import crear_datos_para_exportar
from services.reportes_unificados.datos import crear_datos_diarios

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/mensual/<int:anio>/<int:mes>', methods=['GET'])
@jwt_required()
def get_reporte_mensual(anio, mes):
    """Obtener reporte mensual."""
    if not tiene_permiso('reportes.ver'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        inicio = date(anio, mes, 1)
        fin = date(anio, mes, calendar.monthrange(anio, mes)[1])
        datos = crear_datos_para_exportar(
            {
                "tipo_informe": "mensual",
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "objetivo_ids": None,
                "supervisor_ids": None,
                "turnos": None,
                "equipo_id": None,
            }
        )
        reporte = {
            "anio": anio,
            "mes": mes,
            "periodo": f"{mes:02d}/{anio}",
            "total_dias": calendar.monthrange(anio, mes)[1],
            "objetivos": [
                {
                    "id": fila["id"],
                    "nombre": fila["objetivo"],
                    "dias_esperados": fila["dias_esperados"],
                    "dias_con_pasada": fila["dias_con_pasada"],
                    "dias_sin_pasada": fila["dias_sin_pasada"],
                    "dias_sin_control": fila["dias_sin_pasada"],
                    "cumplimiento_porcentaje": fila["cumplimiento"] * 100,
                    "cumplimiento": fila["cumplimiento"] * 100,
                }
                for fila in datos.filas
            ],
            "cumplimiento_total": datos.totales["cumplimiento_total"] * 100,
        }
        return jsonify(reporte), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reportes_bp.route('/diario/<fecha>', methods=['GET'])
@jwt_required()
def get_reporte_diario(fecha):
    """Obtener reporte diario."""
    if not tiene_permiso('reportes.ver'):
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        reporte_original = generar_reporte_diario(fecha)
        datos = crear_datos_diarios(reporte_original)
        reporte = {
            "fecha": reporte_original["fecha"],
            "pasadas": [
                {
                    "id": fila["id"],
                    "hora": fila["hora"].strftime("%H:%M"),
                    "turno": fila["turno"],
                    "objetivo": fila["objetivo"],
                    "supervisor": fila["supervisor"],
                }
                for fila in datos.filas
            ],
            "total": datos.totales["pasadas"],
            "cumplimiento_porcentaje": datos.totales["cumplimiento"] * 100,
        }
        return jsonify(reporte), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500