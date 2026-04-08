# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de notificaciones en desktop
# =============================================================================

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from typing import Callable, Optional


class NotificadorDesktop(QObject):
    """Sistema de notificaciones desktop del sistema."""
    
    notificacion_nueva = pyqtSignal(str, str)  # titulo, mensaje
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.tray_icon = None
        self._inicializar_tray()
    
    def _inicializar_tray(self) -> None:
        """Inicializa el ícono en la bandeja del sistema."""
        try:
            from services.assets import ruta_asset
            icon_path = ruta_asset("assets/vesp.png")
            icon = QIcon(icon_path)
        except Exception:
            icon = QIcon()
        
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(icon)
        
        menu = QMenu()
        menu.addAction("Mostrar")
        menu.addSeparator()
        menu.addAction("Salir")
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def mostrar_notificacion(self, titulo: str, mensaje: str, duracion_ms: int = 5000) -> None:
        """
        Muestra una notificación en desktop.
        
        Args:
            titulo: Título de la notificación
            mensaje: Contenido del mensaje
            duracion_ms: Duración en milisegundos (default 5000)
        """
        if self.tray_icon:
            self.tray_icon.showMessage(titulo, mensaje, QSystemTrayIcon.MessageIcon.Information, duracion_ms)
        
        self.notificacion_nueva.emit(titulo, mensaje)
    
    def notificar_pasada_registrada(self, objetivo: str, supervisor: str, turno: str) -> None:
        """Notifica cuando se registra una pasada."""
        titulo = "Pasada registrada"
        mensaje = f"{objetivo}\n{supervisor} - {turno}"
        self.mostrar_notificacion(titulo, mensaje)
    
    def notificar_error(self, titulo: str, mensaje: str) -> None:
        """Notifica un error."""
        if self.tray_icon:
            self.tray_icon.showMessage(titulo, mensaje, QSystemTrayIcon.MessageIcon.Critical, 7000)
    
    def notificar_advertencia(self, titulo: str, mensaje: str) -> None:
        """Notifica una advertencia."""
        if self.tray_icon:
            self.tray_icon.showMessage(titulo, mensaje, QSystemTrayIcon.MessageIcon.Warning, 5000)
    
    def notificar_sesion_por_expirar(self, minutos_restantes: int) -> None:
        """Notifica cuando la sesión está próxima a expirar."""
        titulo = "Sesión por expirar"
        mensaje = f"Tu sesión expirará en {minutos_restantes} minutos"
        self.notificar_advertencia(titulo, mensaje)
    
    def limpiar(self) -> None:
        """Limpia el ícono de la bandeja."""
        if self.tray_icon:
            self.tray_icon.hide()


class MonitorNotificaciones(QObject):
    """Monitorea eventos del sistema y genera notificaciones."""
    
    def __init__(self, notificador: NotificadorDesktop):
        super().__init__()
        self.notificador = notificador
        self.timer = QTimer()
        self.timer.timeout.connect(self._chequear_eventos)
    
    def iniciar(self, intervalo_ms: int = 60000) -> None:
        """Inicia el monitoreo de eventos."""
        self.timer.start(intervalo_ms)
    
    def detener(self) -> None:
        """Detiene el monitoreo."""
        self.timer.stop()
    
    def _chequear_eventos(self) -> None:
        """Chequea eventos para generar notificaciones."""
        # Aquí iría lógica para verificar:
        # - Si hay cambios en datos
        # - Si expira la sesión pronto
        # - Si hay errores pendientes
        pass
    
    def on_pasada_registrada(self, objetivo: str, supervisor: str, turno: str) -> None:
        """Callback cuando se registra una pasada."""
        self.notificador.notificar_pasada_registrada(objetivo, supervisor, turno)
    
    def on_objetivo_agregado(self, nombre_objetivo: str) -> None:
        """Callback cuando se agrega un objetivo."""
        titulo = "Objetivo agregado"
        self.notificador.mostrar_notificacion(titulo, f"'{nombre_objetivo}' fue agregado")
    
    def on_supervisor_agregado(self, nombre_supervisor: str) -> None:
        """Callback cuando se agrega un supervisor."""
        titulo = "Supervisor agregado"
        self.notificador.mostrar_notificacion(titulo, f"'{nombre_supervisor}' fue agregado")
    
    def on_error_sincronizacion(self) -> None:
        """Callback cuando falla sincronización."""
        self.notificador.notificar_error(
            "Error de sincronización",
            "No se pudo sincronizar con el servidor. Verifica tu conexión."
        )
    
    def on_backup_completado(self) -> None:
        """Callback cuando se completa backup automático."""
        titulo = "Backup completado"
        self.notificador.mostrar_notificacion(titulo, "Respaldo automático realizado")
