# =============================================================================
# VESP Organizations - Sistema de Caché Inteligente
# =============================================================================

import logging
import time
import threading
from typing import Any, Optional, List, Dict, Callable
from database.db import conectar

# Configurar logger
logger = logging.getLogger(__name__)


class EntradaCache:
    """Representa una entrada en el caché con TTL."""
    """Representa una entrada en el caché con TTL."""
    
    def __init__(self, valor: Any, ttl_segundos: int = 300):
        self.valor = valor
        self.ttl_segundos = ttl_segundos
        self.timestamp_creacion = time.time()
        self.hits = 0  # Contador de accesos
    
    def esta_expirada(self) -> bool:
        """Verifica si la entrada ha expirado."""
        tiempo_transcurrido = time.time() - self.timestamp_creacion
        return tiempo_transcurrido > self.ttl_segundos
        return tiempo_transcurrido > self.ttl_segundos
    
    def obtener(self) -> Any:
        """Obtiene el valor incrementando el contador de hits."""
        self.hits += 1
        return self.valor
    
    def antiguedad_segundos(self) -> float:
        """Retorna cuántos segundos tiene la entrada."""
        return time.time() - self.timestamp_creacion
    
    def info(self) -> dict:
        """Retorna info de la entrada para debugging."""
        return {
            "ttl_segundos": self.ttl_segundos,
            "antiguedad_segundos": self.antiguedad_segundos(),
            "antiguedad_segundos": self.antiguedad_segundos(),
            "hits": self.hits,
            "expirada": self.esta_expirada()
        }


