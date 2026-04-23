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
    def crear_pasada(self, pasada: Pasada) -> bool:
        pass

    @abstractmethod
    def sincronizar_datos(self) -> Dict[str, Any]:
        """Sincronizar con servidor remoto (para futuro)."""
        pass


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