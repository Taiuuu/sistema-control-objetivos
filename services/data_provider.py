# =============================================================================
# VESP Organizations - Capa de Abstracción de Datos OPTIMIZADA
# Prepara el proyecto para multi-usuario y sincronización
# =============================================================================

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from database.gestor_db import gestor_db
from services.cache import cache_global


@dataclass
class Usuario:
    id: int
    username: str
    rol: str
    debe_cambiar_password: bool

@dataclass
class Objetivo:
    id: int
    nombre: str
    descripcion: str
    fecha_inicio: str
    fecha_fin: Optional[str]
    activo: bool

@dataclass
class Supervisor:
    id: int
    nombre: str
    activo: bool

@dataclass
class Pasada:
    id: int
    fecha: str
    hora: str
    turno: str
    supervisor_id: int
    objetivo_id: int
    notas: Optional[str]
    fecha_operativa: str  # Calculada para turnos nocturnos


class DataProvider(ABC):
    """Interfaz abstracta para proveedores de datos."""
    
    # Métodos base con implementación por defecto para crear_pasada
    def crear_pasada(self, pasada: Pasada) -> bool:
        """
        Método base que delegará a la implementación concreta.
        Por defecto retorna False - debe ser sobrescrito.
        """
        raise NotImplementedError("Debe implementarse en subclase")

    @abstractmethod
    def get_usuarios(self) -> List[Usuario]:
        pass

    @abstractmethod
    def get_objetivos(self) -> List[Objetivo]:
        pass

    @abstractmethod
    def get_supervisores(self) -> List[Supervisor]:
        pass

    @abstractmethod
    def get_pasadas(self, fecha: str = None) -> List[Pasada]:
        pass

    @abstractmethod
    def sincronizar_datos(self) -> Dict[str, Any]:
        """Sincronizar con servidor remoto (para futuro)."""
        pass
    
    # Métodos de utilidad comunes
    def contar_pasadas(self, fecha: str, objetivo_id: int, turno: str = None) -> int:
        """Cuenta pasadas para un objetivo en una fecha."""
        return 0  # Default - sobrescribir en implementación
    
    def obtener_estado_cobertura(self, fecha: str, objetivo_id: int) -> Dict[str, Any]:
        """Retorna el estado de cobertura para un objetivo."""
        return {
            'pasadas_dia': 0,
            'pasadas_noche': 0,
            'estado': 'sin_datos'
        }


