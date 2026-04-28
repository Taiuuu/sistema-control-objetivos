# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de backup automático de la base de datos - VERSIÓN PROFESIONAL
# =============================================================================
"""
Módulo para la gestión de copias de seguridad de la base de datos.

Proporciona:
- Backups inteligentes (detecta cambios reales en BD)
- Prevención de duplicados mediante hash SHA256
- Retención automática de backups con límite configurable
- Metadatos de backup con timestamps y estadísticas
- Validación de integridad y limpieza automática

Características:
- Solo genera backup si hay cambios reales (evita escribir innecesariamente)
- Detecta cambios mediante mtime, size y hash SHA256
- Almacena metadata en JSON para auditoría
- Limpia automáticamente backups más antiguos que la retención

Autor: VESP Control de Objetivos
Versión: 2.0.0
"""

import os
import shutil
import logging
import datetime
import hashlib
import json
from typing import Dict, Optional, Tuple
from database.db import DB_PATH
from .exceptions import BackupError, NoHayEspacioBackup, BackupCorruptoError

# Configurar logger
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

BACKUP_DIR: str = os.path.join(os.path.expanduser("~"), "VESP Control", "backups")
BACKUP_METADATA: str = os.path.join(BACKUP_DIR, "backup_meta.json")
DIAS_RETENTION: int = 30
TAMAÑO_BLOQUE_HASH: int = 8192


# =============================================================================
# FUNCIONES PÚBLICAS
# =============================================================================

def hacer_backup() -> bool:
    """Crea copia de seguridad inteligente de la base de datos.
    
    Estrategia:
    1. Detecta cambios mediante mtime + size
    2. Valida que no es duplicado mediante hash SHA256
    3. Copia archivo solo si hay cambios reales
    4. Guarda metadata de backup
    5. Limpia backups antiguos automáticamente
    
    Returns:
        True si se creó un nuevo backup, False si no hubo cambios.
        
    Raises:
        BackupError: Si hay error accediendo a BD o creando backup.
        NoHayEspacioBackup: Si no hay espacio en disco para backup.
        
    Note:
        Evita backups duplicados detectando si el hash SHA256
        del archivo es idéntico al último backup.
        
    Example:
        >>> if hacer_backup():
        ...     print("Nuevo backup creado")
        ... else:
        ...     print("Sin cambios desde último backup")
    """
    try:
        # Validar que BD existe
        if not os.path.exists(DB_PATH):
            logger.warning(f"Base de datos no encontrada: {DB_PATH}")
            raise BackupError(f"Base de datos no encontrada: {DB_PATH}")
        
        # Crear directorio de backups si no existe
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Obtener metadatos actuales de BD
        metadata_actual = _leer_metadata()
        db_stat = os.stat(DB_PATH)
        mtime_actual = db_stat.st_mtime
        size_actual = db_stat.st_size
        
        # Optimización: si mtime y size no cambiaron, no hay cambios
        if metadata_actual:
            if (metadata_actual.get("db_mtime") == mtime_actual and
                metadata_actual.get("db_size") == size_actual):
                logger.debug("Sin cambios desde último backup (mtime/size idénticos)")
                return False
        
        # Calcular hash del archivo actual
        logger.debug(f"Calculando hash SHA256 de {DB_PATH}")
        hash_actual = _hash_archivo(DB_PATH)
        
        # Si hash es idéntico a último backup, actualizar metadata sin copiar
        if metadata_actual and metadata_actual.get("db_hash") == hash_actual:
            logger.info("Archivo sin cambios reales (hash idéntico), actualizando metadata")
            metadata_actual.update({
                "db_mtime": mtime_actual,
                "db_size": size_actual,
                "last_checked": datetime.datetime.now().isoformat()
            })
            _guardar_metadata(metadata_actual)
            return False
        
        # Crear nuevo backup
        logger.info(f"Detectados cambios en BD, creando backup")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destino = os.path.join(BACKUP_DIR, f"seguridad_{timestamp}.db")
        
        try:
            shutil.copy2(DB_PATH, destino)
        except OSError as e:
            if "space" in str(e).lower() or "disk full" in str(e).lower():
                logger.error(f"Sin espacio en disco para backup: {e}")
                raise NoHayEspacioBackup(f"Sin espacio para crear backup: {e}")
            raise
        
        logger.info(f"Backup creado exitosamente: {destino}")
        
        # Actualizar metadata
        nueva_metadata = {
            "last_backup": datetime.datetime.now().isoformat(),
            "last_backup_file": os.path.basename(destino),
            "db_hash": hash_actual,
            "db_mtime": mtime_actual,
            "db_size": size_actual,
            "backup_count": metadata_actual.get("backup_count", 0) + 1
        }
        _guardar_metadata(nueva_metadata)
        
        # Limpiar backups antiguos
        _limpiar_backups_antiguos()
        
        return True
        
    except (BackupError, NoHayEspacioBackup):
        raise
    except Exception as e:
        logger.error(f"Error inesperado en backup: {e}")
        raise BackupError(f"Error creando backup: {str(e)}")


