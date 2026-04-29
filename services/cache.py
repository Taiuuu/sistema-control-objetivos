# =============================================================================
# VESP Organizations - Sistema de Caché Inteligente
# =============================================================================

import logging
import time
import threading
from typing import Any, Optional, List, Dict, Callable
from functools import wraps
from database.db import conectar

logger = logging.getLogger(__name__)


# =============================================================================
# MODELOS
# =============================================================================

class EntradaCache:
    """Representa una entrada en caché con TTL."""

    def __init__(self, valor: Any, ttl_segundos: int = 300):
        self.valor = valor
        self.ttl_segundos = ttl_segundos
        self.timestamp_creacion = time.time()
        self.hits = 0

    def esta_expirada(self) -> bool:
        return (time.time() - self.timestamp_creacion) > self.ttl_segundos

    def obtener(self) -> Any:
        self.hits += 1
        return self.valor

    def antiguedad_segundos(self) -> float:
        return time.time() - self.timestamp_creacion

    def info(self) -> dict:
        return {
            "ttl_segundos": self.ttl_segundos,
            "antiguedad_segundos": round(self.antiguedad_segundos(), 2),
            "hits": self.hits,
            "expirada": self.esta_expirada()
        }


# =============================================================================
# CACHE PRINCIPAL
# =============================================================================

