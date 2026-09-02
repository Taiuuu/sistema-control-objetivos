from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class DialogoMensaje(QDialog):
    """Dialogo de mensaje coherente con el tema global de la aplicación."""

    def __init__(self, titulo: str, mensaje: str, tipo: str = "info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setObjectName("DialogoMensaje")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(16)
        icono = {"error": "!", "warning": "!", "success": "OK"}.get(tipo, "i")
        etiqueta_icono = QLabel(icono)
        etiqueta_icono.setObjectName("DialogIcon")
        etiqueta_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiqueta_icono.setFixedSize(40, 40)
        etiqueta = QLabel(mensaje)
        etiqueta.setWordWrap(True)
        etiqueta.setObjectName("DialogMessage")
        layout.addWidget(etiqueta_icono, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(etiqueta)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        botones.accepted.connect(self.accept)
        layout.addWidget(botones)


def mostrar_mensaje(parent, titulo: str, mensaje: str, tipo: str = "info") -> int:
    return DialogoMensaje(titulo, mensaje, tipo, parent).exec()


def confirmar_mensaje(parent, titulo: str, mensaje: str) -> bool:
    dialogo = QDialog(parent)
    dialogo.setWindowTitle(titulo)
    dialogo.setObjectName("DialogoMensaje")
    layout = QVBoxLayout(dialogo)
    layout.setContentsMargins(24, 22, 24, 18)
    etiqueta = QLabel(mensaje)
    etiqueta.setWordWrap(True)
    layout.addWidget(etiqueta)
    botones = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
    )
    botones.accepted.connect(dialogo.accept)
    botones.rejected.connect(dialogo.reject)
    layout.addWidget(botones)
    return dialogo.exec() == QDialog.DialogCode.Accepted
