from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class OverlayProgreso(QWidget):
    """Capa visual modal para tareas largas como el análisis de Excel."""

    def __init__(self, parent=None, mensaje: str = "Procesando archivo..."):
        super().__init__(parent)
        self.setObjectName("OverlayProgreso")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "#OverlayProgreso { background-color: rgba(8, 14, 35, 220); }"
            "#OverlayProgreso QLabel { color: #F4F7FB; font-size: 15px; font-weight: 600; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(14)
        self.etiqueta = QLabel(mensaje)
        self.etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barra = QProgressBar()
        self.barra.setRange(0, 0)
        layout.addWidget(self.etiqueta)
        layout.addWidget(self.barra)
        self.hide()

    def mostrar(self, mensaje: str = "Procesando archivo...") -> None:
        self.etiqueta.setText(mensaje)
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()

    def ocultar(self) -> None:
        self.hide()
