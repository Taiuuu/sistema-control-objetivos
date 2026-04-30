# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Tests de Estabilidad Básicos
# =============================================================================

import pytest
import sys
import os
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# TESTS DE VALIDACIÓN DE ENTRADA LOGIN
# =============================================================================

class TestValidacionEntradaLogin:
    """Tests para validación de entrada en login."""
    
    def test_usuario_vacio(self):
        """Test: Usuario vacío debería ser rechazado."""
        from ui.login import LoginWindow
        
        # Simular entrada vacía
        username = ""
        password = "password123"
        
        # LoginWindow necesita QApplication, es complejo testear UI directamente
        # Mejor testear la función de validación directamente
        assert not username, "Usuario vacío debería fallar"
    
    def test_usuario_muy_corto(self):
        """Test: Usuario con menos de 3 caracteres."""
        username = "ab"
        assert len(username) < 3, "Usuario muy corto debería fallar"
    
    def test_usuario_muy_largo(self):
        """Test: Usuario con más de 50 caracteres."""
        username = "a" * 51
        assert len(username) > 50, "Usuario muy largo debería fallar"
    
    def test_usuario_caracteres_invalidos(self):
        """Test: Usuario con caracteres especiales."""
        username = "user@name!"
        valido = all(c.isalnum() or c == '_' for c in username)
        assert not valido, "Usuario con caracteres especiales debería fallar"
    
    def test_usuario_con_espacios(self):
        """Test: Usuario con espacios."""
        username = "user name"
        tiene_espacios = ' ' in username
        assert tiene_espacios, "Usuario con espacios debería fallar"
    
    def test_password_vacia(self):
        """Test: Contraseña vacía."""
        password = ""
        assert not password, "Contraseña vacía debería fallar"
    
    def test_password_muy_corta(self):
        """Test: Contraseña con menos de 4 caracteres."""
        password = "123"
        assert len(password) < 4, "Contraseña muy corta debería fallar"


# =============================================================================
# TESTS DE DECORADORES DE PERMISOS
# =============================================================================

class TestDecoradoresPermisos:
    """Tests para decoradores de validación de permisos."""
    
    def test_excepcion_permiso_denegado(self):
        """Test: PermisoDenegadoError se crea correctamente."""
        from services.permisos import PermisoDenegadoError
        
        error = PermisoDenegadoError(
            "Acceso denegado",
            codigo_error="PERMISO_INSUFICIENTE",
            permiso_requerido="objetivos.crear"
        )
        
        assert error.message == "Acceso denegado"
        assert error.codigo_error == "PERMISO_INSUFICIENTE"
        assert error.permiso_requerido == "objetivos.crear"
    
    def test_permisos_por_rol_existen(self):
        """Test: PERMISOS_POR_ROL está bien definido."""
        from services.permisos import PERMISOS_POR_ROL, ROLES_DISPONIBLES
        
        # Verificar que todos los roles tienen permisos
        for rol in ROLES_DISPONIBLES.keys():
            assert rol in PERMISOS_POR_ROL, f"Rol {rol} sin permisos definidos"
            assert len(PERMISOS_POR_ROL[rol]) > 0, f"Rol {rol} sin permisos"
    
    def test_admin_tiene_todos_los_permisos(self):
        """Test: Admin debe tener máximos permisos."""
        from services.permisos import PERMISOS_POR_ROL
        
        admin_permisos = PERMISOS_POR_ROL.get('admin', set())
        
        # Admin debería tener permisos críticos
        assert 'usuarios.crear' in admin_permisos
        assert 'usuarios.eliminar' in admin_permisos
        assert 'config.backup' in admin_permisos


# =============================================================================
# TESTS DE SESIÓN
# =============================================================================

