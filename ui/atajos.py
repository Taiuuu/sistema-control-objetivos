"""Registro común y catálogo de atajos de teclado de la aplicación."""

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)


ATAJOS = (
    ("Ctrl+P", "Registrar una pasada"),
    ("Ctrl+O", "Agregar un objetivo"),
    ("Ctrl+S", "Agregar un supervisor"),
    ("Ctrl+T", "Registrar un turno"),
    ("Ctrl+N", "Crear un registro en la pantalla actual"),
    ("Ctrl+R", "Abrir el reporte mensual"),
    ("Ctrl+F", "Enfocar el buscador de la pantalla actual"),
    ("Ctrl+E", "Exportar en pantallas con exportación"),
    ("F5", "Actualizar la pantalla actual"),
    ("Ctrl+1…9", "Abrir una de las primeras nueve opciones del menú"),
    ("Esc", "Limpiar la búsqueda o cerrar la ventana actual"),
    ("F1 / Ctrl+H", "Abrir la ayuda y los atajos"),
    ("Ctrl+B", "Actualizar el control diario"),
    ("Ctrl+=", "Aumentar el tamaño de letra"),
    ("Ctrl+-", "Reducir el tamaño de letra"),
    ("Ctrl+←", "Ir al día anterior"),
    ("Ctrl+→", "Ir al día siguiente"),
    ("Ctrl+\\", "Contraer o expandir el menú"),
    ("Ctrl+Enter", "Generar un reporte"),
)


def registrar_atajo(
    widget: QWidget,
    secuencia: str,
    accion: Callable[[], None],
    *,
    proteger_edicion: bool = True,
) -> QShortcut:
    """Registra un atajo que evita interferir con texto en edición."""
    atajo = QShortcut(QKeySequence(secuencia), widget)
    atajo.setContext(Qt.ShortcutContext.WindowShortcut)

    def ejecutar() -> None:
        foco = QApplication.focusWidget()
        if proteger_edicion and isinstance(
            foco, (QLineEdit, QTextEdit, QPlainTextEdit)
        ):
            return
        accion()

    atajo.activated.connect(ejecutar)
    return atajo


def escapar_o_limpiar_busqueda(widget: QWidget) -> None:
    """Limpia el buscador identificado o cierra la ventana actual."""
    buscador = next(
        (
            campo
            for campo in widget.findChildren(QLineEdit)
            if campo.property("search_field") is True
        ),
        None,
    )
    if buscador is not None and buscador.text():
        buscador.clear()
        return
    widget.close()


__all__ = ["ATAJOS", "escapar_o_limpiar_busqueda", "registrar_atajo"]
