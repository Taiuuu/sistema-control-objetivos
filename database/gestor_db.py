# =============================================================================
# VESP Organizations - Gestor de Conexiones a Base de Datos
# Pool de conexiones y context managers optimizados
# =============================================================================

import sqlite3
import threading
import os
from typing import Optional, Any, Generator
from contextlib import contextmanager
from functools import wraps
import time

from database.db import DB_PATH


class GestorDB:
    """
    Gestor centralizado de conexiones SQLite con pool y caching de conexiones.
    Thread-safe y optimizado para múltiples accesos concurrentes.
    """
    
    _instancia: Optional['GestorDB'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton para garantizar una sola instancia del gestor."""
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = super().__new__(cls)
                    cls._instancia._inicializado = False
        return cls._instancia
    
    def __init__(self):
        if self._inicializado:
            return
        self._inicializado = True
        self._local = threading.local()
        self._stats = {
            "conexiones_creadas": 0,
            "conexiones_reusadas": 0,
            "queries_ejecutadas": 0,
            "queries_cacheadas": 0
        }
        self._cache_prepared = {}
    
    def obtener_conexion(self) -> sqlite3.Connection:
        """
        Obtiene una conexión del pool local del hilo actual.
        Usa conexión por hilo para evitar problemas de concurrencia SQLite.
        """
        if not hasattr(self._local, 'conexion') or self._local.conexion is None:
            self._local.conexion = self._crear_conexion()
            self._stats["conexiones_creadas"] += 1
        else:
            self._stats["conexiones_reusadas"] += 1
        
        return self._local.conexion
    
    def _crear_conexion(self) -> sqlite3.Connection:
        """Crea una nueva conexión optimizada."""
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Optimizaciones de rendimiento SQLite
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
        return conn
    
    def cerrar_conexion(self) -> None:
        """Cierra la conexión del hilo actual."""
        if hasattr(self._local, 'conexion') and self._local.conexion:
            try:
                self._local.conexion.close()
            except Exception:
                pass
            self._local.conexion = None
    
    def ejecutar(self, query: str, params: tuple = (), 
                 cache: bool = False, ttl: int = 300) -> list:
        """
        Ejecuta una query con opciones de caching.
        
        Args:
            query: SQL query
            params: Parámetros de la query
            cache: Si True, cachea el resultado
            ttl: Tiempo de vida del cache en segundos
        """
        self._stats["queries_ejecutadas"] += 1
        
        # Intentar obtener del cache si está habilitado
        if cache:
            cache_key = f"{query}:{params}"
            # Simple hash para la clave
            from services.cache import cache_global
            resultado_cache = cache_global.get(cache_key)
            if resultado_cache is not None:
                self._stats["queries_cacheadas"] += 1
                return resultado_cache
        
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith("SELECT"):
            resultados = cursor.fetchall()
            # Convertir a dict para mayor flexibilidad
            filas = [dict(row) for row in resultados]
            
            if cache and filas:
                cache_global.set(f"{query}:{params}", filas, ttl)
            
            return filas
        else:
            conn.commit()
            return []
    
    def ejecutar_many(self, query: str, datos: list[tuple]) -> int:
        """
        Ejecuta una query con múltiples conjuntos de parámetros.
        Mucho más eficiente que ejecutar en loop.
        """
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        cursor.executemany(query, datos)
        conn.commit()
        return cursor.rowcount
    
    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Context manager para transacciones.
        Uso:
            with db.transaction():
                db.ejecutar("INSERT...")
                db.ejecutar("UPDATE...")
        """
        conn = self.obtener_conexion()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def ejecutar_scalar(self, query: str, params: tuple = ()) -> Any:
        """Ejecuta query y retorna un solo valor (primera columna, primera fila)."""
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(query, params)
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    
    def ejecutar_dict(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Ejecuta query y retorna un solo diccionario."""
        resultados = self.ejecutar(query, params)
        return resultados[0] if resultados else None
    
    def obtener_stats(self) -> dict:
        """Retorna estadísticas de uso del gestor."""
        total = self._stats["queries_ejecutadas"]
        if total > 0:
            cache_hit_rate = (self._stats["queries_cacheadas"] / total) * 100
        else:
            cache_hit_rate = 0
        
        return {
            **self._stats,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "conexiones_activas": 1 if hasattr(self._local, 'conexion') and self._local.conexion else 0
        }
    
    def reset_stats(self) -> None:
        """Resetea las estadísticas."""
        self._stats = {
            "conexiones_creadas": 0,
            "conexiones_reusadas": 0,
            "queries_ejecutadas": 0,
            "queries_cacheadas": 0
        }


# Instancia global
gestor_db = GestorDB()


# =============================================================================
# DECORADORES Y UTILIDADES
# =============================================================================

def con_cache(ttl: int = 300):
    """
    Decorador para cachear resultados de funciones que ejecutan queries.
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de cache basada en argumentos
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Intentar obtener del cache global
            from services.cache import cache_global
            resultado = cache_global.get(cache_key)
            if resultado is not None:
                return resultado
            
            # Ejecutar función original
            resultado = func(*args, **kwargs)
            
            # Cachear resultado
            if resultado is not None:
                cache_global.set(cache_key, resultado, ttl)
            
            return resultado
        return wrapper
    return decorador


@contextmanager
def db_transaction() -> Generator:
    """
    Context manager global para transacciones.
    Uso:
        with db_transaction() as db:
            db.ejecutar("INSERT INTO...")
            db.ejecutar("UPDATE...")
    """
    with gestor_db.transaction():
        yield gestor_db


# =============================================================================
# COMPATIBILIDAD CON CÓDIGO EXISTENTE
# =============================================================================

def conectar() -> sqlite3.Connection:
    """
    Función de compatibilidad para código existente.
    Preferir usar gestor_db.obtener_conexion() directamente.
    """
    return gestor_db.obtener_conexion()


def ejecutar_query(query: str, params: tuple = ()) -> list:
    """Función de compatibilidad para queries simples."""
    return gestor_db.ejecutar(query, params)


def ejecutar_scalar(query: str, params: tuple = ()) -> Any:
    """Función de compatibilidad para queries escalares."""
    return gestor_db.ejecutar_scalar(query, params)