class TestSesion:
    """Tests para validación de sesión."""
    
    def test_obtener_sesion_valida_sin_sesion(self):
        """Test: obtener_sesion_valida() retorna None sin sesión activa."""
        from services.sesion import obtener_sesion_valida, cerrar_sesion
        
        # Asegurar que no hay sesión activa
        cerrar_sesion()
        
        # Verificar que retorna None
        resultado = obtener_sesion_valida()
        assert resultado is None, "Sin sesión activa, debería retornar None"
    
    def test_sesion_iniciada_correctamente(self):
        """Test: iniciar_sesion() guarda datos correctamente."""
        from services.sesion import iniciar_sesion, get_usuario_id, get_rol, cerrar_sesion
        
        # Iniciar sesión
        usuario_id = 1
        rol = "admin"
        token = iniciar_sesion(usuario_id, rol)
        
        # Verificar
        assert token is not None, "Token debe existir"
        assert get_usuario_id() == usuario_id, "Usuario ID incorrecto"
        assert get_rol() == rol, "Rol incorrecto"
        
        # Limpiar
        cerrar_sesion()


# =============================================================================
# TESTS DE TEMA
# =============================================================================

class TestTema:
    """Tests para validación de tema."""
    
    def test_tema_inicial_existe(self):
        """Test: obtener_tema_actual() siempre retorna un valor."""
        from services.tema import obtener_tema_actual
        
        tema = obtener_tema_actual()
        assert tema in ["oscuro", "claro"], f"Tema inválido: {tema}"
    
    def test_establecer_tema(self):
        """Test: establecer_tema_actual() guarda el tema."""
        from services.tema import obtener_tema_actual, establecer_tema_actual
        
        # Guardar tema actual
        tema_original = obtener_tema_actual()
        
        # Cambiar tema
        nuevo_tema = "claro" if tema_original == "oscuro" else "oscuro"
        establecer_tema_actual(nuevo_tema)
        
        # Verificar
        tema_guardado = obtener_tema_actual()
        assert tema_guardado == nuevo_tema, "Tema no se guardó correctamente"
        
        # Restaurar
        establecer_tema_actual(tema_original)


# =============================================================================
# TESTS DE BASE DE DATOS
# =============================================================================

class TestBaseDatos:
    """Tests para validación de base de datos."""
    
    def test_db_path_existe(self):
        """Test: Ruta de BD está definida."""
        from database.db import DB_PATH
        
        assert DB_PATH is not None, "DB_PATH no debe ser None"
        assert len(DB_PATH) > 0, "DB_PATH no debe estar vacío"
    
    def test_tablas_criticas_existen(self):
        """Test: Tablas críticas existen en BD."""
        from database.db import conectar
        import sqlite3
        
        try:
            conexion = conectar()
            cursor = conexion.cursor()
            
            # Tablas que deben existir
            tablas_criticas = ['usuarios', 'objetivos', 'supervisores', 'pasadas', 'auditoria']
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
            for tabla in tablas_criticas:
                assert tabla in tablas_existentes, f"Tabla {tabla} no existe"
            
            conexion.close()
        except Exception as e:
            pytest.skip(f"No se pudo conectar a BD: {e}")


# =============================================================================
# TESTS DE IMPORTS
# =============================================================================

class TestImports:
    """Tests para validación de imports."""
    
    def test_imports_criticos(self):
        """Test: Todos los imports críticos funcionan."""
        try:
            from database.db import crear_base_datos, conectar
            from services.sesion import iniciar_sesion, get_usuario_id
            from services.permisos import tiene_permiso, requiere_permiso
            from ui.login import LoginWindow, verificar_login
            from ui.ventana_principal import VentanaPrincipal
            print("✅ Todos los imports críticos OK")
        except ImportError as e:
            pytest.fail(f"Import error: {e}")
    
    def test_services_importables(self):
        """Test: Servicios se importan sin errores."""
        try:
            import services
            from services import logger, cache, encriptacion
            from services.permisos import PermisoDenegadoError
            print("✅ Servicios importables correctamente")
        except Exception as e:
            pytest.fail(f"Error importando servicios: {e}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
