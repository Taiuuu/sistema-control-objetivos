# =============================================================================
# VESP Organizations - Rutas de Server-Sent Events API
# =============================================================================

import logging
from hmac import compare_digest

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from flask_sse import sse
from redis.exceptions import RedisError

sse_bp = Blueprint('sse', __name__)
logger = logging.getLogger(__name__)

@sse_bp.route('/events')
@jwt_required()
def stream():
    """Entrega notificaciones SSE reales a clientes autenticados."""
    return sse.stream()

@sse_bp.route('/publish', methods=['POST'])
def publish():
    """Publica un evento SSE autorizado desde el sincronizador local."""
    expected_token = current_app.config["SSE_PUBLISH_TOKEN"]
    authorization = request.headers.get("Authorization", "")
    if not expected_token or not compare_digest(
        authorization.encode("utf-8"),
        f"Bearer {expected_token}".encode("utf-8")
    ):
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    try:
        sse.publish(data, type='data_change')
    except RedisError:
        logger.exception("No se pudo publicar el evento SSE en Redis.")
        return jsonify({"error": "Servicio de notificaciones no disponible"}), 503

    return {'status': 'ok'}, 200