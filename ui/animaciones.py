# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de animaciones de interfaz
# =============================================================================

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


def animar_aparecer(widget: QWidget, duracion: int = 300) -> None:
    """Anima la aparición de un widget con efecto fade in."""
    efecto = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(efecto)
    animacion = QPropertyAnimation(efecto, b"opacity", widget)
    animacion.setDuration(duracion)
    animacion.setStartValue(0.0)
    animacion.setEndValue(1.0)
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    animacion.start()


def animar_deslizar(widget: QWidget, desde: QPoint, hasta: QPoint, duracion: int = 350) -> None:
    """Anima el movimiento de un widget de una posición a otra."""
    animacion = QPropertyAnimation(widget, b"pos", widget)
    animacion.setDuration(duracion)
    animacion.setStartValue(desde)
    animacion.setEndValue(hasta)
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    animacion.start()


def animar_tabla(tabla, duracion: int = 200) -> None:
    """Aplica fade in a una tabla al cargar datos."""
    animar_aparecer(tabla, duracion)