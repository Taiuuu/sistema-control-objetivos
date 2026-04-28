# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Capa de Abstracción de Datos - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo que proporciona abstracción de datos con patrón Repository.

Define:
- Clases de dominio (Usuario, Objetivo, Supervisor, Pasada) como DataClasses
- Interfaz abstracta DataProvider para futuras implementaciones
- Implementación SQLiteDataProvider optimizada con caché y paginación
- Métodos de búsqueda, filtrado y estadísticas
- Preparación para futuro multi-usuario con sincronización

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from database.gestor_db import gestor_db
from services.cache import cache_global
from .exceptions import DataProviderError

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# CLASES DE DOMINIO (DataClasses)
# =============================================================================

@dataclass
class Usuario:
    """Representa un usuario del sistema."""
    id: int
    username: str
    rol: str
    debe_cambiar_password: bool


@dataclass
class Objetivo:
    """Representa un objetivo/meta a ser controlado."""
    id: int
    nombre: str
    descripcion: str
    fecha_inicio: str
    fecha_fin: Optional[str]
    activo: bool


@dataclass
class Supervisor:
    """Representa un supervisor/empleado."""
    id: int
    nombre: str
    activo: bool


@dataclass
class Pasada:
    """Representa un registro de control (pasada)."""
    id: int
    fecha: str
    hora: str
    turno: str
    supervisor_id: int
    objetivo_id: int
    notas: Optional[str] = None
    fecha_operativa: str = ""


# =============================================================================
# INTERFAZ ABSTRACTA
# =============================================================================

class DataProvider(ABC):
    """Interfaz abstracta para proveedores de datos.
    
    Contrato que debe cumplir cualquier implementación
    (SQLite local, API REST remota, etc).
    """

    @abstractmethod
    def get_usuarios(self) -> List[Usuario]:
        """Obtiene lista de todos los usuarios."""
        pass

    @abstractmethod
    def get_objetivos(self) -> List[Objetivo]:
        """Obtiene lista de todos los objetivos activos."""
        pass

    @abstractmethod
    def get_supervisores(self) -> List[Supervisor]:
        """Obtiene lista de todos los supervisores activos."""
        pass

    @abstractmethod
    def get_pasadas(self, fecha: Optional[str] = None) -> List[Pasada]:
        """Obtiene registros, opcionalmente filtrados por fecha."""
        pass

    @abstractmethod
    def crear_pasada(self, pasada: Pasada) -> bool:
        """Crea un nuevo registro de pasada."""
        pass

    @abstractmethod
    def sincronizar_datos(self) -> Dict[str, Any]:
        """Sincroniza datos con servidor remoto (futuro)."""
        pass


# =============================================================================
# IMPLEMENTACIÓN CON SQLITE
# =============================================================================

