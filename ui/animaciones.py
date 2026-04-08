# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de animaciones de interfaz
# =============================================================================

from PyQt6.QtCore import (
    QParallelAnimationGroup, QPropertyAnimation,
    QEasingCurve, QPoint
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect

_active_animations = []


def _guardar_animacion(animacion):
    _active_animations.append(animacion)
    animacion.finished.connect(lambda: _active_animations.remove(animacion))


def animar_aparecer(widget: QWidget, duracion: int = 300) -> None:
    """Anima la aparición de un widget con efecto fade in."""
    efecto = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(efecto)
    animacion = QPropertyAnimation(efecto, b"opacity", widget)
    animacion.setDuration(duracion)
    animacion.setStartValue(0.0)
    animacion.setEndValue(1.0)
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    _guardar_animacion(animacion)
    animacion.start()


def animar_deslizar(widget: QWidget, desde: QPoint, hasta: QPoint, duracion: int = 350) -> None:
    """Anima el movimiento de un widget de una posición a otra."""
    animacion = QPropertyAnimation(widget, b"pos", widget)
    animacion.setDuration(duracion)
    animacion.setStartValue(desde)
    animacion.setEndValue(hasta)
    animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
    _guardar_animacion(animacion)
    animacion.start()


def animar_entrada(widget: QWidget, duracion: int = 350, offset_y: int = 40) -> None:
    """Aplica una animación suave de entrada con fade in y deslizado desde abajo."""
    original_pos = widget.pos()
    widget.move(original_pos + QPoint(0, offset_y))

    efecto = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(efecto)

    animacion_opacidad = QPropertyAnimation(efecto, b"opacity", widget)
    animacion_opacidad.setDuration(duracion)
    animacion_opacidad.setStartValue(0.0)
    animacion_opacidad.setEndValue(1.0)
    animacion_opacidad.setEasingCurve(QEasingCurve.Type.OutCubic)

    animacion_pos = QPropertyAnimation(widget, b"pos", widget)
    animacion_pos.setDuration(duracion)
    animacion_pos.setStartValue(widget.pos())
    animacion_pos.setEndValue(original_pos)
    animacion_pos.setEasingCurve(QEasingCurve.Type.OutCubic)

    grupo = QParallelAnimationGroup(widget)
    grupo.addAnimation(animacion_opacidad)
    grupo.addAnimation(animacion_pos)

    _guardar_animacion(grupo)
    grupo.start()


def animar_tabla(tabla, duracion: int = 200) -> None:
    """Aplica fade in a una tabla al cargar datos."""
    animar_aparecer(tabla, duracion)