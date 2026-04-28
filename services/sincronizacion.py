# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de Sincronización de Datos - VERSIÓN PROFESIONAL
# =============================================================================
"""
Sistema central de sincronización de datos entre módulos.

Proporciona:
- Señales de cambio para mantener consistencia entre módulos
- Invalidación inteligente de caché basada en dependencias
- Notificaciones SSE a API REST para multi-usuario (futuro)
- Actualización en cascada de tablas relacionadas
- Programación de tareas periódicas con thread-safety

Características:
- Type hints completos en todas las funciones
- Logging detallado para auditoría
- Thread-safe con locks para operaciones críticas
- Manejo de módulos sin métodos requeridos (duck typing)
- Invalidación de caché por patrones
- Dependencias entre tablas (grafo de actualización)

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional, Tuple, Any

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

try:
    import requests
except ImportError:
    requests = None

from .exceptions import SincronizacionError, ConflictoSincronizacion

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

# Mapeo de tablas a patrones de caché a invalidar
INVALIDACIONES_CACHE: Dict[str, List[str]] = {
    'objetivos': ['objetivo', 'reporte'],
    'supervisores': ['supervisor', 'equipo'],
    'usuarios': ['usuario', 'sesion'],
    'pasadas': ['pasada', 'cobertura'],
    'equipos': ['equipo', 'cobertura'],
    'auditoria': ['auditoria']
}

# Dependencias entre tablas (si X cambia, actualizar Y, Z...)
DEPENDENCIAS_TABLAS: Dict[str, List[str]] = {
    'objetivos': ['pasadas', 'control_diario', 'reportes'],
    'supervisores': ['pasadas', 'equipos', 'control_diario'],
    'equipos': ['control_diario', 'reportes'],
    'pasadas': ['control_diario', 'reportes', 'estadisticas'],
    'usuarios': []  # Los cambios de usuario no requieren actualizar tablas
}

# Operaciones de sincronización válidas
OPERACIONES_VALIDAS = {'INSERT', 'UPDATE', 'DELETE'}

# URL de la API para SSE (local development)
API_SSE_URL = "http://127.0.0.1:5000/api/sse/publish"
API_SSE_TIMEOUT = 1  # segundos


# =============================================================================
# SINCRONIZADOR CENTRAL
# =============================================================================

class SincronizadorDatos(QObject):
    """Sistema central de sincronización de datos entre módulos.
    
    Responsabilidades:
    - Emitir señales cuando datos cambian
    - Invalidar caché automáticamente
    - Actualizar tablas dependientes en cascada
    - Enviar notificaciones SSE a API para multi-usuario
    - Programar tareas periódicas
    
    Señales:
    - datos_cambiados: (tabla, operacion, datos)
    - cache_invalidado: (patron)
    - tabla_actualizar: (nombre_tabla)
    - notificacion_usuario: (titulo, mensaje)
    - progreso_operacion: (operacion, porcentaje)
    
    Example:
        >>> sync = SincronizadorDatos()
        >>> sync.conectar_modulo(mi_widget, 'principal')
        >>> sync.notificar_cambio('objetivos', 'INSERT', {'id': 1, 'nombre': 'Obj1'})
    """

    # Señales PyQt6
    datos_cambiados = pyqtSignal(str, str, dict)  # tabla, operacion, datos
    cache_invalidado = pyqtSignal(str)  # patron_invalido
    tabla_actualizar = pyqtSignal(str)  # nombre_tabla
    notificacion_usuario = pyqtSignal(str, str)  # titulo, mensaje
    progreso_operacion = pyqtSignal(str, int)  # operacion, porcentaje

    def __init__(self):
        """Inicializa el sincronizador con diccionarios vacíos y lock."""
        super().__init__()
        self._timers: Dict[str, QTimer] = {}
        self._lock = threading.Lock()
        self._modulos_conectados: Dict[str, QObject] = {}
        logger.info("SincronizadorDatos inicializado")

    def conectar_modulo(self, modulo: QObject, nombre: str) -> None:
        """Conecta un módulo al sistema de sincronización.
        
        Args:
            modulo: Instancia del módulo (QWidget, diálogo, etc.)
            nombre: Nombre identificador único del módulo.
            
        Note:
            Usa duck typing: si el módulo no tiene los métodos,
            los conecta a lambdas vacías para evitar errores.
        """
        try:
            # Conectar señales a métodos disponibles (duck typing)
            if hasattr(modulo, 'actualizar_datos') and callable(getattr(modulo, 'actualizar_datos')):
                self.datos_cambiados.connect(modulo.actualizar_datos)
            
            if hasattr(modulo, 'invalidar_cache') and callable(getattr(modulo, 'invalidar_cache')):
                self.cache_invalidado.connect(modulo.invalidar_cache)
            
            if hasattr(modulo, 'actualizar_tabla') and callable(getattr(modulo, 'actualizar_tabla')):
                self.tabla_actualizar.connect(modulo.actualizar_tabla)
            
            if hasattr(modulo, 'mostrar_notificacion') and callable(getattr(modulo, 'mostrar_notificacion')):
                self.notificacion_usuario.connect(modulo.mostrar_notificacion)
            
            self._modulos_conectados[nombre] = modulo
            logger.info(f"Módulo '{nombre}' conectado al sincronizador")
            
        except Exception as e:
            logger.error(f"Error conectando módulo '{nombre}': {e}")
            raise SincronizacionError(f"Error conectando módulo: {str(e)}")

    def notificar_cambio(
        self,
        tabla: str,
        operacion: str,
        datos: Optional[Dict[str, Any]] = None
    ) -> None:
        """Notifica que se realizó un cambio en una tabla.
        
        Proceso:
        1. Valida operación
        2. Agrega timestamp y metadatos
        3. Emite señal datos_cambiados
        4. Envía SSE a API (background)
        5. Invalida caché según tabla
        6. Actualiza tablas dependientes en cascada
        
        Args:
            tabla: Nombre de tabla modificada (objetivos, supervisores, etc).
            operacion: Tipo de cambio ('INSERT', 'UPDATE', 'DELETE').
            datos: Diccionario con información del cambio (opcional).
        
        Raises:
            SincronizacionError: Si operación no es válida.
            
        Example:
            >>> sync.notificar_cambio('objetivos', 'INSERT', 
            ...                       {'id': 1, 'nombre': 'Obj1'})
        """
        try:
            # Validar operación
            operacion_upper = operacion.upper()
            if operacion_upper not in OPERACIONES_VALIDAS:
                raise SincronizacionError(f"Operación inválida: {operacion}")
            
            # Preparar datos
            datos = datos or {}
            datos['timestamp'] = datetime.now().isoformat()
            datos['operacion'] = operacion_upper
            datos['tabla'] = tabla
            
            logger.info(f"Cambio notificado: {operacion_upper} en {tabla}")
            
            # Emitir señal principal
            self.datos_cambiados.emit(tabla, operacion_upper, datos)
            
            # Enviar SSE a API (no bloqueante)
            if requests:
                self._enviar_sse_async(tabla, operacion_upper, datos)
            
            # Invalidar caché según tabla
            self._invalidar_cache_por_tabla(tabla)
            
            # Actualizar tablas relacionadas en cascada
            self._actualizar_tablas_relacionadas(tabla)
            
        except SincronizacionError:
            raise
        except Exception as e:
            logger.error(f"Error notificando cambio en {tabla}: {e}")
            raise SincronizacionError(f"Error notificando cambio: {str(e)}")

    def _enviar_sse_async(self, tabla: str, operacion: str, datos: Dict[str, Any]) -> None:
        """Envía notificación SSE a la API en un hilo separado (no bloqueante).
        
        Args:
            tabla: Nombre de tabla.
            operacion: Operación realizada.
            datos: Datos del cambio.
        """
        def _post():
            try:
                payload = {
                    'tabla': tabla,
                    'operacion': operacion,
                    'datos': datos
                }
                requests.post(API_SSE_URL, json=payload, timeout=API_SSE_TIMEOUT)
                logger.debug(f"SSE enviado para {tabla}/{operacion}")
            except requests.exceptions.Timeout:
                logger.debug("SSE timeout (API no disponible)")
            except Exception as e:
                logger.debug(f"SSE error: {e}")
        
        thread = threading.Thread(target=_post, daemon=True)
        thread.start()

    def _invalidar_cache_por_tabla(self, tabla: str) -> None:
        """Invalida caché según la tabla modificada.
        
        Emite señales cache_invalidado para cada patrón asociado a la tabla.
        
        Args:
            tabla: Nombre de tabla modificada.
        """
        patrones = INVALIDACIONES_CACHE.get(tabla, [])
        for patron in patrones:
            logger.debug(f"Invalidando caché: {patron}")
            self.cache_invalidado.emit(patron)

    def _actualizar_tablas_relacionadas(self, tabla: str) -> None:
        """Actualiza tablas que dependen de la tabla modificada (cascada).
        
        Emite señales tabla_actualizar para cada tabla dependiente.
        
        Args:
            tabla: Tabla que fue modificada.
        """
        tablas_dependientes = DEPENDENCIAS_TABLAS.get(tabla, [])
        for tabla_dep in tablas_dependientes:
            logger.debug(f"Programando actualización en cascada: {tabla_dep}")
            self.tabla_actualizar.emit(tabla_dep)

    def programar_actualizacion(
        self,
        nombre: str,
        intervalo_ms: int,
        callback: Callable
    ) -> None:
        """Programa una actualización periódica con QTimer.
        
        Args:
            nombre: Identificador único del timer.
            intervalo_ms: Intervalo en milisegundos.
            callback: Función a ejecutar (sin argumentos).
        
        Note:
            Thread-safe. Si ya existe un timer con ese nombre, lo detiene primero.
            
        Example:
            >>> sync.programar_actualizacion(
            ...     'refresco_tablas',
            ...     5000,  # cada 5 segundos
            ...     lambda: print('Actualizando...')
            ... )
        """
        try:
            with self._lock:
                # Detener timer anterior si existe
                if nombre in self._timers:
                    self._timers[nombre].stop()
                    logger.debug(f"Timer anterior '{nombre}' detenido")
                
                # Crear nuevo timer
                timer = QTimer()
                timer.timeout.connect(callback)
                timer.start(intervalo_ms)
                self._timers[nombre] = timer
                
                logger.info(f"Timer '{nombre}' programado cada {intervalo_ms}ms")
        except Exception as e:
            logger.error(f"Error programando actualización '{nombre}': {e}")
            raise SincronizacionError(f"Error programando actualización: {str(e)}")

    def cancelar_actualizacion(self, nombre: str) -> bool:
        """Cancela una actualización programada.
        
        Args:
            nombre: Identificador del timer.
        
        Returns:
            True si se canceló, False si no existía.
        """
        try:
            with self._lock:
                if nombre in self._timers:
                    self._timers[nombre].stop()
                    del self._timers[nombre]
                    logger.info(f"Timer '{nombre}' cancelado")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error cancelando actualización '{nombre}': {e}")
            return False

    def notificar_progreso(self, operacion: str, porcentaje: int) -> None:
        """Notifica progreso de una operación larga.
        
        Args:
            operacion: Nombre descriptivo de la operación.
            porcentaje: Progreso de 0 a 100.
            
        Example:
            >>> for i in range(101):
            ...     sync.notificar_progreso('Importando datos', i)
        """
        if not (0 <= porcentaje <= 100):
            logger.warning(f"Porcentaje fuera de rango: {porcentaje}")
            return
        
        logger.debug(f"Progreso {operacion}: {porcentaje}%")
        self.progreso_operacion.emit(operacion, porcentaje)

    def enviar_notificacion(self, titulo: str, mensaje: str) -> None:
        """Envía una notificación al usuario mediante señal.
        
        Args:
            titulo: Título o categoría de notificación.
            mensaje: Mensaje a mostrar.
            
        Example:
            >>> sync.enviar_notificacion(
            ...     'Éxito',
            ...     'Datos importados correctamente'
            ... )
        """
        logger.info(f"Notificación: {titulo} - {mensaje}")
        self.notificacion_usuario.emit(titulo, mensaje)

    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sincronizador.
        
        Returns:
            Diccionario con información de módulos y timers activos.
        """
        with self._lock:
            return {
                'modulos_conectados': list(self._modulos_conectados.keys()),
                'total_modulos': len(self._modulos_conectados),
                'timers_activos': list(self._timers.keys()),
                'total_timers': len(self._timers)
            }


# =============================================================================
# INSTANCIA GLOBAL
# =============================================================================

_sincronizador_global = SincronizadorDatos()


def obtener_sincronizador() -> SincronizadorDatos:
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
