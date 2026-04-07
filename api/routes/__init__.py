# =============================================================================
# VESP Organizations - Registro de Rutas API
# =============================================================================

from api.routes.objetivos import objetivos_bp
from api.routes.supervisores import supervisores_bp
from api.routes.pasadas import pasadas_bp
from api.routes.reportes import reportes_bp
from api.routes.auth import auth_bp
from api.routes.sse import sse_bp

def register_routes(app):
    """Registra todos los blueprints de rutas en la aplicación Flask."""
    app.register_blueprint(objetivos_bp, url_prefix='/api/objetivos')
    app.register_blueprint(supervisores_bp, url_prefix='/api/supervisores')
    app.register_blueprint(pasadas_bp, url_prefix='/api/pasadas')
    app.register_blueprint(reportes_bp, url_prefix='/api/reportes')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(sse_bp, url_prefix='/api/sse', name='vesp_sse')