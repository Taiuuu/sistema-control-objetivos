from PyQt6.QtWidgets import QWidget, QVBoxLayout

import pyqtgraph as pg


class Sparkline(QWidget):
    """Gráfico compacto sin ejes para tendencias de cumplimiento."""

    def __init__(self, valores=None, parent=None):
        super().__init__(parent)
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
        self.set_values(valores or [])

    def set_values(self, valores):
        self._plot.clear()
        if len(valores) < 2:
            return
        curva = self._plot.plot(
            list(range(len(valores))),
            valores,
            pen=pg.mkPen("#63E6BE", width=2),
        )
        relleno = pg.FillBetweenItem(
            curva,
            self._plot.plot(
                list(range(len(valores))),
                [0] * len(valores),
                pen=None,
            ),
            brush=pg.mkBrush(99, 230, 190, 35),
        )
        self._plot.addItem(relleno)
        self._plot.setYRange(0, max(max(valores), 1), padding=0.2)
