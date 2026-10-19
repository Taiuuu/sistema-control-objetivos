"""Carga progresiva de filas para mantener disponible el bucle de eventos."""

from collections.abc import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QTableWidget


def cargar_tabla_en_lotes(
    tabla: QTableWidget,
    cantidad: int,
    poblar_fila: Callable[[int], None],
    al_terminar: Callable[[], None],
    *,
    tamano_lote: int = 100,
) -> QTimer:
    """Puebla una tabla por lotes cortos y permite pintar entre cada uno."""
    tabla.setRowCount(cantidad)
    timer = QTimer(tabla)
    timer.setSingleShot(True)
    siguiente_fila = 0

    def procesar_lote() -> None:
        nonlocal siguiente_fila
        fin = min(siguiente_fila + tamano_lote, cantidad)
        tabla.setUpdatesEnabled(False)
        try:
            for fila in range(siguiente_fila, fin):
                poblar_fila(fila)
        finally:
            tabla.setUpdatesEnabled(True)
        siguiente_fila = fin
        if siguiente_fila < cantidad:
            timer.start(0)
        else:
            timer.deleteLater()
            al_terminar()

    timer.timeout.connect(procesar_lote)
    timer.start(0)
    return timer