class SQLiteDataProvider(DataProvider):
    """
    Proveedor de datos local con SQLite OPTIMIZADO.
    Usa gestor_db y caché para mejor rendimiento.
    """

    @cache_global.auto_cache(ttl=120)
    def get_usuarios(self) -> List[Usuario]:
        """Obtiene usuarios con cache de 2 minutos."""
        rows = gestor_db.ejecutar("SELECT id, username, rol, debe_cambiar_password FROM usuarios")
        return [Usuario(id=r['id'], username=r['username'], rol=r['rol'], 
                       debe_cambiar_password=bool(r['debe_cambiar_password'])) for r in rows]

    @cache_global.auto_cache(ttl=120)
    def get_objetivos(self) -> List[Objetivo]:
        """Obtiene objetivos con cache de 2 minutos."""
        rows = gestor_db.ejecutar("""
            SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo
            FROM objetivos WHERE activo = 1
        """)
        return [Objetivo(id=r['id'], nombre=r['nombre'], descripcion=r['descripcion'], 
                        fecha_inicio=r['fecha_inicio'], fecha_fin=r['fecha_fin'], 
                        activo=bool(r['activo'])) for r in rows]

    @cache_global.auto_cache(ttl=120)
    def get_supervisores(self) -> List[Supervisor]:
        """Obtiene supervisores con cache de 2 minutos."""
        rows = gestor_db.ejecutar("SELECT id, nombre, activo FROM supervisores WHERE activo = 1")
        return [Supervisor(id=r['id'], nombre=r['nombre'], activo=bool(r['activo'])) for r in rows]

    def get_pasadas(self, fecha: str = None) -> List[Pasada]:
        """
        Obtiene pasadas con lazy loading.
        Si no se especifica fecha, carga solo las últimas 100.
        """
        cache_key = f"pasadas:{fecha}:limit_100"
        
        # Intentar cache para fechas específicas
        if fecha:
            resultado = cache_global.get(cache_key)
            if resultado is not None:
                return resultado
        
        query = """
            SELECT p.id, p.fecha, p.hora, p.turno, p.supervisor_id, p.objetivo_id, p.notas,
                   p.fecha_operativa
            FROM pasadas p
        """
        params = []

        if fecha:
            query += " WHERE p.fecha = ?"
            params.append(fecha)

        query += " ORDER BY p.fecha DESC, p.hora DESC LIMIT 100"

        rows = gestor_db.ejecutar(query, tuple(params) if params else ())

        pasadas = [Pasada(id=r['id'], fecha=r['fecha'], hora=r['hora'], turno=r['turno'],
                      supervisor_id=r['supervisor_id'], objetivo_id=r['objetivo_id'], 
                      notas=r['notas'], fecha_operativa=r['fecha_operativa']) for r in rows]
        
        # Cachear solo si hay fecha específica
        if fecha:
            cache_global.set(cache_key, pasadas, 60)
        
        return pasadas

    def crear_pasada(self, pasada: Pasada) -> bool:
        """Crea una nueva pasada."""
        try:
            with gestor_db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pasadas (fecha, hora, turno, supervisor_id, objetivo_id, notas, fecha_operativa)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (pasada.fecha, pasada.hora, pasada.turno, pasada.supervisor_id,
                      pasada.objetivo_id, pasada.notas, pasada.fecha_operativa))
            return True
        except Exception as e:
            print(f"Error creando pasada: {e}")
            return False

    def sincronizar_datos(self) -> Dict[str, Any]:
        """Simulación de sincronización (para futuro con servidor)."""
        return {
            "estado": "local",
            "mensaje": "Datos locales, no hay servidor para sincronizar",
            "timestamp": None
        }
    
    # =========================================================================
    # Métodos de utilidad adicionales OPTIMIZADOS
    # =========================================================================
    
    def contar_pasadas(self, fecha: str, objetivo_id: int, turno: str = None) -> int:
        """Cuenta pasadas para un objetivo en una fecha y opcionalmente turno."""
        query = 'SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?'
        params = [fecha, objetivo_id]
        if turno:
            query += ' AND turno = ?'
            params.append(turno)
        return gestor_db.ejecutar_scalar(query, tuple(params))
    
    def obtener_estado_cobertura(self, fecha: str, objetivo_id: int) -> Dict[str, Any]:
        """Retorna el estado de cobertura para un objetivo."""
        # Usar una sola query en lugar de dos
        query = """
            SELECT 
                SUM(CASE WHEN turno = 'diurno' THEN 1 ELSE 0 END) as dia,
                SUM(CASE WHEN turno = 'nocturno' THEN 1 ELSE 0 END) as noche
            FROM pasadas 
            WHERE fecha = ? AND objetivo_id = ?
        """
        resultado = gestor_db.ejecutar(query, (fecha, objetivo_id))
        
        if resultado and resultado[0]:
            pasadas_dia = resultado[0]['dia'] or 0
            pasadas_noche = resultado[0]['noche'] or 0
        else:
            pasadas_dia = 0
            pasadas_noche = 0
        
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


