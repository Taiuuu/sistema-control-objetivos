"""Backups SQLite verificados, restauración segura y retención."""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
import shutil
import sqlite3
from pathlib import Path

from core.configuracion import (
    BACKUP_DIR,
    DB_PATH,
    obtener_ruta_backup_externo,
    asegurar_directorios,
)
from database.db import configurar_conexion_sqlite
from services.exceptions import BackupError, NoHayEspacioBackup, BackupCorruptoError

logger = logging.getLogger("vesp.backup")
MOTIVOS_VALIDOS = {
    "diario", "pre_importacion", "pre_borrado_mes", "pre_restauracion", "manual"
}
TABLAS_PRINCIPALES = ("pasadas", "objetivos", "supervisores", "usuarios")
PATRON_BACKUP = re.compile(r"^vesp_(\d{8}_\d{6})_([a-z_]+?)(?:_\d+)?\.db$")


def _abrir_db(ruta: str | os.PathLike[str]) -> sqlite3.Connection:
    conexion = sqlite3.connect(str(ruta), timeout=5)
    configurar_conexion_sqlite(conexion)
    return conexion


def _integridad(ruta: Path) -> tuple[bool, str]:
    try:
        conexion = sqlite3.connect(str(ruta), timeout=5)
        try:
            salida = conexion.execute("PRAGMA integrity_check").fetchall()
            claves = conexion.execute("PRAGMA foreign_key_check").fetchall()
            if salida != [("ok",)]:
                return False, "; ".join(str(fila[0]) for fila in salida)
            if claves:
                return False, f"foreign_key_check encontró {len(claves)} referencia(s)"
            return True, "ok"
        finally:
            conexion.close()
    except sqlite3.DatabaseError as error:
        return False, str(error)


def _conteos(conexion: sqlite3.Connection) -> dict[str, int]:
    tablas = {
        fila[0] for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    return {
        tabla: int(conexion.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0])
        if tabla in tablas else 0
        for tabla in TABLAS_PRINCIPALES
    }


def verificar_backup(path: str | os.PathLike[str]) -> bool:
    """Comprueba una copia y descarta el archivo si está truncado o corrupto."""
    ruta = Path(path)
    valido, detalle = _integridad(ruta)
    if not valido:
        logger.error("Backup corrupto descartado ruta=%s detalle=%s", ruta, detalle)
        from database.db import cerrar_conexiones_de
        cerrar_conexiones_de(ruta)
        ruta.unlink(missing_ok=True)
    return valido


def _copiar_externo(origen: Path) -> None:
    ruta_externa = obtener_ruta_backup_externo()
    if not ruta_externa:
        return
    try:
        ruta_externa.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, ruta_externa / origen.name)
        logger.info("Copia externa creada: %s", ruta_externa / origen.name)
    except OSError:
        # La copia externa es secundaria: un fallo nunca invalida el backup local.
        logger.warning("No disponible la copia externa configurada: %s", ruta_externa,
                       exc_info=True)