class CacheInteligente:
    """
    Sistema de caché centralizado con TTL, invalidación y métricas.
    Thread-safe para uso concurrente.
    """
    
    def __init__(self, ttl_por_defecto: int = 300):
        """
        Args:
            ttl_por_defecto: TTL en segundos para nuevas entradas (default: 5 min)
        """
        self._cache: Dict[str, EntradaCache] = {}
        self._ttl_por_defecto = ttl_por_defecto
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidaciones": 0
        }
    
    def set(self, clave: str, valor: Any, ttl_segundos: Optional[int] = None) -> None:
        """Almacena un valor en el caché."""
        """Almacena un valor en el caché."""
        ttl = ttl_segundos or self._ttl_por_defecto
        with self._lock:
            self._cache[clave] = EntradaCache(valor, ttl)
    
    def get(self, clave: str, generador: Optional[Callable] = None) -> Optional[Any]:
        """
        Obtiene un valor del caché.
        Si no existe o está expirado, y se proporciona generador, lo calcula.
        
        Args:
            clave: Clave del caché
            generador: Callable que genera el valor si no está en caché
            clave: Clave del caché
            generador: Callable que genera el valor si no está en caché
        
        Returns:
            Valor del caché o None si no existe y no hay generador
            Valor del caché o None si no existe y no hay generador
        """
        with self._lock:
            if clave in self._cache:
                entrada = self._cache[clave]
                if not entrada.esta_expirada():
                    self._stats["hits"] += 1
                    return entrada.obtener()
                else:
                    # Entrada expirada, eliminarla
                    del self._cache[clave]
        
        # Caché miss
        self._stats["misses"] += 1
        
        if generador:
            valor = generador()
            if valor is not None:
                self.set(clave, valor)
            return valor
        
        return None
    
    def existe(self, clave: str) -> bool:
        """Verifica si existe una clave válida en caché."""
        """Verifica si existe una clave válida en caché."""
        with self._lock:
            if clave not in self._cache:
                return False
            if self._cache[clave].esta_expirada():
                del self._cache[clave]
                return False
            return True
    
    def eliminar(self, clave: str) -> bool:
        """Elimina una clave del caché."""
        """Elimina una clave del caché."""
        with self._lock:
            if clave in self._cache:
                del self._cache[clave]
                self._stats["invalidaciones"] += 1
                return True
            return False
    
    def limpiar(self) -> None:
        """Limpia todas las entradas del caché."""
        """Limpia todas las entradas del caché."""
        with self._lock:
            cantidad = len(self._cache)
            self._cache.clear()
            self._stats["invalidaciones"] += cantidad
    
    def limpiar_expiradas(self) -> int:
        """Elimina todas las entradas expiradas."""
        """Elimina todas las entradas expiradas."""
        with self._lock:
            claves_a_eliminar = [
                clave for clave, entrada in self._cache.items()
                if entrada.esta_expirada()
            ]
            for clave in claves_a_eliminar:
                del self._cache[clave]
            self._stats["invalidaciones"] += len(claves_a_eliminar)
            return len(claves_a_eliminar)
    
    def invalidar_patron(self, patron: str) -> int:
        """
        Invalida todas las claves que contengan el patrón.
        Ej: invalidar_patron("objetivo:") elimina todas las claves objetivo:*
        """
        with self._lock:
            claves_a_eliminar = [
                clave for clave in self._cache.keys()
                if patron in clave
            ]
            for clave in claves_a_eliminar:
                del self._cache[clave]
            self._stats["invalidaciones"] += len(claves_a_eliminar)
            return len(claves_a_eliminar)
    
    def obtener_stats(self) -> dict:
        """Retorna estadísticas de uso del caché."""
        """Retorna estadísticas de uso del caché."""
        with self._lock:
            total_accesos = self._stats["hits"] + self._stats["misses"]
            tasa_acierto = (
                (self._stats["hits"] / total_accesos * 100) 
                if total_accesos > 0 else 0
            )
            
            return {
                "enumerador": len(self._cache),
            return {
                "enumerador": len(self._cache),
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "total_accesos": total_accesos,
                "tasa_acierto_porcentaje": round(tasa_acierto, 2),
                "invalidaciones": self._stats["invalidaciones"],
                "ttl_por_defecto_segundos": self._ttl_por_defecto
            }
    
    def obtener_detalles(self) -> dict:
        """Retorna detalles de todas las entradas en caché."""
        """Retorna detalles de todas las entradas en caché."""
        with self._lock:
            detalles = {}
            for clave, entrada in self._cache.items():
                detalles[clave] = entrada.info()
            return detalles
    
    def establecer_ttl_por_defecto(self, ttl_segundos: int) -> None:
        """Cambia el TTL por defecto para futuras entradas."""
        """Cambia el TTL por defecto para futuras entradas."""
        self._ttl_por_defecto = ttl_segundos
    
    def auto_cache(self, ttl: int = None):
        """
        Decorador para cachear automáticamente resultados de funciones.
        Uso:
        Uso:
            @cache_global.auto_cache(ttl=60)
            def mi_funcion():
                ...
            def mi_funcion():
                ...
        """
        def decorador(func):
            from functools import wraps
            from functools import wraps
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generar clave basada en nombre de función y argumentos
                clave = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                clave = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                resultado = self.get(clave)
                if resultado is not None:
                    return resultado
                resultado = func(*args, **kwargs)
                if resultado is not None:
                    self.set(clave, resultado, ttl or self._ttl_por_defecto)
                return resultado
            return wrapper
        return decorador


# =============================================================================
# INSTANCIA GLOBAL DE CACHÉ
# =============================================================================

_cache_global = CacheInteligente(ttl_por_defecto=300)  # 5 minutos por defecto


def obtener_cache() -> CacheInteligente:
    """Retorna la instancia global de caché."""
    """Retorna la instancia global de caché."""
    return _cache_global


# Alias para compatibilidad
cache_global = _cache_global


# =============================================================================
# FUNCIONES DE INVALIDACIÓN ESPECÍFICAS
# =============================================================================

def invalidar_objetivos() -> None:
    """Invalida todas las entradas relacionadas con objetivos."""
    _cache_global.invalidar_patron("objetivo")
    _cache_global.invalidar_patron("contar_pasadas")
    _cache_global.invalidar_patron("pasadas_turno")
def invalidar_objetivos() -> None:
    """Invalida todas las entradas relacionadas con objetivos."""
    _cache_global.invalidar_patron("objetivo")
    _cache_global.invalidar_patron("contar_pasadas")
    _cache_global.invalidar_patron("pasadas_turno")


def invalidar_supervisores() -> None:
    """Invalida todas las entradas relacionadas con supervisores."""
    _cache_global.invalidar_patron("supervisor")
    _cache_global.invalidar_patron("cargar_supervisores")
def invalidar_supervisores() -> None:
    """Invalida todas las entradas relacionadas con supervisores."""
    _cache_global.invalidar_patron("supervisor")
    _cache_global.invalidar_patron("cargar_supervisores")


def invalidar_pasadas() -> None:
    """Invalida todas las entradas relacionadas con pasadas."""
    _cache_global.invalidar_patron("pasada")
    _cache_global.invalidar_patron("contar_pasadas")
    _cache_global.invalidar_patron("pasadas_turno")
def invalidar_pasadas() -> None:
    """Invalida todas las entradas relacionadas con pasadas."""
    _cache_global.invalidar_patron("pasada")
    _cache_global.invalidar_patron("contar_pasadas")
    _cache_global.invalidar_patron("pasadas_turno")


def invalidar_todo() -> None:
    """Invalida todo el caché."""
def invalidar_todo() -> None:
    """Invalida todo el caché."""
    _cache_global.limpiar()


# =============================================================================
# FUNCIONES DE CACHÉ PARA ENTIDADES
# =============================================================================

def cargar_objetivos_en_cache(ttl: int = 300) -> None:
    """Carga todos los objetivos en caché."""
def cargar_objetivos_en_cache(ttl: int = 300) -> None:
    """Carga todos los objetivos en caché."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, dias_semana FROM objetivos ORDER BY nombre")
        objetivos = cursor.fetchall()
        conn.close()
        
        _cache_global.set("objetivos:lista", objetivos, ttl)
        
        # También cachear índice por ID
        obj_por_id = {obj[0]: {"id": obj[0], "nombre": obj[1], "dias": obj[2]} 
                      for obj in objetivos}
        _cache_global.set("objetivos:por_id", obj_por_id, ttl)
        
    except Exception as e:
        print(f"Error cacheando objetivos: {e}")
        print(f"Error cacheando objetivos: {e}")


def obtener_objetivos_cache(generar_si_falta: bool = True) -> List[tuple]:
    """
    Obtiene objetivos del caché.
    Si no existen y generar_si_falta=True, los genera.
    """
    def generador():
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, dias_semana FROM objetivos ORDER BY nombre")
            resultado = cursor.fetchall()
            conn.close()
            return resultado
        except:
        except:
            return []
    
    resultado = _cache_global.get("objetivos:lista", generador if generar_si_falta else None)
    return resultado or []


def obtener_objetivo_por_id_cache(objetivo_id: int) -> Optional[dict]:
    """Obtiene un objetivo específico del caché por ID."""
    objetivos_por_id = _cache_global.get("objetivos:por_id")
    if objetivos_por_id:
        return objetivos_por_id.get(objetivo_id)
    return None


def cargar_supervisores_en_cache(ttl: int = 300) -> None:
    """Carga todos los supervisores en caché."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM supervisores ORDER BY nombre")
        supervisores = cursor.fetchall()
        conn.close()
        
        _cache_global.set("supervisores:lista", supervisores, ttl)
        
        # Índice por ID
        sup_por_id = {sup[0]: {"id": sup[0], "nombre": sup[1]} 
                      for sup in supervisores}
        _cache_global.set("supervisores:por_id", sup_por_id, ttl)
        
    except Exception as e:
        print(f"Error cacheando supervisores: {e}")