# =============================================================================
# MÉTODOS DE PAGINACIÓN
# =============================================================================

    def get_objetivos_paginados(self, pagina: int = 1, por_pagina: int = 50) -> Dict[str, Any]:
        """
        Obtiene objetivos con paginación.
        Retorna: {items: [], total: int, pagina: int, total_paginas: int}
        """
        offset = (pagina - 1) * por_pagina
        
        # Obtener total
        total = gestor_db.ejecutar_scalar("SELECT COUNT(*) FROM objetivos")
        
        # Obtener página
        rows = gestor_db.ejecutar(
            "SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo FROM objetivos ORDER BY nombre LIMIT ? OFFSET ?",
            (por_pagina, offset)
        )
        
        objetivos = [Objetivo(id=r['id'], nombre=r['nombre'], descripcion=r['descripcion'],
                            fecha_inicio=r['fecha_inicio'], fecha_fin=r['fecha_fin'],
                            activo=bool(r['activo'])) for r in rows]
        
        return {
            'items': objetivos,
            'total': total or 0,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total or 0) // por_pagina + ((total or 0) % por_pagina > 0)
        }

    def get_supervisores_paginados(self, pagina: int = 1, por_pagina: int = 50) -> Dict[str, Any]:
        """Obtiene supervisores con paginación."""
        offset = (pagina - 1) * por_pagina
        
        total = gestor_db.ejecutar_scalar("SELECT COUNT(*) FROM supervisores")
        
        rows = gestor_db.ejecutar(
            "SELECT id, nombre, fecha_alta, fecha_baja FROM supervisores ORDER BY nombre LIMIT ? OFFSET ?",
            (por_pagina, offset)
        )
        
        supervisores = [Supervisor(id=r['id'], nombre=r['nombre'], activo=not r['fecha_baja']) for r in rows]
        
        return {
            'items': supervisores,
            'total': total or 0,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total or 0) // por_pagina + ((total or 0) % por_pagina > 0)
        }

    def get_pasadas_paginadas(self, pagina: int = 1, por_pagina: int = 100, fecha: str = None) -> Dict[str, Any]:
        """Obtiene pasadas con paginación."""
        offset = (pagina - 1) * por_pagina
        
        # Query base
        if fecha:
            count_query = "SELECT COUNT(*) FROM pasadas WHERE fecha = ?"
            data_query = "SELECT id, fecha, hora, turno, supervisor_id, objetivo_id, notas, fecha_operativa FROM pasadas WHERE fecha = ? ORDER BY fecha DESC, hora DESC LIMIT ? OFFSET ?"
            count_params = (fecha,)
            data_params = (fecha, por_pagina, offset)
        else:
            count_query = "SELECT COUNT(*) FROM pasadas"
            data_query = "SELECT id, fecha, hora, turno, supervisor_id, objetivo_id, notas, fecha_operativa FROM pasadas ORDER BY fecha DESC, hora DESC LIMIT ? OFFSET ?"
            count_params = ()
            data_params = (por_pagina, offset)
        
        total = gestor_db.ejecutar_scalar(count_query, count_params)
        rows = gestor_db.ejecutar(data_query, data_params)
        
        pasadas = [Pasada(id=r['id'], fecha=r['fecha'], hora=r['hora'], turno=r['turno'],
                         supervisor_id=r['supervisor_id'], objetivo_id=r['objetivo_id'],
                         notas=r['notas'], fecha_operativa=r['fecha_operativa']) for r in rows]
        
        return {
            'items': pasadas,
            'total': total or 0,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total or 0) // por_pagina + ((total or 0) % por_pagina > 0)
        }


# =============================================================================
# MÉTODOS DE BÚSQUEDA
# =============================================================================

    def buscar_objetivos(self, texto: str) -> List[Objetivo]:
        """Busca objetivos por nombre."""
        rows = gestor_db.ejecutar(
            "SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo FROM objetivos WHERE nombre LIKE ? LIMIT 20",
            (f"%{texto}%",)
        )
        return [Objetivo(id=r['id'], nombre=r['nombre'], descripcion=r['descripcion'],
                        fecha_inicio=r['fecha_inicio'], fecha_fin=r['fecha_fin'],
                        activo=bool(r['activo'])) for r in rows]

    def buscar_supervisores(self, texto: str) -> List[Supervisor]:
        """Busca supervisores por nombre."""
        rows = gestor_db.ejecutar(
            "SELECT id, nombre, activo FROM supervisores WHERE nombre LIKE ? LIMIT 20",
            (f"%{texto}%",)
        )
        return [Supervisor(id=r['id'], nombre=r['nombre'], activo=bool(r['activo'])) for r in rows]


