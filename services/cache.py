# =============================================================================
# VESP Organizations - Servicio de caché
# =============================================================================
"""
Caché simple en memoria con expiración por TTL (Time To Live).

Provee:
- cache_global: instancia global de CacheManager
- invalidar_objetivos / invalidar_supervisores / invalidar_pasadas: helpers
  para limpiar entradas relacionadas cuando cambian los datos subyacentes.
- obtener_supervisores_cache: acceso cacheado a la lista de supervisores.
"""

import time
import logging
import threading
from functools import wraps
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Cache en memoria, thread-safe, con expiración por TTL."""

    def __init__(self):
        self._store: dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any:
        """Devuelve el valor cacheado o None si no existe / expiró."""
        with self._lock:
            entrada = self._store.get(key)
            if entrada is None:
                return None
            valor, expira = entrada
            if expira is not None and time.time() > expira:
                del self._store[key]
                return None
            return valor

    def set(self, key: str, valor: Any, ttl: Optional[int] = 300) -> Any:
        """Guarda un valor en caché con un TTL en segundos (None = sin expiración)."""
        with self._lock:
            expira = (time.time() + ttl) if ttl else None
            self._store[key] = (valor, expira)
        return valor

    def invalidar_patron(self, patron: str) -> None:
        """Elimina todas las claves que contengan el patrón indicado."""
        with self._lock:
            claves = [k for k in self._store if patron in k]
            for k in claves:
                del self._store[k]
        logger.debug("Cache invalidada por patrón '%s' (%d claves eliminadas)", patron, len(claves))

    def invalidar_todo(self) -> None:
        """Vacía toda la caché."""
        with self._lock:
            self._store.clear()

    def auto_cache(self, ttl: int = 300):
        """Decorador que cachea el resultado de una función según sus argumentos."""
        def decorador(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                clave = f"{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"
                valor = self.get(clave)
                if valor is not None:
                    return valor
                resultado = func(*args, **kwargs)
                self.set(clave, resultado, ttl)
                return resultado

            wrapper.cache_clear = lambda: self.invalidar_patron(
                f"{func.__module__}.{func.__qualname__}"
            )
            return wrapper
        return decorador


# Instancia global compartida por todo el sistema
cache_global = CacheManager()


def invalidar_objetivos() -> None:
    """Invalida toda la caché relacionada con objetivos."""
    cache_global.invalidar_patron("objetivos")


def invalidar_supervisores() -> None:
    """Invalida toda la caché relacionada con supervisores."""
    cache_global.invalidar_patron("supervisores")


def invalidar_pasadas() -> None:
    """Invalida toda la caché relacionada con pasadas/turnos."""
    cache_global.invalidar_patron("pasadas")


def obtener_supervisores_cache():
    """Devuelve la lista de supervisores, cacheada por 60 segundos.

    NOTA: ajustar el import/función real de tu módulo de supervisores
    si el nombre no coincide (ver models/supervisores.py).
    """
    clave = "supervisores:lista_cache"
    valor = cache_global.get(clave)
    if valor is not None:
        return valor

    from models.supervisores import listar_supervisores

    resultado = listar_supervisores()
    cache_global.set(clave, resultado, 60)
    return resultado