def obtener_informacion_backups() -> Dict[str, any]:
    """Obtiene información y estadísticas de backups existentes.
    
    Returns:
        Diccionario con estructura:
        {
            'total_backups': int,
            'espacio_usado': int,
            'backups': [
                {
                    'archivo': str,
                    'tamaño': int,
                    'fecha': str,
                    'antigüedad_días': int
                }
            ],
            'último_backup': str,
            'metadata': dict
        }
        
    Example:
        >>> info = obtener_informacion_backups()
        >>> print(f"Total: {info['total_backups']} backups")
    """
    try:
        if not os.path.exists(BACKUP_DIR):
            return {
                'total_backups': 0,
                'espacio_usado': 0,
                'backups': [],
                'último_backup': None,
                'metadata': {}
            }
        
        metadata = _leer_metadata()
        backups = []
        espacio_usado = 0
        ahora = datetime.datetime.now()
        
        for archivo in sorted(os.listdir(BACKUP_DIR), reverse=True):
            ruta = os.path.join(BACKUP_DIR, archivo)
            
            # Saltar metadata y directorios
            if not os.path.isfile(ruta) or archivo == os.path.basename(BACKUP_METADATA):
                continue
            
            tamaño = os.path.getsize(ruta)
            espacio_usado += tamaño
            fecha_mod = datetime.datetime.fromtimestamp(os.path.getmtime(ruta))
            antigüedad = (ahora - fecha_mod).days
            
            backups.append({
                'archivo': archivo,
                'tamaño': tamaño,
                'fecha': fecha_mod.isoformat(),
                'antigüedad_días': antigüedad
            })
        
        return {
            'total_backups': len(backups),
            'espacio_usado': espacio_usado,
            'backups': backups,
            'último_backup': metadata.get('last_backup_file'),
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo información de backups: {e}")
        return {
            'total_backups': 0,
            'espacio_usado': 0,
            'backups': [],
            'último_backup': None,
            'metadata': {},
            'error': str(e)
        }


def validar_integridad_backup(archivo_backup: str) -> Tuple[bool, str]:
    """Valida integridad de un archivo de backup.
    
    Args:
        archivo_backup: Nombre o ruta del archivo de backup.
    
    Returns:
        Tupla (es_válido, mensaje).
        
    Raises:
        BackupCorruptoError: Si el archivo parece estar corrupto.
        
    Example:
        >>> válido, msg = validar_integridad_backup("seguridad_2026-04-27_10-30.db")
    """
    try:
        # Obtener ruta completa si solo se proporciona nombre
        if os.path.dirname(archivo_backup) == "":
            ruta = os.path.join(BACKUP_DIR, archivo_backup)
        else:
            ruta = archivo_backup
        
        # Verificar existencia
        if not os.path.exists(ruta):
            raise BackupCorruptoError(f"Archivo no encontrado: {ruta}")
        
        # Verificar que es archivo (no directorio)
        if not os.path.isfile(ruta):
            raise BackupCorruptoError(f"No es archivo: {ruta}")
        
        # Verificar tamaño mínimo (debe tener estructura de BD SQLite)
        tamaño = os.path.getsize(ruta)
        if tamaño < 4096:  # SQLite página mínima
            raise BackupCorruptoError(
                f"Archivo demasiado pequeño ({tamaño} bytes), probablemente corrupto"
            )
        
        # Verificar magic number de SQLite (primeros 16 bytes)
        with open(ruta, "rb") as f:
            header = f.read(16)
        
        if not header.startswith(b"SQLite format 3"):
            raise BackupCorruptoError(
                "Header de SQLite inválido, archivo probablemente corrupto"
            )
        
        logger.info(f"Backup validado exitosamente: {archivo_backup}")
        return (True, "Backup íntegro y válido")
        
    except BackupCorruptoError:
        raise
    except Exception as e:
        logger.error(f"Error validando backup {archivo_backup}: {e}")
        raise BackupCorruptoError(f"Error validando backup: {str(e)}")


# =============================================================================
# FUNCIONES PRIVADAS
# =============================================================================

def _hash_archivo(ruta: str) -> str:
    """Calcula hash SHA256 del archivo mediante lectura en bloques.
    
    Args:
        ruta: Ruta del archivo.
    
    Returns:
        Hash SHA256 en formato hexadecimal.
        
    Raises:
        IOError: Si no se puede leer el archivo.
    """
    try:
        hash_sha256 = hashlib.sha256()
        with open(ruta, "rb") as archivo:
            for bloque in iter(lambda: archivo.read(TAMAÑO_BLOQUE_HASH), b""):
                hash_sha256.update(bloque)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculando hash de {ruta}: {e}")
        raise


def _leer_metadata() -> Dict[str, any]:
    """Lee metadata de backup desde JSON.
    
    Returns:
        Diccionario con metadatos de último backup.
    """
    if not os.path.exists(BACKUP_METADATA):
        logger.debug("No existe archivo de metadata")
        return {}
    
    try:
        with open(BACKUP_METADATA, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
            logger.debug(f"Metadata leída: {len(data)} campos")
            return data
    except json.JSONDecodeError:
        logger.warning("Metadata corrupta, iniciando nueva")
        return {}
    except Exception as e:
        logger.error(f"Error leyendo metadata: {e}")
        return {}


def _guardar_metadata(metadata: Dict[str, any]) -> None:
    """Guarda metadata de backup en JSON.
    
    Args:
        metadata: Diccionario con metadatos a guardar.
    """
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(BACKUP_METADATA, "w", encoding="utf-8") as archivo:
            json.dump(metadata, archivo, indent=2, ensure_ascii=False)
        logger.debug(f"Metadata guardada con {len(metadata)} campos")
    except Exception as e:
        logger.error(f"Error guardando metadata de backup: {e}")


def _limpiar_backups_antiguos() -> None:
    """Elimina backups que superan el límite de retención configurado.
    
    Mantiene automáticamente solo los últimos DIAS_RETENTION días de backups.
    """
    if not os.path.exists(BACKUP_DIR):
        return
    
    ahora = datetime.datetime.now()
    backups_eliminados = 0
    
    for archivo in os.listdir(BACKUP_DIR):
        ruta = os.path.join(BACKUP_DIR, archivo)
        
        # Saltar si no es archivo o es metadata
        if not os.path.isfile(ruta) or archivo == os.path.basename(BACKUP_METADATA):
            continue
        
        # Calcular antigüedad
        fecha_modificacion = datetime.datetime.fromtimestamp(os.path.getmtime(ruta))
        dias_diferencia = (ahora - fecha_modificacion).days
        
        # Eliminar si supera retención
        if dias_diferencia > DIAS_RETENTION:
            try:
                os.remove(ruta)
                logger.info(f"Backup antiguo eliminado ({dias_diferencia} días): {archivo}")
                backups_eliminados += 1
            except Exception as e:
                logger.error(f"Error eliminando backup antiguo {archivo}: {e}")
    
    if backups_eliminados > 0:
        logger.info(f"Limpieza completada: {backups_eliminados} backups eliminados")