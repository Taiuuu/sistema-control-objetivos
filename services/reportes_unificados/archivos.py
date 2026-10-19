"""Persistencia segura de exportaciones de informes."""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Sequence

from services.permisos import tiene_permiso
from services.reportes_unificados.modelos import ReporteDatos

logger = logging.getLogger("vesp.reportes_unificados.archivos")
_CARACTERES_INVALIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitizar_nombre_archivo(nombre: str, extension: str, limite: int = 120) -> str:
    """Quita caracteres no admitidos y limita el nombre sin alterar su extensión."""
    extension_normalizada = extension.lower().lstrip(".")
    if extension_normalizada not in {"xlsx", "pdf"}:
        raise ValueError("El formato de exportación debe ser Excel o PDF")
    nombre_limpio = _CARACTERES_INVALIDOS.sub("_", str(nombre))
    nombre_limpio = re.sub(r"\s+", "_", nombre_limpio).strip(" ._")
    if not nombre_limpio:
        nombre_limpio = "reporte"
    sufijo = f".{extension_normalizada}"
    maximo_base = max(1, limite - len(sufijo))
    return f"{nombre_limpio[:maximo_base].rstrip(' ._') or 'reporte'}{sufijo}"


def nombre_sugerido(
    tipo: str,
    periodo: str,
    extension: str,
    ahora: datetime.datetime | None = None,
) -> str:
    """Forma un nombre reproducible y sanitizado para el período solicitado."""
    generado = ahora or datetime.datetime.now()
    tipo_limpio = _CARACTERES_INVALIDOS.sub("_", tipo).replace(" ", "_")
    periodo_limpio = _CARACTERES_INVALIDOS.sub("_", periodo).replace(" ", "")
    nombre = (
        f"VESP_{tipo_limpio}_{periodo_limpio}_"
        f"{generado:%Y%m%d-%H%M}"
    )
    return sanitizar_nombre_archivo(nombre, extension)


def mensaje_error_exportacion(error: Exception) -> str:
    """Traduce los fallos de escritura frecuentes a mensajes accionables."""
    if isinstance(error, FileExistsError):
        return "Ya existe un archivo con ese nombre. Elegí otro nombre para no sobrescribirlo."
    if isinstance(error, PermissionError):
        return (
            "No se pudo guardar el archivo. Puede estar abierto en Excel o en un "
            "visor; cerralo o elegí otro nombre."
        )
    if isinstance(error, OSError) and error.errno == 22:
        return "El nombre o la ruta del archivo no son válidos. Elegí otro nombre."
    return "No se pudo completar la exportación. Revisá el registro de errores."


def guardar_reporte(
    datos: ReporteDatos,
    ruta: str | Path,
    formato: str,
    columnas: Sequence[str] | None = None,
    contenido: str = "ambos",
    incluir_totales: bool = True,
    incluir_notas: bool = False,
) -> Path:
    """Escribe un archivo nuevo, sin reemplazar otro, y audita la exportación."""
    if not tiene_permiso("reportes.exportar"):
        raise PermissionError("No tiene permiso para exportar reportes.")
    if formato not in {"excel", "pdf"}:
        raise ValueError(f"Formato de exportación no reconocido: {formato}")
    filas = (
        datos.filas
        if contenido == "resumen"
        else datos.filas_detalle or datos.filas
        if contenido == "detalle"
        else (*datos.filas, *datos.filas_detalle)
    )
    if contenido not in {"resumen", "detalle", "ambos"}:
        raise ValueError(f"Contenido de informe no reconocido: {contenido}")
    if not filas:
        raise ValueError("No hay datos para el período y los filtros seleccionados.")

    destino = Path(ruta)
    extension_esperada = ".xlsx" if formato == "excel" else ".pdf"
    if destino.suffix.lower() != extension_esperada:
        raise ValueError(f"El archivo debe tener extensión {extension_esperada}")
    creado = False
    try:
        from core.logging_config import configurar_logging

        configurar_logging()
        destino.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            destino,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        creado = True
        os.close(descriptor)
        if formato == "excel":
            from services.reportes_unificados.excel import exportar_excel

            exportar_excel(
                datos, destino, columnas, contenido, incluir_totales, incluir_notas
            )
        else:
            from services.reportes_unificados.pdf import exportar_pdf

            exportar_pdf(
                datos, destino, columnas, contenido, incluir_totales, incluir_notas
            )
        _registrar_exportacion(datos, destino, formato, columnas, contenido)
        return destino
    except Exception as error:
        logger.exception("Falló la exportación del informe a %s", destino)
        if creado:
            try:
                destino.unlink(missing_ok=True)
            except OSError:
                logger.exception("No se pudo limpiar el archivo incompleto %s", destino)
        if isinstance(error, FileExistsError):
            raise FileExistsError(mensaje_error_exportacion(error)) from error
        if isinstance(error, PermissionError):
            raise PermissionError(mensaje_error_exportacion(error)) from error
        raise


def _registrar_exportacion(
    datos: ReporteDatos,
    ruta: Path,
    formato: str,
    columnas: Sequence[str] | None,
    contenido: str,
) -> None:
    """Guarda el evento de auditoría con filtros y destino realmente generado."""
    from database import db
    from services.sesion import get_usuario_id

    ahora = datetime.datetime.now()
    detalles = json.dumps(
        {
            "tipo_informe": datos.metadatos.tipo_informe,
            "titulo": datos.metadatos.titulo,
            "periodo": datos.metadatos.periodo,
            "filtros": dict(datos.metadatos.filtros_aplicados),
            "formato": formato,
            "contenido": contenido,
            "columnas": list(columnas) if columnas is not None else None,
            "archivo": str(ruta),
        },
        ensure_ascii=False,
        default=str,
    )
    with db.conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO auditoria (
                fecha, hora, usuario_id, tipo_operacion, tabla, detalles, estado
            ) VALUES (?, ?, ?, 'EXPORTACION', 'reportes', ?, 'EXITOSO')
            """,
            (
                ahora.strftime("%Y-%m-%d"),
                ahora.strftime("%H:%M:%S"),
                get_usuario_id(),
                detalles,
            ),
        )
