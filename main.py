from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from ui.login import LoginWindow
from ui.ventana_principal import VentanaPrincipal
from database.db import crear_base_datos
from services.backup import hacer_backup
from services.actualizador import verificar_actualizacion
import sys


def aplicar_tema_oscuro(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(55, 55, 55))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(55, 55, 55))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 100, 100))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    app.setStyleSheet("""
        QWidget {
            font-family: Segoe UI;
            font-size: 13px;
        }
        QPushButton {
            background-color: #2a2a2a;
            color: #dcdcdc;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 5px 12px;
        }
        QPushButton:hover {
            background-color: #3a3a3a;
            border: 1px solid #2a82da;
        }
        QPushButton:pressed {
            background-color: #2a82da;
            color: white;
        }
        QTableWidget {
            gridline-color: #444;
            border: 1px solid #444;
        }
        QHeaderView::section {
            background-color: #2a2a2a;
            color: #dcdcdc;
            padding: 5px;
            border: 1px solid #444;
            font-weight: bold;
        }
        QComboBox {
            background-color: #2a2a2a;
            color: #dcdcdc;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 3px 8px;
        }
        QDateEdit {
            background-color: #2a2a2a;
            color: #dcdcdc;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 3px 8px;
        }
        QLineEdit {
            background-color: #2a2a2a;
            color: #dcdcdc;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 3px 8px;
        }
        QMessageBox {
            background-color: #1e1e1e;
            color: #dcdcdc;
        }
    """)


def iniciar_app():
    crear_base_datos()
    hacer_backup()

    app = QApplication(sys.argv)
    aplicar_tema_oscuro(app)

    def on_login_exitoso(usuario_id, rol):
        from services.sesion import iniciar_sesion
        from PyQt6.QtCore import QTimer
        iniciar_sesion(usuario_id, rol)
        global ventana_principal
        ventana_principal = VentanaPrincipal(usuario_id, rol, on_login_exitoso)
        ventana_principal.show()
        QTimer.singleShot(1000, lambda: verificar_actualizacion(ventana_principal))

    login = LoginWindow(on_login_exitoso)
    login.show()

    sys.exit(app.exec())


iniciar_app()
