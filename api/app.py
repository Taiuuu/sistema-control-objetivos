# =============================================================================
# VESP Organizations - API REST Avanzada
# Aplicación principal de Flask
# =============================================================================

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sse import sse
from api.routes import register_routes
from database.db import DB_PATH
import os

app = Flask(__name__)

# Configuración JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'vesp-api-secret-key-2024')
jwt = JWTManager(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# SSE para notificaciones
app.config['REDIS_URL'] = 'redis://localhost:6379/0'  # Opcional, usar memoria por defecto
app.register_blueprint(sse, url_prefix='/api/stream')

# CORS para desarrollo
CORS(app)

# Registrar rutas
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)