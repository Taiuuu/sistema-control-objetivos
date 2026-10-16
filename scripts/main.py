# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Archivo principal de entrada de la aplicación
# =============================================================================

import sys
import os
import logging
import traceback
import threading
from typing import Optional

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from ui.login import LoginWindow
from ui.ventana_principal import VentanaPrincipal
from database.db import (
    DB_PATH,
    crear_base_datos,
    migrar_supervisor3,
    migrar_supervisores_alta_baja,
    migrar_usuarios_activo,
    migrar_feriados,
    verificar_integridad,
)
from services.backup import (
    hacer_backup,
    listar_backups,
    restaurar_backup,
    crear_backup,
)
from core.configuracion import asegurar_directorios
from core.logging_config import configurar_logging as configurar_logging_archivo
from core.instancia import adquirir_bloqueo_instancia
from services.actualizador import verificar_actualizacion
from services.api_rest import iniciar_api_rest
from ui.theme.theme_manager import get_theme_manager

_DESPACHADOR_EXCEPCIONES = None


class _DespachadorExcepciones(QObject):
    """Entrega diálogos de error desde hilos al hilo dueño de Qt."""

    mostrar = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mostrar.connect(self._mostrar_dialogo)

    def _mostrar_dialogo(self, mensaje: str) -> None:
        QMessageBox.critical(None, "Error inesperado", mensaje)


# =============================================================================
# UTILIDADES DE ERROR HANDLING
# =============================================================================

def configurar_logging() -> logging.Logger:
    """Configura consola y archivo rotativo persistente."""
    configurar_logging_archivo()
    logger = logging.getLogger('vesp_main')
    logger.setLevel(logging.INFO)

    # Handler para consola
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def instalar_manejadores_excepciones(logger: logging.Logger) -> None:
    """Registra excepciones no capturadas y notifica al usuario."""
    global _DESPACHADOR_EXCEPCIONES
    _DESPACHADOR_EXCEPCIONES = _DespachadorExcepciones()
    mensaje = (
        "Ocurrió un error inesperado, tus datos están a salvo. "
        "Detalle guardado en el log."
    )

    def manejar(tipo, valor, traza):
        logger.critical("Excepción no capturada", exc_info=(tipo, valor, traza))
        mostrar_error_critico("Error inesperado", mensaje)

    def manejar_hilo(args):
        logger.critical(
            "Excepción no capturada en hilo %s",
            args.thread.name if args.thread else "desconocido",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        _DESPACHADOR_EXCEPCIONES.mostrar.emit(mensaje)

    sys.excepthook = manejar
    threading.excepthook = manejar_hilo


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


def iniciar_app() -> None:
    """
    Inicializa la aplicación con error handling robusto.

    Esta función maneja errores de manera que la aplicación pueda continuar
    funcionando incluso si algunos componentes no críticos fallan.
    Solo falla completamente si componentes críticos (como Qt) no pueden inicializarse.
    """
    # Configurar logging
    asegurar_directorios()
    logger = configurar_logging()
    logger.info("🚀 Iniciando VESP Organizations")

    try:
        app = QApplication(sys.argv)
    except Exception as error:
        logger.critical("No se pudo inicializar Qt", exc_info=True)
        mostrar_error_critico("Error Crítico", "No se pudo inicializar la interfaz gráfica.", str(error))
        sys.exit(1)
    instalar_manejadores_excepciones(logger)

    bloqueo = adquirir_bloqueo_instancia(DB_PATH)
    if bloqueo is None:
        QMessageBox.warning(
            None,
            "VESP ya está abierto",
            "Ya hay una instancia usando esta base de datos. Cerrala antes de abrir otra.",
        )
        return
    app.aboutToQuit.connect(lambda: logger.info("Cierre de VESP"))

    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        try:
            integra, errores = verificar_integridad()
        except Exception as error:
            integra, errores = False, [str(error)]
        logger.info(
            "Resultado integrity_check/foreign_key_check: %s",
            "correcto" if integra else "; ".join(errores),
        )
        if not integra:
            respuesta = QMessageBox.question(
                None,
                "Base de datos dañada",
                "Se detectaron problemas en la base:\n"
                + "\n".join(errores)
                + "\n\n¿Querés restaurar el último backup verificado?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            copias = [copia for copia in listar_backups() if copia["verificado"]]
            if respuesta != QMessageBox.StandardButton.Yes:
                bloqueo.unlock()
                sys.exit(1)
            if not copias:
                QMessageBox.critical(
                    None,
                    "Sin copias verificadas",
                    "No existe un backup verificado para restaurar. "
                    "La aplicación no va a abrir la base dañada.",
                )
                bloqueo.unlock()
                sys.exit(1)
            try:
                restaurar_backup(
                    max(copias, key=lambda copia: copia["fecha"])["path"]
                )
                integra, errores = verificar_integridad()
            except Exception as error:
                logger.exception("Falló la recuperación de la base dañada")
                QMessageBox.critical(
                    None,
                    "No se pudo restaurar",
                    f"No se pudo restaurar la copia verificada:\n{error}",
                )
                bloqueo.unlock()
                sys.exit(1)
            if not integra:
                QMessageBox.critical(
                    None,
                    "Restauración inválida",
                    "La base restaurada sigue dañada:\n" + "\n".join(errores),
                )
                bloqueo.unlock()
                sys.exit(1)

    # Estado de inicialización
    componentes_exitosos = []
    componentes_fallidos = []

    # =============================================================================
    # INICIALIZACIÓN DE COMPONENTES (ordenada por importancia)
    # =============================================================================

    # Los backfills/migraciones de arranque pueden tocar muchas filas. Como no
    # existe un motivo de migración en el formato de nombres permitido, se
    # registra como copia manual antes de cualquier cambio de esquema/datos.
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        import sqlite3
        conexion_version = sqlite3.connect(DB_PATH)
        try:
            cantidad_tablas = conexion_version.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchone()[0]
        finally:
            conexion_version.close()
        if cantidad_tablas:
            try:
                crear_backup("manual")
            except Exception as error:
                logger.exception("Migración detenida: no se pudo crear backup previo")
                QMessageBox.critical(
                    None,
                    "Migración detenida",
                    f"No se pudo crear una copia verificada antes de migrar:\n{error}",
                )
                bloqueo.unlock()
                sys.exit(1)

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
        bloqueo.unlock()
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

    # Aplicar el tema global guardado antes de crear ventanas y diálogos.
    try:
        get_theme_manager().apply_current()
    except Exception as e:
        logger.warning(f"Error aplicando tema inicial: {e}, usando Grafito")
        get_theme_manager().set_theme("Grafito")

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
            ventana_principal = VentanaPrincipal(usuario_id, rol, on_login_exitoso, app)
            ventana_principal.show()
            from ui.animaciones import animar_aparecer
            animar_aparecer(ventana_principal, 180)

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
        bloqueo.unlock()
        sys.exit(1)

    # =============================================================================
    # EJECUCIÓN PRINCIPAL
    # =============================================================================

    try:
        logger.info("🚀 Iniciando loop principal de Qt")
        exit_code = app.exec()
        logger.info(f"✅ Aplicación finalizada con código {exit_code}")
        bloqueo.unlock()
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("🛑 Aplicación interrumpida por usuario")
        bloqueo.unlock()
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
        bloqueo.unlock()
        sys.exit(1)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    iniciar_app()