def obtener_supervisores_cache(generar_si_falta: bool = True) -> List[tuple]:
    """
    Obtiene supervisores del caché.
    Si no existen y generar_si_falta=True, los genera.
    """
    def generador():
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM supervisores ORDER BY nombre")
            resultado = cursor.fetchall()
            conn.close()
            return resultado
        except:
            return []
    
    resultado = _cache_global.get("supervisores:lista", generador if generar_si_falta else None)
    return resultado or []


def obtener_supervisor_por_id_cache(supervisor_id: int) -> Optional[dict]:
    """Obtiene un supervisor específico del caché por ID."""
    supervisores_por_id = _cache_global.get("supervisores:por_id")
    if supervisores_por_id:
        return supervisores_por_id.get(supervisor_id)
    return None


def cargar_usuarios_en_cache(ttl: int = 600) -> None:
    """Carga todos los usuarios en caché (TTL más largo por seguridad)."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, rol FROM usuarios ORDER BY username")
        usuarios = cursor.fetchall()
        conn.close()
        
        _cache_global.set("usuarios:lista", usuarios, ttl)
        
        # Índice por ID
        users_por_id = {user[0]: {"id": user[0], "username": user[1], "rol": user[2]} 
                        for user in usuarios}
        _cache_global.set("usuarios:por_id", users_por_id, ttl)
        
    except Exception as e:
        print(f"Error cacheando usuarios: {e}")


def obtener_usuarios_cache(generar_si_falta: bool = True) -> List[tuple]:
    """Obtiene usuarios del caché."""
    def generador():
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, rol FROM usuarios ORDER BY username")
            resultado = cursor.fetchall()
            conn.close()
            return resultado
        except:
            return []
    
    resultado = _cache_global.get("usuarios:lista", generador if generar_si_falta else None)
    return resultado or []


# =============================================================================
# FUNCIONES DE INVALIDACIÓN
# =============================================================================

def invalidar_objetivos() -> None:
    """Invalida el caché de objetivos."""
    _cache_global.invalidar_patron("objetivo")


def invalidar_supervisores() -> None:
    """Invalida el caché de supervisores."""
    _cache_global.invalidar_patron("supervisor")


def invalidar_usuarios() -> None:
    """Invalida el caché de usuarios."""
    _cache_global.invalidar_patron("usuario")


def invalidar_todo() -> None:
    """Invalida todo el caché."""
    _cache_global.limpiar()
