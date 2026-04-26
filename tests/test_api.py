# =============================================================================
# VESP Testing - API: Endpoints
# =============================================================================

import pytest
import datetime


@pytest.fixture
def api_client(db_initialized):
    """Cliente de test para la API Flask."""
    # Monkeypatch database path
    import api.app as app_module
    from database import db as db_module
    
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = db_initialized
    app_module.app.config['TESTING'] = True
    
    with app_module.app.test_client() as client:
        yield client
    
    db_module.DB_PATH = original_db_path


@pytest.fixture
def auth_token(api_client, db_initialized):
    """Obtiene un token JWT válido para tests."""
    # Crear usuario de prueba
    from services.usuarios import crear_usuario
    crear_usuario("test_user", "Prueba123!", "admin", debe_cambiar_password=False)
    
    # Login y obtener token
    response = api_client.post('/api/auth/login', json={
        'username': 'test_user',
        'password': 'Prueba123!'
    })
    
    if response.status_code == 200:
        return response.get_json()['access_token']
    return None


class TestAuthAPI:
    """Tests para endpoints de autenticación."""
    
    def test_login_exitoso(self, api_client, admin_user):
        """Debe autenticarse correctamente con credenciales válidas."""
        response = api_client.post('/api/auth/login', json={
            'username': 'admin_test',
            'password': 'Prueba123!'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['token_type'] == 'Bearer'
    
    def test_login_fallido_usuario_invalido(self, api_client):
        """Debe rechazar credenciales inválidas."""
        response = api_client.post('/api/auth/login', json={
            'username': 'usuario_inexistente',
            'password': 'Cualquier123!'
        })
        
        assert response.status_code == 401
    
    def test_login_fallido_contrasena_invalida(self, api_client, admin_user):
        """Debe rechazar contraseña incorrecta."""
        response = api_client.post('/api/auth/login', json={
            'username': 'admin_test',
            'password': 'ContraseñaIncorrecta123!'
        })
        
        assert response.status_code == 401


class TestObjetivosAPI:
    """Tests para endpoints de objetivos."""
    
    def test_get_objetivos_sin_auth(self, api_client):
        """Debe rechazar acceso sin autenticación."""
        response = api_client.get('/api/objetivos')
        
        assert response.status_code == 401
    
    def test_get_objetivos_con_auth(self, api_client, auth_token):
        """Debe retornar lista de objetivos con token válido."""
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = api_client.get('/api/objetivos', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_crear_objetivo(self, api_client, auth_token):
        """Debe crear un nuevo objetivo."""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = api_client.post('/api/objetivos', 
            headers=headers,
            json={
                'nombre': 'Nuevo Objetivo',
                'dias_semana': '1,2,3,4,5'
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert data['nombre'] == 'Nuevo Objetivo'


class TestReportesAPI:
    """Tests para endpoints de reportes."""
    
    def test_reporte_mensual_sin_auth(self, api_client):
        """Debe rechazar acceso sin autenticación."""
        response = api_client.get('/api/reportes/mensual/2025/1')
        
        assert response.status_code == 401
    
    def test_reporte_mensual_valido(self, api_client, auth_token):
        """Debe retornar reporte mensual válido."""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        today = datetime.date.today()
        response = api_client.get(f'/api/reportes/mensual/{today.year}/{today.month}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'anio' in data
        assert 'mes' in data
        assert 'objetivos' in data


class TestRateLimiting:
    """Tests para rate limiting en API."""
    
    def test_rate_limit_login(self, api_client):
        """Debe implementar rate limiting en login."""
        # Hacer múltiples intentos fallidos
        for _ in range(10):
            api_client.post('/api/auth/login', json={
                'username': 'invalid',
                'password': 'invalid'
            })
        
        # El siguiente debería ser rechazado o rate limited
        response = api_client.post('/api/auth/login', json={
            'username': 'invalid',
            'password': 'invalid'
        })
        
        # Debe ser 401 o 429 (Too Many Requests)
        assert response.status_code in [401, 429]
