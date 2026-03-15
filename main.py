from PyQt6.QtWidgets import QApplication
from ui.ventana_principal import VentanaPrincipal
from database.db import crear_base_datos
import sys

crear_base_datos()

app = QApplication(sys.argv)
ventana = VentanaPrincipal()
ventana.show()
sys.exit(app.exec())