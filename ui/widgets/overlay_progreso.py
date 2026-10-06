from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget
from ui.theme.theme_manager import get_theme_manager


class OverlayProgreso(QWidget):
    """Capa visual modal para tareas largas como el análisis de Excel."""

    def __init__(self, parent=None, mensaje: str = "Procesando archivo..."):
        super().__init__(parent)
        self._theme_manager = get_theme_manager()
        self.setObjectName("OverlayProgreso")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(14)
        self.etiqueta = QLabel(mensaje)
        self.etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barra = QProgressBar()
        self.barra.setRange(0, 0)
        layout.addWidget(self.etiqueta)
        layout.addWidget(self.barra)
        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())
        self.hide()

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.setStyleSheet(f"""
            QWidget#OverlayProgreso {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {tokens['bg_gradient_start']},
                    stop: 1 {tokens['bg_gradient_end']}
                );
            }}
            QWidget#OverlayProgreso QLabel {{
                color: {tokens['text_primary']};
                font-size: {tokens['font_size_lg']};
                font-weight: 600;
            }}
        """)

    def mostrar(self, mensaje: str = "Procesando archivo...") -> None:
        self.etiqueta.setText(mensaje)
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()

    def ocultar(self) -> None:
        self.hide()