def crear_backup(
    motivo: str,
    conexion_origen: sqlite3.Connection | None = None,
) -> Path:
    """Crea una copia mediante Connection.backup y la valida antes de aceptarla."""
    if motivo not in MOTIVOS_VALIDOS:
        raise ValueError(f"Motivo de backup no válido: {motivo}")
    asegurar_directorios()
    origen_path: Path | None = Path(DB_PATH)
    propia = conexion_origen is None
    if propia and not origen_path.exists():
        raise BackupError(f"No existe la base de datos: {origen_path}")
    if propia:
        conexion_origen = _abrir_db(origen_path)
    elif conexion_origen is not None:
        nombre_db = conexion_origen.execute("PRAGMA database_list").fetchone()[2]
        if nombre_db:
            origen_path = Path(nombre_db)
        else:
            origen_path = None
    assert conexion_origen is not None
    tamaño_base = origen_path.stat().st_size if origen_path and origen_path.exists() else (
        conexion_origen.execute("PRAGMA page_count").fetchone()[0]
        * conexion_origen.execute("PRAGMA page_size").fetchone()[0]
    )
    if origen_path:
        for sufijo in ("-wal", "-shm"):
            sidecar = Path(str(origen_path) + sufijo)
            if sidecar.exists():
                tamaño_base += sidecar.stat().st_size
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    espacio = shutil.disk_usage(BACKUP_DIR).free
    if espacio < tamaño_base * 2:
        mensaje = (
            f"Espacio insuficiente: se requieren al menos {tamaño_base * 2} bytes "
            f"libres para una copia segura; hay {espacio}."
        )
        logger.error(mensaje)
        if propia:
            conexion_origen.close()
        raise NoHayEspacioBackup(
            max(1, (tamaño_base * 2) // (1024 * 1024)),
            espacio // (1024 * 1024),
        )

    ahora = dt.datetime.now()
    destino = BACKUP_DIR / f"vesp_{ahora:%Y%m%d_%H%M%S}_{motivo}.db"
    indice = 1
    while destino.exists():
        destino = BACKUP_DIR / f"vesp_{ahora:%Y%m%d_%H%M%S}_{motivo}_{indice}.db"
        indice += 1

    conexion_destino = None
    try:
        original = _conteos(conexion_origen)
        conexion_destino = sqlite3.connect(str(destino))
        conexion_origen.backup(conexion_destino)
        conexion_destino.close()
        conexion_destino = None

        copiado = sqlite3.connect(str(destino))
        try:
            copiado_counts = _conteos(copiado)
        finally:
            copiado.close()
        es_integro, detalle = _integridad(destino)
        if not es_integro or copiado_counts != original:
            raise BackupCorruptoError(str(destino))
        tamaño = destino.stat().st_size
        logger.info(
            "Backup creado motivo=%s tamaño=%s verificado=sí ruta=%s",
            motivo, tamaño, destino,
        )
        _copiar_externo(destino)
        limpiar_backups()
        return destino
    except Exception as error:
        if conexion_destino is not None:
            conexion_destino.close()
        destino.unlink(missing_ok=True)
        logger.exception("Falló backup motivo=%s: %s", motivo, error)
        if isinstance(error, (BackupError, NoHayEspacioBackup, BackupCorruptoError)):
            raise
        raise BackupError(f"No se pudo crear el backup: {error}") from error
    finally:
        if propia:
            conexion_origen.close()


def listar_backups() -> list[dict]:
    """Lista las copias con su estado de verificación real."""
    asegurar_directorios()
    resultado = []
    for archivo in sorted(BACKUP_DIR.glob("vesp_*.db"), reverse=True):
        coincidencia = PATRON_BACKUP.match(archivo.name)
        if not coincidencia:
            continue
        try:
            fecha = dt.datetime.strptime(coincidencia.group(1), "%Y%m%d_%H%M%S")
            valido, detalle = _integridad(archivo)
            resultado.append({
                "path": archivo,
                "fecha": fecha,
                "motivo": coincidencia.group(2),
                "tamaño": archivo.stat().st_size,
                "verificado": valido,
                "detalle": detalle,
            })
        except OSError as error:
            logger.warning("No se pudo inspeccionar backup %s: %s", archivo, error)
    return resultado


def limpiar_backups(ahora: dt.datetime | None = None) -> None:
    """Aplica retención por tipo y nunca elimina la última copia verificada."""
    ahora = ahora or dt.datetime.now()
    existentes = [item for item in listar_backups() if item["verificado"]]
    if len(existentes) <= 1:
        return
    ultima = max(existentes, key=lambda item: item["fecha"])["path"]
    diarios = sorted(
        (item for item in existentes if item["motivo"] == "diario"),
        key=lambda item: item["fecha"],
        reverse=True,
    )
    preservar_diarios = {item["path"] for item in diarios[:14]}
    edades = {
        "pre_importacion": 90,
        "pre_borrado_mes": 90,
        "manual": 90,
        "pre_restauracion": 30,
    }
    for item in existentes:
        path = item["path"]
        if path == ultima or path in preservar_diarios:
            continue
        dias = (ahora - item["fecha"]).days
        vencido = (
            item["motivo"] == "diario"
            or dias > edades.get(item["motivo"], 90)
        )
        if vencido:
            try:
                path.unlink()
                logger.info("Backup vencido eliminado: %s", path)
            except OSError:
                logger.exception("No se pudo eliminar backup vencido: %s", path)


def hacer_backup() -> bool:
    """Compatibilidad con el arranque histórico: garantiza un backup diario."""
    hoy = dt.date.today()
    if any(item["motivo"] == "diario" and item["fecha"].date() == hoy
           and item["verificado"] for item in listar_backups()):
        return False
    crear_backup("diario")
    return True


def restaurar_backup(path: str | os.PathLike[str]) -> Path:
    """Verifica y reemplaza atómicamente la base, con copia previa recuperable."""
    elegido = Path(path).resolve()
    valido, detalle = _integridad(elegido)
    if not valido:
        raise BackupCorruptoError(f"{elegido}: {detalle}")
    ruta_base = Path(DB_PATH).resolve()
    temporal = ruta_base.with_name(f".{ruta_base.name}.restaurando")
    ruta_base.parent.mkdir(parents=True, exist_ok=True)
    integridad_actual, _ = _integridad(ruta_base) if ruta_base.exists() else (True, "ok")
    copia_previa: Path | None = None
    respaldo_dañado: Path | None = None
    if ruta_base.exists() and integridad_actual:
        copia_previa = crear_backup("pre_restauracion")
    elif not ruta_base.exists():
        logger.warning("Restauración sin base actual; no hay estado previo que respaldar")
    elif ruta_base.exists():
        # Una BD dañada no puede ser un backup verificado; se conserva como
        # evidencia aparte para poder recuperar el backup válido solicitado.
        respaldo_dañado = ruta_base.with_name(
            f"{ruta_base.name}.corrupta.{dt.datetime.now():%Y%m%d_%H%M%S}"
        )
        shutil.copy2(ruta_base, respaldo_dañado)
        for sufijo in ("-wal", "-shm"):
            sidecar = Path(str(ruta_base) + sufijo)
            if sidecar.exists():
                shutil.copy2(sidecar, Path(str(respaldo_dañado) + sufijo))
        logger.error(
            "Estado previo dañado; se conserva copia no verificada en %s",
            respaldo_dañado,
        )
    try:
        fuente = sqlite3.connect(str(elegido))
        destino = sqlite3.connect(str(temporal))
        try:
            fuente.backup(destino)
        finally:
            destino.close()
            fuente.close()
        valido, detalle = _integridad(temporal)
        if not valido:
            raise BackupCorruptoError(f"{temporal}: {detalle}")

        from database.gestor_db import gestor_db
        gestor_db.cerrar_conexion()
        from database.db import cerrar_todas_las_conexiones
        cerrar_todas_las_conexiones()
        for sufijo in ("-wal", "-shm"):
            Path(str(ruta_base) + sufijo).unlink(missing_ok=True)
        os.replace(temporal, ruta_base)
        valido, detalle = _integridad(ruta_base)
        if not valido:
            raise BackupCorruptoError(f"{ruta_base}: {detalle}")
        logger.info("Restauración completada desde %s; estado anterior=%s",
                    elegido, copia_previa or respaldo_dañado)
        return ruta_base
    except Exception as error:
        temporal.unlink(missing_ok=True)
        recuperacion = ruta_base.with_name(f".{ruta_base.name}.recuperando")
        try:
            recuperable = copia_previa or respaldo_dañado
            if recuperable is not None:
                for sufijo in ("-wal", "-shm"):
                    Path(str(ruta_base) + sufijo).unlink(missing_ok=True)
                shutil.copy2(recuperable, recuperacion)
                os.replace(recuperacion, ruta_base)
                if copia_previa is None and respaldo_dañado is not None:
                    for sufijo in ("-wal", "-shm"):
                        sidecar_respaldo = Path(str(respaldo_dañado) + sufijo)
                        if sidecar_respaldo.exists():
                            shutil.copy2(
                                sidecar_respaldo,
                                Path(str(ruta_base) + sufijo),
                            )
        except OSError:
            logger.critical("No se pudo restaurar la base previa desde %s",
                            copia_previa or respaldo_dañado, exc_info=True)
        logger.exception("Falló restauración de %s", elegido)
        raise BackupError(f"No se pudo restaurar el backup: {error}") from error


def obtener_informacion_backups() -> dict:
    """Adaptador compatible para las pantallas antiguas de estado de backups."""
    copias = listar_backups()
    return {
        "total_backups": len(copias),
        "espacio_usado": sum(item["tamaño"] for item in copias),
        "backups": [
            {"archivo": item["path"].name, "tamaño": item["tamaño"],
             "fecha": item["fecha"].isoformat(),
             "antigüedad_días": (dt.datetime.now() - item["fecha"]).days}
            for item in copias
        ],
        "último_backup": copias[0]["path"].name if copias else None,
        "metadata": {},
    }