class SQLiteDataProvider(DataProvider):
    """Proveedor de datos local con SQLite OPTIMIZADO.
    
    Características:
    - Caché de 2 minutos para queries frecuentes
    - Paginación para grandes datasets
    - Búsqueda y filtrado con type hints completos
    - Métodos de utilidad para estado y estadísticas
    - Thread-safe mediante gestor_db
    """

    @cache_global.auto_cache(ttl=120)
    def get_usuarios(self) -> List[Usuario]:
        """Obtiene usuarios con cache de 2 minutos.
        
        Returns:
            Lista de objetos Usuario.
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            rows = gestor_db.ejecutar(
                "SELECT id, username, rol, debe_cambiar_password FROM usuarios"
            )
            return [
                Usuario(
                    id=r['id'],
                    username=r['username'],
                    rol=r['rol'],
                    debe_cambiar_password=bool(r['debe_cambiar_password'])
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            raise DataProviderError(f"Error obteniendo usuarios: {str(e)}")

    @cache_global.auto_cache(ttl=120)
    def get_objetivos(self) -> List[Objetivo]:
        """Obtiene objetivos activos con cache de 2 minutos.
        
        Returns:
            Lista de objetos Objetivo (solo activos).
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            rows = gestor_db.ejecutar(
                """SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo
                   FROM objetivos WHERE activo = 1 ORDER BY nombre"""
            )
            return [
                Objetivo(
                    id=r['id'],
                    nombre=r['nombre'],
                    descripcion=r['descripcion'],
                    fecha_inicio=r['fecha_inicio'],
                    fecha_fin=r['fecha_fin'],
                    activo=bool(r['activo'])
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error obteniendo objetivos: {e}")
            raise DataProviderError(f"Error obteniendo objetivos: {str(e)}")

    @cache_global.auto_cache(ttl=120)
    def get_supervisores(self) -> List[Supervisor]:
        """Obtiene supervisores activos con cache de 2 minutos.
        
        Returns:
            Lista de objetos Supervisor (solo activos).
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            rows = gestor_db.ejecutar(
                """SELECT id, nombre, activo FROM supervisores 
                   WHERE fecha_baja IS NULL ORDER BY nombre"""
            )
            return [
                Supervisor(id=r['id'], nombre=r['nombre'], activo=bool(r['activo']))
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error obteniendo supervisores: {e}")
            raise DataProviderError(f"Error obteniendo supervisores: {str(e)}")

    def get_pasadas(self, fecha: Optional[str] = None) -> List[Pasada]:
        """Obtiene pasadas con lazy loading opcional.
        
        Args:
            fecha: Si se especifica, filtra por esa fecha (YYYY-MM-DD).
        
        Returns:
            Lista de objetos Pasada (máximo últimas 100).
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            cache_key = f"pasadas:{fecha}:limit_100" if fecha else None
            
            # Intentar cache para fechas específicas
            if cache_key:
                resultado = cache_global.get(cache_key)
                if resultado is not None:
                    return resultado
            
            query = """SELECT p.id, p.fecha, p.hora, p.turno, p.supervisor_id,
                              p.objetivo_id, p.notas, p.fecha_operativa
                       FROM pasadas p"""
            params = []
            
            if fecha:
                query += " WHERE p.fecha = ?"
                params.append(fecha)
            
            query += " ORDER BY p.fecha DESC, p.hora DESC LIMIT 100"
            
            rows = gestor_db.ejecutar(query, tuple(params) if params else ())
            
            pasadas = [
                Pasada(
                    id=r['id'],
                    fecha=r['fecha'],
                    hora=r['hora'],
                    turno=r['turno'],
                    supervisor_id=r['supervisor_id'],
                    objetivo_id=r['objetivo_id'],
                    notas=r['notas'],
                    fecha_operativa=r['fecha_operativa']
                )
                for r in rows
            ]
            
            # Cachear solo si hay fecha específica
            if cache_key:
                cache_global.set(cache_key, pasadas, 60)
            
            logger.debug(f"Obtenidas {len(pasadas)} pasadas")
            return pasadas
            
        except Exception as e:
            logger.error(f"Error obteniendo pasadas: {e}")
            raise DataProviderError(f"Error obteniendo pasadas: {str(e)}")

    def crear_pasada(self, pasada: Pasada) -> bool:
        """Crea una nueva pasada en la BD.
        
        Args:
            pasada: Objeto Pasada con datos a insertar.
        
        Returns:
            True si se creó exitosamente.
            
        Raises:
            DataProviderError: Si hay error en inserción.
        """
        try:
            with gestor_db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO pasadas
                       (fecha, hora, turno, supervisor_id, objetivo_id, notas, fecha_operativa)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (pasada.fecha, pasada.hora, pasada.turno, pasada.supervisor_id,
                     pasada.objetivo_id, pasada.notas, pasada.fecha_operativa)
                )
            logger.info(f"Pasada creada para objetivo {pasada.objetivo_id}")
            return True
        except Exception as e:
            logger.error(f"Error creando pasada: {e}")
            raise DataProviderError(f"Error creando pasada: {str(e)}")

    def sincronizar_datos(self) -> Dict[str, Any]:
        """Simulación de sincronización (para futuro con servidor).
        
        Returns:
            Diccionario con estado de sincronización.
        """
        return {
            "estado": "local",
            "mensaje": "Datos locales, sin servidor remoto",
            "timestamp": None
        }

    # =========================================================================
    # PAGINACIÓN
    # =========================================================================

    def get_objetivos_paginados(
        self, pagina: int = 1, por_pagina: int = 50
    ) -> Dict[str, Any]:
        """Obtiene objetivos con paginación.
        
        Args:
            pagina: Número de página (1-based).
            por_pagina: Cantidad de items por página.
        
        Returns:
            Diccionario con items, total, pagina, total_paginas.
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            offset = (pagina - 1) * por_pagina
            
            total = gestor_db.ejecutar_scalar("SELECT COUNT(*) FROM objetivos") or 0
            
            rows = gestor_db.ejecutar(
                """SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo
                   FROM objetivos ORDER BY nombre LIMIT ? OFFSET ?""",
                (por_pagina, offset)
            )
            
            objetivos = [
                Objetivo(
                    id=r['id'],
                    nombre=r['nombre'],
                    descripcion=r['descripcion'],
                    fecha_inicio=r['fecha_inicio'],
                    fecha_fin=r['fecha_fin'],
                    activo=bool(r['activo'])
                )
                for r in rows
            ]
            
            total_paginas = (total // por_pagina) + (1 if total % por_pagina > 0 else 0)
            
            return {
                'items': objetivos,
                'total': total,
                'pagina': pagina,
                'por_pagina': por_pagina,
                'total_paginas': total_paginas
            }
        except Exception as e:
            logger.error(f"Error obteniendo objetivos paginados: {e}")
            raise DataProviderError(f"Error obteniendo objetivos: {str(e)}")

    def get_pasadas_paginadas(
        self, pagina: int = 1, por_pagina: int = 100, fecha: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene pasadas con paginación.
        
        Args:
            pagina: Número de página (1-based).
            por_pagina: Cantidad de items por página.
            fecha: Filtro opcional por fecha (YYYY-MM-DD).
        
        Returns:
            Diccionario paginado con pasadas.
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            offset = (pagina - 1) * por_pagina
            
            if fecha:
                count_query = "SELECT COUNT(*) FROM pasadas WHERE fecha = ?"
                data_query = """SELECT id, fecha, hora, turno, supervisor_id, objetivo_id,
                                       notas, fecha_operativa FROM pasadas
                                WHERE fecha = ? ORDER BY fecha DESC, hora DESC
                                LIMIT ? OFFSET ?"""
                count_params = (fecha,)
                data_params = (fecha, por_pagina, offset)
            else:
                count_query = "SELECT COUNT(*) FROM pasadas"
                data_query = """SELECT id, fecha, hora, turno, supervisor_id, objetivo_id,
                                       notas, fecha_operativa FROM pasadas
                                ORDER BY fecha DESC, hora DESC LIMIT ? OFFSET ?"""
                count_params = ()
                data_params = (por_pagina, offset)
            
            total = gestor_db.ejecutar_scalar(count_query, count_params) or 0
            rows = gestor_db.ejecutar(data_query, data_params)
            
            pasadas = [
                Pasada(
                    id=r['id'],
                    fecha=r['fecha'],
                    hora=r['hora'],
                    turno=r['turno'],
                    supervisor_id=r['supervisor_id'],
                    objetivo_id=r['objetivo_id'],
                    notas=r['notas'],
                    fecha_operativa=r['fecha_operativa']
                )
                for r in rows
            ]
            
            total_paginas = (total // por_pagina) + (1 if total % por_pagina > 0 else 0)
            
            return {
                'items': pasadas,
                'total': total,
                'pagina': pagina,
                'por_pagina': por_pagina,
                'total_paginas': total_paginas
            }
        except Exception as e:
            logger.error(f"Error obteniendo pasadas paginadas: {e}")
            raise DataProviderError(f"Error obteniendo pasadas: {str(e)}")

    # =========================================================================
    # BÚSQUEDA
    # =========================================================================

    def buscar_objetivos(self, texto: str) -> List[Objetivo]:
        """Busca objetivos por nombre (case-insensitive).
        
        Args:
            texto: Texto a buscar (búsqueda LIKE).
        
        Returns:
            Lista de objetivos que coinciden (máximo 50).
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            rows = gestor_db.ejecutar(
                """SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo
                   FROM objetivos WHERE nombre LIKE ? LIMIT 50""",
                (f"%{texto}%",)
            )
            return [
                Objetivo(
                    id=r['id'],
                    nombre=r['nombre'],
                    descripcion=r['descripcion'],
                    fecha_inicio=r['fecha_inicio'],
                    fecha_fin=r['fecha_fin'],
                    activo=bool(r['activo'])
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error buscando objetivos: {e}")
            raise DataProviderError(f"Error buscando: {str(e)}")

    def buscar_supervisores(self, texto: str) -> List[Supervisor]:
        """Busca supervisores por nombre (case-insensitive).
        
        Args:
            texto: Texto a buscar (búsqueda LIKE).
        
        Returns:
            Lista de supervisores que coinciden (máximo 50).
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            rows = gestor_db.ejecutar(
                """SELECT id, nombre, activo FROM supervisores
                   WHERE nombre LIKE ? LIMIT 50""",
                (f"%{texto}%",)
            )
            return [
                Supervisor(id=r['id'], nombre=r['nombre'], activo=bool(r['activo']))
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error buscando supervisores: {e}")
            raise DataProviderError(f"Error buscando: {str(e)}")

    # =========================================================================
    # UTILIDAD Y ESTADÍSTICAS
    # =========================================================================

    def contar_pasadas(
        self, fecha: str, objetivo_id: int, turno: Optional[str] = None
    ) -> int:
        """Cuenta pasadas para un objetivo en una fecha.
        
        Args:
            fecha: Fecha a consultar (YYYY-MM-DD).
            objetivo_id: ID del objetivo.
            turno: Turno opcional (Mañana, Tarde, Noche).
        
        Returns:
            Cantidad de pasadas.
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            query = "SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?"
            params = [fecha, objetivo_id]
            
            if turno:
                query += " AND turno = ?"
                params.append(turno)
            
            result = gestor_db.ejecutar_scalar(query, tuple(params)) or 0
            return result
        except Exception as e:
            logger.error(f"Error contando pasadas: {e}")
            raise DataProviderError(f"Error contando pasadas: {str(e)}")

    def obtener_estado_cobertura(self, fecha: str, objetivo_id: int) -> Dict[str, Any]:
        """Retorna el estado de cobertura para un objetivo en una fecha.
        
        Args:
            fecha: Fecha a consultar (YYYY-MM-DD).
            objetivo_id: ID del objetivo.
        
        Returns:
            Diccionario con pasadas_dia, pasadas_noche, estado.
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            query = """SELECT
                        SUM(CASE WHEN turno IN ('Mañana', 'Tarde', 'Completo') THEN 1 ELSE 0 END) as dia,
                        SUM(CASE WHEN turno IN ('Noche', 'Completo') THEN 1 ELSE 0 END) as noche
                       FROM pasadas
                       WHERE fecha = ? AND objetivo_id = ?"""
            
            resultado = gestor_db.ejecutar(query, (fecha, objetivo_id))
            
            if resultado and resultado[0]:
                pasadas_dia = resultado[0]['dia'] or 0
                pasadas_noche = resultado[0]['noche'] or 0
            else:
                pasadas_dia = 0
                pasadas_noche = 0
            
            # Determinar estado
            if pasadas_dia > 0 and pasadas_noche > 0:
                estado = "completo"
            elif pasadas_dia > 0 or pasadas_noche > 0:
                estado = "parcial"
            else:
                estado = "sin_datos"
            
            return {
                'pasadas_dia': pasadas_dia,
                'pasadas_noche': pasadas_noche,
                'estado': estado
            }
        except Exception as e:
            logger.error(f"Error obteniendo cobertura: {e}")
            raise DataProviderError(f"Error obteniendo cobertura: {str(e)}")

    def get_resumen_rapido(self) -> Dict[str, int]:
        """Obtiene resumen rápido de estadísticas en una sola query.
        
        Returns:
            Diccionario con conteos de objetivos, supervisores, pasadas.
            
        Raises:
            DataProviderError: Si hay error en consulta.
        """
        try:
            query = """SELECT
                        (SELECT COUNT(*) FROM objetivos) as total_objetivos,
                        (SELECT COUNT(*) FROM supervisores WHERE fecha_baja IS NULL) as supervisores,
                        (SELECT COUNT(*) FROM pasadas WHERE fecha = date('now')) as hoy,
                        (SELECT COUNT(*) FROM pasadas WHERE fecha >= date('now', '-7 days')) as semana"""
            
            resultado = gestor_db.ejecutar(query)
            
            if resultado and resultado[0]:
                r = resultado[0]
                return {
                    'total_objetivos': r.get('total_objetivos', 0) or 0,
                    'total_supervisores': r.get('supervisores', 0) or 0,
                    'pasadas_hoy': r.get('hoy', 0) or 0,
                    'pasadas_semana': r.get('semana', 0) or 0
                }
            return {
                'total_objetivos': 0,
                'total_supervisores': 0,
                'pasadas_hoy': 0,
                'pasadas_semana': 0
            }
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            raise DataProviderError(f"Error obteniendo resumen: {str(e)}")


# =============================================================================
# SINGLETON GLOBAL
# =============================================================================

# Instancia global del proveedor de datos
data_provider: DataProvider = SQLiteDataProvider()


def get_data_provider() -> DataProvider:
    """Obtiene la instancia actual del proveedor de datos.
    
    Returns:
        La instancia global de DataProvider (SQLiteDataProvider por defecto).
        
    Example:
        >>> provider = get_data_provider()
        >>> usuarios = provider.get_usuarios()
    """
    return data_provider


def set_data_provider(provider: DataProvider) -> None:
    """Cambia la instancia del proveedor de datos.
    
    Permite cambiar entre SQLiteDataProvider o mocks para testing.
    
    Args:
        provider: Instancia que implementa DataProvider.
        
    Example:
        >>> mock_provider = MockDataProvider()
        >>> set_data_provider(mock_provider)
    """
    global data_provider
    data_provider = provider
    logger.info(f"Proveedor de datos cambiado a {type(provider).__name__}")
