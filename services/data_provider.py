# =============================================================================
# VESP Organizations - Capa de Abstracción de Datos
# Prepara el proyecto para multi-usuario y sincronización
# =============================================================================

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sqlite3
from database.db import DB_PATH


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
    """Proveedor de datos local con SQLite."""

    def get_usuarios(self) -> List[Usuario]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, rol, debe_cambiar_password FROM usuarios")
        rows = cursor.fetchall()
        conn.close()
        return [Usuario(id=r[0], username=r[1], rol=r[2], debe_cambiar_password=bool(r[3])) for r in rows]

    def get_objetivos(self) -> List[Objetivo]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, descripcion, fecha_inicio, fecha_fin, activo
            FROM objetivos WHERE activo = 1
        """)
        rows = cursor.fetchall()
        conn.close()
        return [Objetivo(id=r[0], nombre=r[1], descripcion=r[2], fecha_inicio=r[3],
                        fecha_fin=r[4], activo=bool(r[5])) for r in rows]

    def get_supervisores(self) -> List[Supervisor]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, activo FROM supervisores WHERE activo = 1")
        rows = cursor.fetchall()
        conn.close()
        return [Supervisor(id=r[0], nombre=r[1], activo=bool(r[2])) for r in rows]

    def get_pasadas(self, fecha: str = None) -> List[Pasada]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = """
            SELECT p.id, p.fecha, p.hora, p.turno, p.supervisor_id, p.objetivo_id, p.notas,
                   p.fecha_operativa
            FROM pasadas p
        """
        params = []

        if fecha:
            query += " WHERE p.fecha = ?"
            params.append(fecha)

        query += " ORDER BY p.fecha DESC, p.hora DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [Pasada(id=r[0], fecha=r[1], hora=r[2], turno=r[3],
                      supervisor_id=r[4], objetivo_id=r[5], notas=r[6],
                      fecha_operativa=r[7]) for r in rows]

    def crear_pasada(self, pasada: Pasada) -> bool:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pasadas (fecha, hora, turno, supervisor_id, objetivo_id, notas, fecha_operativa)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pasada.fecha, pasada.hora, pasada.turno, pasada.supervisor_id,
                  pasada.objetivo_id, pasada.notas, pasada.fecha_operativa))
            conn.commit()
            conn.close()
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
    # Métodos de utilidad adicionales
    # =========================================================================
    
    def contar_pasadas(self, fecha: str, objetivo_id: int, turno: str = None) -> int:
        """Cuenta pasadas para un objetivo en una fecha y opcionalmente turno."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = 'SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?'
        params = [fecha, objetivo_id]
        if turno:
            query += ' AND turno = ?'
            params.append(turno)
        cursor.execute(query, params)
        resultado = cursor.fetchone()[0]
        conn.close()
        return resultado
    
    def obtener_estado_cobertura(self, fecha: str, objetivo_id: int) -> Dict[str, Any]:
        """Retorna el estado de cobertura para un objetivo."""
        pasadas_dia = self.contar_pasadas(fecha, objetivo_id, turno="diurno")
        pasadas_noche = self.contar_pasadas(fecha, objetivo_id, turno="nocturno")
        
        if pasadas_dia > 0 and pasadas_noche > 0:
            estado = "completo"
        elif pasadas_dia > 0 or pasadas_noche > 0:
            estado = "parcial"
        else:
            estado = "sin_cobertura"
            
        return {
            'pasadas_dia': pasadas_dia,
            'pasadas_noche': pasadas_noche,
            'estado': estado,
            'objetivo_id': objetivo_id,
            'fecha': fecha
        }
    
    def get_pasadas_por_objetivo(self, objetivo_id: int, fecha: str = None) -> List[Pasada]:
        """Obtiene todas las pasadas de un objetivo específico."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = """
            SELECT p.id, p.fecha, p.hora, p.turno, p.supervisor_id, p.objetivo_id, p.notas,
                   p.fecha_operativa
            FROM pasadas p
            WHERE p.objetivo_id = ?
        """
        params = [objetivo_id]
        
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