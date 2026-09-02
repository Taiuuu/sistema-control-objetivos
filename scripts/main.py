# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Archivo principal de entrada de la aplicación
# =============================================================================

import sys
import os
import logging
import traceback
from pathlib import Path
from typing import Optional

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from ui.login import LoginWindow
from ui.ventana_principal import VentanaPrincipal
from database.db import crear_base_datos, migrar_supervisor3, migrar_supervisores_alta_baja, migrar_usuarios_activo, migrar_feriados
from services.backup import hacer_backup
from services.actualizador import verificar_actualizacion
from services.tema import obtener_tema_actual, establecer_tema_actual
from services.api_rest import iniciar_api_rest


def cargar_qss(nombre: str) -> str:
    """Carga un stylesheet empaquetado junto con la aplicación."""
    ruta = Path(__file__).resolve().parent.parent / "ui" / nombre
    try:
        return ruta.read_text(encoding="utf-8")
    except OSError:
        return ""


# =============================================================================
# UTILIDADES DE ERROR HANDLING
# =============================================================================

def configurar_logging() -> logging.Logger:
    """Configura el sistema de logging básico."""
    logger = logging.getLogger('vesp_main')
    logger.setLevel(logging.INFO)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def mostrar_error_critico(titulo: str, mensaje: str, detalle: str = "") -> None:
    """Muestra un mensaje de error crítico al usuario."""
    try:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        if detalle:
            msg_box.setDetailedText(detalle)
        msg_box.exec()
    except Exception:
        # Fallback si Qt no está disponible
        print(f"❌ {titulo}: {mensaje}")
        if detalle:
            print(f"Detalle: {detalle}")