class CacheInteligente:
    """Sistema de caché thread-safe con TTL."""

    def __init__(self, ttl_por_defecto: int = 300):
        self._cache: Dict[str, EntradaCache] = {}
        self._ttl_por_defecto = ttl_por_defecto
        self._lock = threading.Lock()

        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidaciones": 0
        }

    def set(self, clave: str, valor: Any, ttl_segundos: Optional[int] = None) -> None:
        ttl = ttl_segundos if ttl_segundos is not None else self._ttl_por_defecto

        with self._lock:
            self._cache[clave] = EntradaCache(valor, ttl)

    def get(self, clave: str, generador: Optional[Callable] = None) -> Optional[Any]:
        with self._lock:
            entrada = self._cache.get(clave)

            if entrada:
                if not entrada.esta_expirada():
                    self._stats["hits"] += 1
                    return entrada.obtener()

                del self._cache[clave]

        self._stats["misses"] += 1

        if generador:
            valor = generador()
            if valor is not None:
                self.set(clave, valor)
            return valor

        return None

    def existe(self, clave: str) -> bool:
        with self._lock:
            entrada = self._cache.get(clave)

            if not entrada:
                return False

            if entrada.esta_expirada():
                del self._cache[clave]
                return False

            return True

    def eliminar(self, clave: str) -> bool:
        with self._lock:
            if clave in self._cache:
                del self._cache[clave]
                self._stats["invalidaciones"] += 1
                return True
            return False

    def limpiar(self) -> None:
        with self._lock:
            cantidad = len(self._cache)
            self._cache.clear()
            self._stats["invalidaciones"] += cantidad

    def limpiar_expiradas(self) -> int:
        with self._lock:
            expiradas = [
                clave for clave, entrada in self._cache.items()
                if entrada.esta_expirada()
            ]

            for clave in expiradas:
                del self._cache[clave]

            self._stats["invalidaciones"] += len(expiradas)
            return len(expiradas)

    def invalidar_patron(self, patron: str) -> int:
        with self._lock:
            claves = [k for k in self._cache if patron in k]

            for clave in claves:
                del self._cache[clave]

            self._stats["invalidaciones"] += len(claves)
            return len(claves)

    def obtener_stats(self) -> dict:
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]

            tasa = round(
                (self._stats["hits"] / total) * 100, 2
            ) if total > 0 else 0

            return {
                "entradas": len(self._cache),
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "total_accesos": total,
                "tasa_acierto_porcentaje": tasa,
                "invalidaciones": self._stats["invalidaciones"],
                "ttl_por_defecto_segundos": self._ttl_por_defecto
            }

    def obtener_detalles(self) -> dict:
        with self._lock:
            return {
                clave: entrada.info()
                for clave, entrada in self._cache.items()
            }

    def establecer_ttl_por_defecto(self, ttl_segundos: int) -> None:
        self._ttl_por_defecto = ttl_segundos

    def auto_cache(self, ttl: Optional[int] = None):
        """Decorador automático."""

        def decorador(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                clave = f"{func.__name__}:{args}:{kwargs}"

                valor = self.get(clave)
                if valor is not None:
                    return valor

                resultado = func(*args, **kwargs)

                if resultado is not None:
                    self.set(
                        clave,
                        resultado,
                        ttl if ttl is not None else self._ttl_por_defecto
                    )

                return resultado

            return wrapper

        return decorador


# =============================================================================
# INSTANCIA GLOBAL
# =============================================================================

_cache_global = CacheInteligente(ttl_por_defecto=300)
cache_global = _cache_global


def obtener_cache() -> CacheInteligente:
    return _cache_global


# =============================================================================
# HELPERS DB
# =============================================================================

def _query_all(sql: str) -> list:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(sql)
    datos = cursor.fetchall()
    conn.close()
    return datos


# =============================================================================
# OBJETIVOS
# =============================================================================

def cargar_objetivos_en_cache(ttl: int = 300) -> None:
    try:
        objetivos = _query_all(
            "SELECT id, nombre, dias_semana FROM objetivos ORDER BY nombre"
        )

        cache_global.set("objetivos:lista", objetivos, ttl)

        por_id = {
            fila[0]: {
                "id": fila[0],
                "nombre": fila[1],
                "dias": fila[2]
            }
            for fila in objetivos
        }

        cache_global.set("objetivos:por_id", por_id, ttl)

    except Exception as e:
        logger.exception("Error cacheando objetivos: %s", e)


def obtener_objetivos_cache(generar_si_falta: bool = True) -> List[tuple]:
    def generador():
        return _query_all(
            "SELECT id, nombre, dias_semana FROM objetivos ORDER BY nombre"
        )

    return cache_global.get(
        "objetivos:lista",
        generador if generar_si_falta else None
    ) or []


def obtener_objetivo_por_id_cache(objetivo_id: int) -> Optional[dict]:
    datos = cache_global.get("objetivos:por_id")
    return datos.get(objetivo_id) if datos else None


# =============================================================================
# SUPERVISORES
# =============================================================================

def cargar_supervisores_en_cache(ttl: int = 300) -> None:
    try:
        supervisores = _query_all(
            "SELECT id, nombre FROM supervisores ORDER BY nombre"
        )

        cache_global.set("supervisores:lista", supervisores, ttl)

        por_id = {
            fila[0]: {
                "id": fila[0],
                "nombre": fila[1]
            }
            for fila in supervisores
        }

        cache_global.set("supervisores:por_id", por_id, ttl)

    except Exception as e:
        logger.exception("Error cacheando supervisores: %s", e)


def obtener_supervisores_cache(generar_si_falta: bool = True) -> List[tuple]:
    def generador():
        return _query_all(
            "SELECT id, nombre FROM supervisores ORDER BY nombre"
        )

    return cache_global.get(
        "supervisores:lista",
        generador if generar_si_falta else None
    ) or []


def obtener_supervisor_por_id_cache(supervisor_id: int) -> Optional[dict]:
    datos = cache_global.get("supervisores:por_id")
    return datos.get(supervisor_id) if datos else None


# =============================================================================
# USUARIOS
# =============================================================================

def cargar_usuarios_en_cache(ttl: int = 600) -> None:
    try:
        usuarios = _query_all(
            "SELECT id, username, rol FROM usuarios ORDER BY username"
        )

        cache_global.set("usuarios:lista", usuarios, ttl)

        por_id = {
            fila[0]: {
                "id": fila[0],
                "username": fila[1],
                "rol": fila[2]
            }
            for fila in usuarios
        }

        cache_global.set("usuarios:por_id", por_id, ttl)

    except Exception as e:
        logger.exception("Error cacheando usuarios: %s", e)


def obtener_usuarios_cache(generar_si_falta: bool = True) -> List[tuple]:
    def generador():
        return _query_all(
            "SELECT id, username, rol FROM usuarios ORDER BY username"
        )

    return cache_global.get(
        "usuarios:lista",
        generador if generar_si_falta else None
    ) or []


# =============================================================================
# INVALIDACIONES
# =============================================================================

def invalidar_objetivos() -> None:
    cache_global.invalidar_patron("objetivo")


def invalidar_supervisores() -> None:
    cache_global.invalidar_patron("supervisor")


def invalidar_pasadas() -> None:
    cache_global.invalidar_patron("pasada")
    cache_global.invalidar_patron("contar_pasadas")
    cache_global.invalidar_patron("turno")


def invalidar_usuarios() -> None:
    cache_global.invalidar_patron("usuario")


def invalidar_todo() -> None:
    cache_global.limpiar()