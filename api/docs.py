# =============================================================================
# VESP Organizations - Documentación API con Swagger
# =============================================================================

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask
from api.app import app

spec = APISpec(
    title="VESP Control de Objetivos API",
    version="1.0.0",
    openapi_version="3.0.3",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

# Registrar rutas en la especificación
with app.test_request_context():
    spec.path(view=app.view_functions['auth.login'])
    spec.path(view=app.view_functions['objetivos.get_objetivos'])
    spec.path(view=app.view_functions['objetivos.create_objetivo'])
    spec.path(view=app.view_functions['supervisores.get_supervisores'])
    spec.path(view=app.view_functions['supervisores.create_supervisor'])
    spec.path(view=app.view_functions['pasadas.create_pasada'])
    spec.path(view=app.view_functions['reportes.get_reporte_mensual'])
    spec.path(view=app.view_functions['reportes.get_reporte_diario'])

@app.route('/api/docs')
def get_docs():
    """Retorna la documentación OpenAPI/Swagger."""
    return spec.to_dict()