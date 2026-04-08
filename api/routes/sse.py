# =============================================================================
# VESP Organizations - Rutas de Server-Sent Events API
# =============================================================================

from flask import Blueprint, Response
from flask_jwt_extended import jwt_required
from flask_sse import sse
import json
import time

sse_bp = Blueprint('sse', __name__)

@sse_bp.route('/events')
@jwt_required()
def stream():
    """Endpoint SSE para notificaciones en tiempo real."""
    def event_stream():
        while True:
            # Mantener conexión viva
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            time.sleep(30)  # Ping cada 30 segundos

    return Response(event_stream(), mimetype='text/event-stream')

@sse_bp.route('/publish', methods=['POST'])
def publish():
    """Publica un evento SSE (llamado desde sincronización)."""
    data = request.get_json()
    if data:
        sse.publish(data, type='data_change')
    return {'status': 'ok'}, 200