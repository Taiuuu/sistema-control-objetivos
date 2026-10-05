from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QColor

import pyqtgraph as pg
from ui.theme.theme_manager import get_theme_manager


class Sparkline(QWidget):
    """Gráfico compacto sin ejes para tendencias de cumplimiento."""

    def __init__(self, valores=None, parent=None):
        super().__init__(parent)
        self._theme_manager = get_theme_manager()
        self._values = valores or []
        self._plot = pg.PlotWidget()
        self._plot.setBackground(None)
        self._plot.hideAxis("left")
        self._plot.hideAxis("bottom")
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setMenuEnabled(False)
        self._plot.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        self.set_values(self._values)

    def _on_theme_changed(self, _theme_name: str) -> None:
        self.set_values(self._values)

    def set_values(self, valores):
        self._values = list(valores)
        self._plot.clear()
        if len(valores) < 2:
            return
        tokens = self._theme_manager.tokens()
        fill = QColor(tokens["accent"])
        fill.setAlpha(35)
        curva = self._plot.plot(
            list(range(len(valores))),
            valores,
            pen=pg.mkPen(tokens["accent"], width=2),
        )
        relleno = pg.FillBetweenItem(
            curva,
            self._plot.plot(
                list(range(len(valores))),
                [0] * len(valores),
                pen=None,
            ),
            brush=pg.mkBrush(fill),
        )
        self._plot.addItem(relleno)
        self._plot.setYRange(0, max(max(valores), 1), padding=0.2)
