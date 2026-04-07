# =============================================================================
# VESP Testing - Services: Usuarios
# =============================================================================

import pytest
import sqlite3
from services.usuarios import crear_usuario, cambiar_contrasena, obtener_usuarios, obtener_usuario_por_id


class TestCrearUsuario:
    """Tests para creación de usuarios."""
    
    def test_crear_usuario_operador(self, db_initialized):
        """Debe crear un usuario operador correctamente."""
        user_id = crear_usuario("nuevo_user", "Contrasena123!", "operador", debe_cambiar_password=False)
        
        assert user_id > 0
        
        conexion = sqlite3.connect(db_initialized)
        cursor = conexion.cursor()
        cursor.execute("SELECT username, rol, debe_cambiar_password FROM usuarios WHERE id = ?", (user_id,))
        resultado = cursor.fetchone()
        conexion.close()
        
        assert resultado is not None
        assert resultado[0] == "nuevo_user"
        assert resultado[1] == "operador"
        assert resultado[2] == 0
    
    def test_crear_usuario_admin(self, db_initialized):
        """Debe crear un usuario admin correctamente."""
        user_id = crear_usuario("admin_nuevo", "Contrasena123!", "admin", debe_cambiar_password=False)
        
        assert user_id > 0
        
        conexion = sqlite3.connect(db_initialized)
        cursor = conexion.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE id = ?", (user_id,))
        resultado = cursor.fetchone()
        conexion.close()
        
        assert resultado[0] == "admin"
    
    def test_usuario_duplicado(self, db_initialized):
        """No debe permitir usuarios con username duplicado."""
        crear_usuario("duplicado", "Contrasena123!", "operador")
        
        with pytest.raises(Exception):
            crear_usuario("duplicado", "Otra123!", "operador")
    
    def test_contrasena_hasheada(self, db_initialized):
        """La contraseña debe guardarse hasheada."""
        user_id = crear_usuario("usuario_secured", "Contrasena123!", "operador")
        
        conexion = sqlite3.connect(db_initialized)
        cursor = conexion.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE id = ?", (user_id,))
        password_hash = cursor.fetchone()[0]
        conexion.close()
        
        assert password_hash != "Contrasena123!"
        assert len(password_hash) > 20  # bcrypt hash es largo


class TestObtenerUsuarios:
    """Tests para obtención de usuarios."""
    
    def test_obtener_todos_usuarios(self, db_initialized, admin_user, operador_user):
        """Debe obtener lista de todos los usuarios."""
        usuarios = obtener_usuarios()
        
        assert len(usuarios) >= 2
        usernames = [u['username'] for u in usuarios]
        assert "admin_test" in usernames
        assert "operador_test" in usernames
    
    def test_obtener_usuario_por_id(self, db_initialized, admin_user):
        """Debe obtener un usuario específico por ID."""
        usuario = obtener_usuario_por_id(admin_user['id'])
        
        assert usuario is not None
        assert usuario['username'] == "admin_test"
        assert usuario['rol'] == "admin"
    
    def test_obtener_usuario_inexistente(self, db_initialized):
        """Debe retornar None para usuario inexistente."""
        usuario = obtener_usuario_por_id(99999)
        
        assert usuario is None


class TestCambiarContrasena:
    """Tests para cambio de contraseña."""
    
    def test_cambiar_contrasena_valida(self, db_initialized, admin_user):
        """Debe cambiar la contraseña correctamente."""
        cambiar_contrasena(admin_user['id'], "NuevaContrasena123!")
        
        # Verificar que se actualizó
        conexion = sqlite3.connect(db_initialized)
        cursor = conexion.cursor()
        cursor.execute("SELECT debe_cambiar_password FROM usuarios WHERE id = ?", (admin_user['id'],))
        resultado = cursor.fetchone()
        conexion.close()
        
        assert resultado[0] == 0  # Debe cambiar flag después de cambiar contraseña
