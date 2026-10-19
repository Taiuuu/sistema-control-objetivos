"""Flujo compartido del diálogo, selección de rutas y generación en segundo plano."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PyQt6.QtCore import QSettings, Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QDialog,
    QMessageBox,
    QProgressDialog,
)

from services.background_task import run_background_task
from services.reportes_unificados.archivos import (
    guardar_reporte,
    mensaje_error_exportacion,
    nombre_sugerido,
)
from services.reportes_unificados.modelos import ColumnaReporte, ReporteDatos
from ui.reportes.dialogo_exportar import DialogoExportar

_ULTIMA_CARPETA_KEY = "reportes/ultima_carpeta"


def mostrar_dialogo_exportar(
    parent,
    tipo_informe: str,
    fecha_inicio: date,
    fecha_fin: date,
    proveedor: Callable[[dict], ReporteDatos],
    columnas: Sequence[ColumnaReporte],
    filtros_iniciales: dict | None = None,
    objetivos: Iterable[tuple[int, str]] = (),
    supervisores: Iterable[tuple[int, str]] = (),
    equipos: Iterable[tuple[int, str]] = (),
    periodo_inicial: str | None = None,
    formato_inicial: str | None = None,
) -> None:
    """Abre el diálogo único y delega la escritura a un hilo de fondo."""
    try:
        dialogo = DialogoExportar(
            tipo_informe=tipo_informe,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            filtros_iniciales=filtros_iniciales,
            objetivos=objetivos,
            supervisores=supervisores,
            equipos=equipos,
            columnas=columnas,
            proveedor_vista_previa=proveedor,
            parent=parent,
        )
    except PermissionError as error:
        QMessageBox.warning(parent, "Permiso denegado", str(error))
        return

    if periodo_inicial is not None:
        indice = dialogo.selector_periodo.findData(periodo_inicial)
        if indice >= 0:
            dialogo.selector_periodo.setCurrentIndex(indice)
    if formato_inicial is not None:
        indice = dialogo.selector_formato.findData(formato_inicial)
        if indice >= 0:
            dialogo.selector_formato.setCurrentIndex(indice)
    if tipo_informe in {"detalle", "diario"}:
        for contenido in ("resumen", "ambos"):
            indice = dialogo.selector_contenido.findData(contenido)
            if indice >= 0:
                dialogo.selector_contenido.removeItem(indice)
        dialogo.selector_contenido.setCurrentIndex(
            dialogo.selector_contenido.findData("detalle")
        )
    elif tipo_informe == "objetivo":
        for contenido in ("detalle", "ambos"):
            indice = dialogo.selector_contenido.findData(contenido)
            if indice >= 0:
                dialogo.selector_contenido.removeItem(indice)
        for agrupacion in ("supervisor", "dia"):
            indice = dialogo.selector_agrupacion.findData(agrupacion)
            if indice >= 0:
                dialogo.selector_agrupacion.removeItem(indice)

    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return
    datos = dialogo.datos_previsualizados()
    if datos is None:
        QMessageBox.warning(
            parent, "Vista previa requerida", "Actualizá la vista previa antes de exportar."
        )
        return
    seleccion = dialogo.seleccion()
    destinos = _elegir_destinos(parent, datos, seleccion["formato"])
    if not destinos:
        return
    for destino, _ in destinos:
        if destino.exists():
            QMessageBox.warning(
                parent,
                "Archivo existente",
                "Ese archivo ya existe. Elegí otro nombre para no sobrescribirlo.",
            )
            return

    progreso = QProgressDialog(
        "Generando el informe…",
        "",
        0,
        0,
        parent,
    )
    progreso.setWindowTitle("Exportar")
    progreso.setWindowModality(Qt.WindowModality.WindowModal)
    progreso.setCancelButton(None)
    progreso.setMinimumDuration(0)
    progreso.show()
    tarea = run_background_task(
        _guardar_destinos,
        datos,
        destinos,
        seleccion,
    )
    tarea.signals.finished.connect(
        lambda rutas: _finalizar_exito(parent, progreso, rutas)
    )
    tarea.signals.error.connect(
        lambda mensaje: _finalizar_error(parent, progreso, mensaje)
    )


def _elegir_destinos(
    parent,
    datos: ReporteDatos,
    formato: str,
) -> list[tuple[Path, str]]:
    settings = QSettings("VESP Organizations", "Reportes")
    ultima_carpeta = Path(
        str(settings.value(_ULTIMA_CARPETA_KEY, str(Path.home())))
    )
    formatos = (
        (("excel", "xlsx"), ("pdf", "pdf"))
        if formato == "ambos"
        else (("excel", "xlsx"),)
        if formato == "excel"
        else (("pdf", "pdf"),)
    )
    if formato == "ambos":
        carpeta = QFileDialog.getExistingDirectory(
            parent,
            "Guardar los dos informes",
            str(ultima_carpeta),
        )
        if not carpeta:
            return []
        carpeta_elegida = Path(carpeta)
        settings.setValue(_ULTIMA_CARPETA_KEY, str(carpeta_elegida))
        return [
            (
                carpeta_elegida
                / nombre_sugerido(
                    datos.metadatos.tipo_informe,
                    datos.metadatos.periodo,
                    extension,
                    datos.metadatos.generado_en,
                ),
                tipo,
            )
            for tipo, extension in formatos
        ]

    tipo, extension = formatos[0]
    nombre = nombre_sugerido(
        datos.metadatos.tipo_informe,
        datos.metadatos.periodo,
        extension,
        datos.metadatos.generado_en,
    )
    ruta, _ = QFileDialog.getSaveFileName(
        parent,
        "Guardar informe",
        str(ultima_carpeta / nombre),
        "Excel (*.xlsx)" if extension == "xlsx" else "PDF (*.pdf)",
    )
    if not ruta:
        return []
    destino = Path(ruta)
    if not destino.suffix:
        destino = destino.with_suffix(f".{extension}")
    if destino.suffix.lower() != f".{extension}":
        QMessageBox.warning(
            parent,
            "Extensión inválida",
            f"Elegí un archivo con extensión .{extension}.",
        )
        return []
    settings.setValue(_ULTIMA_CARPETA_KEY, str(destino.parent))
    return [(destino, tipo)]


def _guardar_destinos(
    datos: ReporteDatos,
    destinos: Sequence[tuple[Path, str]],
    seleccion: dict,
) -> list[Path]:
    return [
        guardar_reporte(
            datos,
            ruta,
            formato,
            columnas=seleccion["columnas"],
            contenido=seleccion["contenido"],
            incluir_totales=seleccion["incluir_totales"],
            incluir_notas=seleccion["incluir_notas"],
        )
        for ruta, formato in destinos
    ]


def _finalizar_exito(parent, progreso: QProgressDialog, rutas: Sequence[Path]) -> None:
    progreso.close()
    mensaje = QMessageBox(parent)
    mensaje.setWindowTitle("Exportación completa")
    mensaje.setText("Los informes se guardaron correctamente.")
    mensaje.setIcon(QMessageBox.Icon.Information)
    boton_archivo = mensaje.addButton(
        "Abrir archivo", QMessageBox.ButtonRole.ActionRole
    )
    boton_carpeta = mensaje.addButton(
        "Abrir carpeta", QMessageBox.ButtonRole.ActionRole
    )
    mensaje.addButton(QMessageBox.StandardButton.Close)
    mensaje.exec()
    pulsado = mensaje.clickedButton()
    destino = rutas[0]
    if pulsado == boton_archivo:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(destino)))
    elif pulsado == boton_carpeta:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(destino.parent)))


def _finalizar_error(parent, progreso: QProgressDialog, detalle: str) -> None:
    progreso.close()
    texto = detalle.casefold()
    if "ya existe" in texto:
        error = FileExistsError(detalle)
    elif "permiso" in texto or "abierto en excel" in texto:
        error = PermissionError(detalle)
    elif "nombre" in texto and "válid" in texto:
        error = OSError(22, detalle)
    else:
        error = OSError(detalle)
    QMessageBox.critical(
        parent,
        "Error de exportación",
        mensaje_error_exportacion(error),
    )
