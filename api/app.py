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
import os

app = Flask(__name__)

# Configuración JWT
jwt_secret = os.environ.get('VESP_JWT_SECRET')
if not jwt_secret:
    raise RuntimeError(
        'Falta la variable de entorno VESP_JWT_SECRET. Definila en .env antes de iniciar la API.'
    )
app.config["JWT_SECRET_KEY"] = jwt_secret
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

@app.route('/')
def index():
    """Página de bienvenida de la API."""
    return {
        'message': 'VESP Control de Objetivos API',
        'version': '1.0.0',
        'status': 'running',
        'docs': 'Ver README.md para documentación'
    }, 200

if __name__ == '__main__':
    host = os.environ.get('VESP_API_HOST', '127.0.0.1')
    port = int(os.environ.get('VESP_API_PORT', '5000'))
    debug = os.environ.get('VESP_API_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host=host, port=port)