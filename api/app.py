# =============================================================================
# VESP Organizations - API REST Avanzada
# Aplicación principal de Flask
# =============================================================================

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from api.routes import register_routes
from database.db import DB_PATH
import os

app = Flask(__name__)

# Configuración JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'vesp-api-secret-key-2024')
jwt = JWTManager(app)

# CORS para desarrollo
CORS(app)

# Registrar rutas
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)