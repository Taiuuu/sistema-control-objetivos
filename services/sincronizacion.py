# =============================================================================
# VESP Organizations - Sistema de Sincronización de Datos
# =============================================================================

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Callable, Any
from datetime import datetime
import threading


class Sincronizador(QObject):
    """
    Sistema central de sincronización de datos entre módulos.
    Maneja señales para mantener consistencia entre formularios, tablas y caché.
    """

    # Señales principales
    datos_cambiados = pyqtSignal(str, str, dict)  # tabla, operacion, datos
    cache_invalidado = pyqtSignal(str)  # patron_invalido
    tabla_actualizar = pyqtSignal(str)  # nombre_tabla
    notificacion_usuario = pyqtSignal(str, str)  # titulo, mensaje
    progreso_operacion = pyqtSignal(str, int)  # operacion, porcentaje

    def __init__(self):
        super().__init__()
        self._listeners: Dict[str, List[Callable]] = {}
        self._timers: Dict[str, QTimer] = {}
        self._lock = threading.Lock()

    def conectar_modulo(self, modulo: QObject, nombre: str) -> None:
        """
        Conecta un módulo al sistema de sincronización.
        Args:
            modulo: Instancia del módulo (QWidget, etc.)
            nombre: Nombre identificador del módulo
        """
        # Conectar señales principales
        self.datos_cambiados.connect(modulo.actualizar_datos if hasattr(modulo, 'actualizar_datos') else lambda *args: None)
        self.cache_invalidado.connect(modulo.invalidar_cache if hasattr(modulo, 'invalidar_cache') else lambda *args: None)
        self.tabla_actualizar.connect(modulo.actualizar_tabla if hasattr(modulo, 'actualizar_tabla') else lambda *args: None)
        self.notificacion_usuario.connect(modulo.mostrar_notificacion if hasattr(modulo, 'mostrar_notificacion') else lambda *args: None)

        print(f"✅ Módulo '{nombre}' conectado al sincronizador")

    def notificar_cambio(self, tabla: str, operacion: str, datos: dict = None) -> None:
        """
        Notifica que se realizó un cambio en una tabla.
        Args:
            tabla: Nombre de la tabla modificada
            operacion: 'INSERT', 'UPDATE', 'DELETE'
            datos: Información adicional del cambio
        """
        datos = datos or {}
        datos['timestamp'] = datetime.now().isoformat()
        datos['operacion'] = operacion

        print(f"📢 Cambio notificado: {operacion} en {tabla}")
        self.datos_cambiados.emit(tabla, operacion, datos)

        # Invalidar caché automáticamente según tabla
        self._invalidar_cache_por_tabla(tabla)

        # Actualizar tablas relacionadas
        self._actualizar_tablas_relacionadas(tabla)

    def _invalidar_cache_por_tabla(self, tabla: str) -> None:
        """Invalida el caché según la tabla modificada."""
        invalidaciones = {
            'objetivos': ['objetivo'],
            'supervisores': ['supervisor'],
            'usuarios': ['usuario'],
            'pasadas': ['pasada'],
            'equipos': ['equipo'],
            'auditoria': ['auditoria']
        }

        patrones = invalidaciones.get(tabla, [])
        for patron in patrones:
            self.cache_invalidado.emit(patron)

    def _actualizar_tablas_relacionadas(self, tabla: str) -> None:
        """Actualiza tablas que dependen de la tabla modificada."""
        dependencias = {
            'objetivos': ['pasadas', 'control_diario'],
            'supervisores': ['pasadas', 'equipos', 'control_diario'],
            'equipos': ['control_diario'],
            'pasadas': ['control_diario', 'reportes']
        }

        tablas_a_actualizar = dependencias.get(tabla, [])
        for tabla_dep in tablas_a_actualizar:
            self.tabla_actualizar.emit(tabla_dep)

    def programar_actualizacion(self, nombre: str, intervalo_ms: int, callback: Callable) -> None:
        """
        Programa una actualización periódica.
        Args:
            nombre: Nombre identificador del timer
            intervalo_ms: Intervalo en milisegundos
            callback: Función a ejecutar
        """
        with self._lock:
            if nombre in self._timers:
                self._timers[nombre].stop()

            timer = QTimer()
            timer.timeout.connect(callback)
            timer.start(intervalo_ms)
            self._timers[nombre] = timer

    def cancelar_actualizacion(self, nombre: str) -> None:
        """Cancela una actualización programada."""
        with self._lock:
            if nombre in self._timers:
                self._timers[nombre].stop()
                del self._timers[nombre]

    def notificar_progreso(self, operacion: str, porcentaje: int) -> None:
        """Notifica progreso de una operación."""
        self.progreso_operacion.emit(operacion, porcentaje)

    def enviar_notificacion(self, titulo: str, mensaje: str) -> None:
        """Envía una notificación al usuario."""
        self.notificacion_usuario.emit(titulo, mensaje)


# =============================================================================
# INSTANCIA GLOBAL
# =============================================================================

_sincronizador_global = Sincronizador()


def obtener_sincronizador() -> Sincronizador:
    """Retorna la instancia global del sincronizador."""
    return _sincronizador_global


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def notificar_cambio(tabla: str, operacion: str, datos: dict = None) -> None:
    """Función de conveniencia para notificar cambios."""
    _sincronizador_global.notificar_cambio(tabla, operacion, datos)


def conectar_modulo(modulo: QObject, nombre: str) -> None:
    """Función de conveniencia para conectar módulos."""
    _sincronizador_global.conectar_modulo(modulo, nombre)


def programar_actualizacion(nombre: str, intervalo_ms: int, callback: Callable) -> None:
    """Función de conveniencia para programar actualizaciones."""
    _sincronizador_global.programar_actualizacion(nombre, intervalo_ms, callback)


def enviar_notificacion(titulo: str, mensaje: str) -> None:
    """Función de conveniencia para enviar notificaciones."""
    _sincronizador_global.enviar_notificacion(titulo, mensaje)


# =============================================================================
# DECORADORES PARA SINCRONIZACIÓN AUTOMÁTICA
# =============================================================================

def sincronizar_operacion_bd(tabla: str, operacion: str):
    """
    Decorador que notifica cambios automáticamente después de operaciones BD.
    Uso: @sincronizar_operacion_bd('objetivos', 'INSERT')
    """
    def decorador(func):
        def wrapper(*args, **kwargs):
            resultado = func(*args, **kwargs)
            # Extraer datos del resultado si es posible
            datos_extra = {}
            if resultado and isinstance(resultado, dict):
                datos_extra = resultado
            elif resultado and hasattr(resultado, '__dict__'):
                datos_extra = vars(resultado)

            notificar_cambio(tabla, operacion, datos_extra)
            return resultado
        return wrapper
    return decorador


def actualizar_cache_al_cambio(tabla: str):
    """
    Decorador que invalida caché automáticamente.
    Uso: @actualizar_cache_al_cambio('objetivos')
    """
    def decorador(func):
        def wrapper(*args, **kwargs):
            resultado = func(*args, **kwargs)
            _sincronizador_global._invalidar_cache_por_tabla(tabla)
            return resultado
        return wrapper
    return decorador
