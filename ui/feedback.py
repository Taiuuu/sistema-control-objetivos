"""Mensajes de error claros para la persona usuaria y detalles para el log."""

import logging

from PyQt6.QtWidgets import QWidget, QMessageBox


_logger = logging.getLogger(__name__)


def mostrar_error_usuario(
    parent: QWidget | None,
    titulo: str,
    mensaje: str,
    detalle: Exception | str,
) -> None:
    """Evita mostrar detalles técnicos y los conserva en el registro de la app."""
    if isinstance(detalle, Exception):
        _logger.error(
            "%s: %s",
            titulo,
            detalle,
            exc_info=(type(detalle), detalle, detalle.__traceback__),
        )
    else:
        _logger.error("%s: %s", titulo, detalle)
    QMessageBox.critical(parent, titulo, mensaje)