def inicializar_componente(logger: logging.Logger, nombre: str, funcion, *args, **kwargs) -> bool:
    """
    Inicializa un componente con error handling robusto.

    Args:
        logger: Logger para registrar eventos
        nombre: Nombre del componente para logging
        funcion: Función a ejecutar
        *args, **kwargs: Argumentos para la función

    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        logger.info(f"Inicializando {nombre}...")
        funcion(*args, **kwargs)
        logger.info(f"✅ {nombre} inicializado correctamente")
        return True
    except Exception as e:
        error_msg = f"Error inicializando {nombre}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"⚠️  {error_msg}")
        return False


def aplicar_tema(app: QApplication, nombre_tema: str) -> None:
    """Aplica el único stylesheet correspondiente al tema activo."""
    if nombre_tema not in {"oscuro", "claro"}:
        nombre_tema = "oscuro"

    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    stylesheet = cargar_qss(f"tema_{nombre_tema}.qss")
    if not stylesheet:
        raise RuntimeError(f"No se pudo cargar el stylesheet del tema '{nombre_tema}'")
    app.setStyleSheet(stylesheet)


def aplicar_tema_oscuro(app: QApplication) -> None:
    aplicar_tema(app, "oscuro")


def aplicar_tema_claro(app: QApplication) -> None:
    aplicar_tema(app, "claro")


def alternar_tema(app: QApplication, ventana) -> None:
    if obtener_tema_actual() == "oscuro":
        aplicar_tema_claro(app)
        establecer_tema_actual("claro")
        ventana.btn_tema.setText("🌙 Modo oscuro")
    else:
        aplicar_tema_oscuro(app)
        establecer_tema_actual("oscuro")
        ventana.btn_tema.setText("☀ Modo claro")

def iniciar_app() -> None:
    """
    Inicializa la aplicación con error handling robusto.

    Esta función maneja errores de manera que la aplicación pueda continuar
    funcionando incluso si algunos componentes no críticos fallan.
    Solo falla completamente si componentes críticos (como Qt) no pueden inicializarse.
    """
    # Configurar logging
    logger = configurar_logging()
    logger.info("🚀 Iniciando VESP Control de Objetivos")

    # Estado de inicialización
    componentes_exitosos = []
    componentes_fallidos = []

    # =============================================================================
    # INICIALIZACIÓN DE COMPONENTES (ordenada por importancia)
    # =============================================================================

    # 1. Base de datos (CRÍTICA - sin BD no hay app)
    if inicializar_componente(logger, "Base de datos", crear_base_datos):
        componentes_exitosos.append("Base de datos")
    else:
        componentes_fallidos.append("Base de datos")
        logger.critical("❌ No se pudo inicializar la base de datos. La aplicación no puede continuar.")
        mostrar_error_critico(
            "Error Crítico",
            "No se pudo inicializar la base de datos.",
            "Verifique que tenga permisos de escritura en el directorio de la aplicación."
        )
        sys.exit(1)

    # 2. Migraciones (IMPORTANTE - pero no crítica)
    if inicializar_componente(logger, "Migraciones", lambda: (migrar_supervisor3(), migrar_supervisores_alta_baja(), migrar_usuarios_activo(), migrar_feriados())):
        componentes_exitosos.append("Migraciones")
    else:
        componentes_fallidos.append("Migraciones")
        logger.warning("⚠️  Las migraciones fallaron, pero la aplicación puede continuar")

    # 3. Backup (NO CRÍTICA - puede fallar)
    if inicializar_componente(logger, "Sistema de backup", hacer_backup):
        componentes_exitosos.append("Backup")
    else:
        componentes_fallidos.append("Backup")
        logger.warning("⚠️  El sistema de backup falló, pero la aplicación puede continuar")

    # 4. API REST (OPCIONAL - puede fallar)
    if inicializar_componente(logger, "API REST", iniciar_api_rest):
        componentes_exitosos.append("API REST")
    else:
        componentes_fallidos.append("API REST")
        logger.warning("⚠️  La API REST falló, pero la aplicación puede continuar en modo local")

    # =============================================================================
    # INICIALIZACIÓN DE INTERFAZ GRÁFICA (CRÍTICA)
    # =============================================================================

    try:
        logger.info("Inicializando interfaz gráfica...")
        app = QApplication(sys.argv)
        logger.info("✅ QApplication inicializada")

        # Aplicar tema inicial
        try:
            if obtener_tema_actual() == "claro":
                aplicar_tema_claro(app)
            else:
                aplicar_tema_oscuro(app)
        except Exception as e:
            logger.warning(f"Error aplicando tema inicial: {e}, usando tema oscuro por defecto")
            aplicar_tema_oscuro(app)

        logger.info("✅ Tema aplicado")

    except Exception as e:
        error_msg = f"Error crítico inicializando Qt: {str(e)}"
        logger.critical(error_msg)
        logger.critical(f"Traceback: {traceback.format_exc()}")
        mostrar_error_critico(
            "Error Crítico",
            "No se pudo inicializar la interfaz gráfica.",
            f"Detalle del error:\n{str(e)}\n\nVerifique que PyQt6 esté instalado correctamente."
        )
        sys.exit(1)

    # =============================================================================
    # INICIALIZACIÓN DE VENTANAS
    # =============================================================================

    ventana_principal = None

    def on_login_exitoso(usuario_id: int, rol: str) -> None:
        """Callback al login exitoso con error handling."""
        try:
            logger.info(f"Login exitoso para usuario ID {usuario_id} con rol {rol}")

            from services.sesion import iniciar_sesion
            iniciar_sesion(usuario_id, rol)

            nonlocal ventana_principal
            ventana_principal = VentanaPrincipal(usuario_id, rol, on_login_exitoso, app, alternar_tema)
            ventana_principal.show()

            # Verificar actualizaciones después de un delay
            QTimer.singleShot(1000, lambda: verificar_actualizacion(ventana_principal))

            logger.info("✅ Ventana principal abierta correctamente")

        except Exception as e:
            error_msg = f"Error al abrir ventana principal: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")

            mostrar_error_critico(
                "Error al Iniciar Sesión",
                "Ocurrió un error al abrir la ventana principal.",
                f"Detalle del error:\n{str(e)}"
            )

    # Mostrar resumen de inicialización
    logger.info("=== RESUMEN DE INICIALIZACIÓN ===")
    logger.info(f"Componentes exitosos: {', '.join(componentes_exitosos)}")
    if componentes_fallidos:
        logger.warning(f"Componentes fallidos: {', '.join(componentes_fallidos)}")

    # Mostrar ventana de login
    try:
        logger.info("Mostrando ventana de login...")
        login = LoginWindow(on_login_exitoso)
        login.show()
        logger.info("✅ Ventana de login mostrada")

    except Exception as e:
        error_msg = f"Error crítico mostrando login: {str(e)}"
        logger.critical(error_msg)
        logger.critical(f"Traceback: {traceback.format_exc()}")
        mostrar_error_critico(
            "Error Crítico",
            "No se pudo mostrar la ventana de login.",
            f"Detalle del error:\n{str(e)}"
        )
        sys.exit(1)

    # =============================================================================
    # EJECUCIÓN PRINCIPAL
    # =============================================================================

    try:
        logger.info("🚀 Iniciando loop principal de Qt")
        exit_code = app.exec()
        logger.info(f"✅ Aplicación finalizada con código {exit_code}")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("🛑 Aplicación interrumpida por usuario")
        sys.exit(0)

    except Exception as e:
        error_msg = f"Error crítico en loop principal: {str(e)}"
        logger.critical(error_msg)
        logger.critical(f"Traceback: {traceback.format_exc()}")
        mostrar_error_critico(
            "Error Crítico",
            "Ocurrió un error inesperado en la aplicación.",
            f"Detalle del error:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    iniciar_app()