# =============================================================================
# MÉTODOS DE ESTADÍSTICAS RÁPIDAS
# =============================================================================

    def get_resumen_rapido(self) -> Dict[str, Any]:
        """Obtiene un resumen rápido de la app en una sola query."""
        query = """
            SELECT 
                (SELECT COUNT(*) FROM objetivos) as total_objetivos,
                (SELECT COUNT(*) FROM supervisores WHERE fecha_baja IS NULL) as total_supervisores,
                (SELECT COUNT(*) FROM pasadas WHERE fecha = date('now')) as pasadas_hoy,
                (SELECT COUNT(*) FROM pasadas WHERE fecha >= date('now', '-7 days')) as pasadas_semana
        """
        resultado = gestor_db.ejecutar_dict(query, ())
        
        if resultado:
            return {
                'total_objetivos': resultado['total_objetivos'] or 0,
                'total_supervisores': resultado['total_supervisores'] or 0,
                'pasadas_hoy': resultado['pasadas_hoy'] or 0,
                'pasadas_semana': resultado['pasadas_semana'] or 0
            }
        return {'total_objetivos': 0, 'total_supervisores': 0, 'pasadas_hoy': 0, 'pasadas_semana': 0}
        
        if fecha:
            query += " AND p.fecha = ?"
            params.append(fecha)
        
        query += " ORDER BY p.fecha DESC, p.hora DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [Pasada(id=r[0], fecha=r[1], hora=r[2], turno=r[3],
                      supervisor_id=r[4], objetivo_id=r[5], notas=r[6],
                      fecha_operativa=r[7]) for r in rows]
    
    def get_estadisticas_dia(self, fecha: str) -> Dict[str, Any]:
        """Obtiene estadísticas agregadas del día."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total pasadas
        cursor.execute("SELECT COUNT(*) FROM pasadas WHERE fecha = ?", (fecha,))
        total_pasadas = cursor.fetchone()[0]
        
        # Pasadas por turno
        cursor.execute("""
            SELECT turno, COUNT(*) 
            FROM pasadas 
            WHERE fecha = ? 
            GROUP BY turno
        """, (fecha,))
        por_turno = dict(cursor.fetchall())
        
        # Objetivos cubiertos (tienen al menos una pasada)
        cursor.execute("""
            SELECT COUNT(DISTINCT objetivo_id) 
            FROM pasadas 
            WHERE fecha = ?
        """, (fecha,))
        objetivos_cubiertos = cursor.fetchone()[0]
        
        # Total objetivos activos
        cursor.execute("SELECT COUNT(*) FROM objetivos WHERE activo = 1")
        total_objetivos = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'fecha': fecha,
            'total_pasadas': total_pasadas,
            'pasadas_diurno': por_turno.get('diurno', 0),
            'pasadas_nocturno': por_turno.get('nocturno', 0),
            'objetivos_cubiertos': objetivos_cubiertos,
            'total_objetivos': total_objetivos,
            'porcentaje_cobertura': round((objetivos_cubiertos / total_objetivos) * 100, 1) if total_objetivos > 0 else 0
        }


class RemoteDataProvider(DataProvider):
    """Proveedor de datos remoto (para futuro con API)."""

    def __init__(self, api_url: str, token: str = None):
        self.api_url = api_url
        self.token = token

    def get_usuarios(self) -> List[Usuario]:
        # TODO: Implementar llamada a API
        return []

    def get_objetivos(self) -> List[Objetivo]:
        # TODO: Implementar llamada a API
        return []

    def get_supervisores(self) -> List[Supervisor]:
        # TODO: Implementar llamada a API
        return []

    def get_pasadas(self, fecha: str = None) -> List[Pasada]:
        # TODO: Implementar llamada a API
        return []

    def crear_pasada(self, pasada: Pasada) -> bool:
        # TODO: Implementar llamada a API
        return False

    def sincronizar_datos(self) -> Dict[str, Any]:
        # TODO: Implementar sincronización real
        return {
            "estado": "remoto",
            "mensaje": "Sincronización con servidor remoto",
            "timestamp": None
        }


# Instancia global del proveedor de datos
_data_provider: DataProvider = SQLiteDataProvider()


def get_data_provider() -> DataProvider:
    """Obtiene el proveedor de datos actual."""
    return _data_provider


def set_data_provider(provider: DataProvider) -> None:
    """Cambia el proveedor de datos (útil para testing o cambio a remoto)."""
    global _data_provider
    _data_provider = provider


def cambiar_a_modo_remoto(api_url: str, token: str = None) -> None:
    """Cambia a modo remoto cuando esté disponible el servidor."""
    set_data_provider(RemoteDataProvider(api_url, token))


def cambiar_a_modo_local() -> None:
    """Vuelve al modo local."""
    set_data_provider(SQLiteDataProvider())</content>
<parameter name="filePath">c:\Vesp taiu\sistema-control-objetivos\services\data_provider.py