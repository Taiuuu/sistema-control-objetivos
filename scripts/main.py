# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Archivo principal de entrada de la aplicación
# =============================================================================

import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QTimer

from ui.login import LoginWindow
from ui.ventana_principal import VentanaPrincipal
from database.db import crear_base_datos, migrar_supervisor3, migrar_supervisores_alta_baja
from services.backup import hacer_backup
from services.actualizador import verificar_actualizacion
from services.tema import obtener_tema_actual, establecer_tema_actual
from services.api_rest import iniciar_api_rest


def aplicar_tema_oscuro(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base,            QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(55, 55, 55))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text,            QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button,          QColor(55, 55, 55))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor(255, 100, 100))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    app.setStyleSheet("""
        QWidget { font-family: Segoe UI; font-size: 13px; }
        QPushButton {
            background-color: #2a2a2a; color: #dcdcdc;
            border: 1px solid #555; border-radius: 4px; padding: 5px 12px;
        }
        QPushButton:hover { background-color: #3a3a3a; border: 1px solid #2a82da; }
        QPushButton:pressed { background-color: #2a82da; color: white; }
        QTableWidget { gridline-color: #444; border: 1px solid #444; }
        QHeaderView::section {
            background-color: #2a2a2a; color: #dcdcdc;
            padding: 5px; border: 1px solid #444; font-weight: bold;
        }
        QComboBox, QDateEdit, QLineEdit {
            background-color: #2a2a2a; color: #dcdcdc;
            border: 1px solid #555; border-radius: 4px; padding: 3px 8px;
        }
        QMessageBox { background-color: #1e1e1e; color: #dcdcdc; }
        QScrollBar:vertical { background: #2a2a2a; width: 8px; border-radius: 4px; }
        QScrollBar::handle:vertical { background: #555; border-radius: 4px; }
        QScrollBar::handle:vertical:hover { background: #2a82da; }
        QScrollBar:horizontal { background: #2a2a2a; height: 8px; border-radius: 4px; }
        QScrollBar::handle:horizontal { background: #555; border-radius: 4px; }
    """)


def aplicar_tema_claro(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.Base,            QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(235, 235, 235))
    palette.setColor(QPalette.ColorRole.Text,            QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.Button,          QColor(225, 225, 225))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor(255, 0, 0))
    app.setPalette(palette)
    for widget in app.allWidgets():
        widget.update()
        widget.repaint()
    app.setStyleSheet("""
        QWidget { font-family: Segoe UI; font-size: 13px; }
        QPushButton {
            background-color: #e0e0e0; color: #1e1e1e;
            border: 1px solid #bbb; border-radius: 4px; padding: 5px 12px;
        }
        QPushButton:hover { background-color: #d0d0d0; border: 1px solid #2a82da; }
        QPushButton:pressed { background-color: #2a82da; color: white; }
        QTableWidget {
            gridline-color: #ccc; border: 1px solid #ccc;
            background-color: white; alternate-background-color: #f9f9f9;
        }
        QHeaderView::section {
            background-color: #e0e0e0; color: #1e1e1e;
            padding: 5px; border: 1px solid #ccc; font-weight: bold;
        }
        QFrame { background-color: #f0f0f0; }
        QScrollBar:vertical { background: #e0e0e0; width: 8px; border-radius: 4px; }
        QScrollBar::handle:vertical { background: #aaa; border-radius: 4px; }
        QScrollBar::handle:vertical:hover { background: #2a82da; }
        QComboBox, QDateEdit, QLineEdit {
            background-color: #f5f5f5; color: #1e1e1e;
            border: 1px solid #ccc; border-radius: 4px; padding: 3px 8px;
        }
        QMessageBox { background-color: #f5f5f5; color: #1e1e1e; }
        QScrollBar:horizontal { background: #e0e0e0; height: 8px; border-radius: 4px; }
        QScrollBar::handle:horizontal { background: #aaa; border-radius: 4px; }
    """)


def alternar_tema(app: QApplication, ventana) -> None:
    if obtener_tema_actual() == "oscuro":
        aplicar_tema_claro(app)
        establecer_tema_actual("claro")
        ventana.btn_tema.setText("🌙 Modo oscuro")
    else:
        aplicar_tema_oscuro(app)
        establecer_tema_actual("oscuro")
        ventana.btn_tema.setText("☀ Modo claro")


def iniciar_app() -> None:
    crear_base_datos()
    migrar_supervisor3()
    migrar_supervisores_alta_baja()
    hacer_backup()
    iniciar_api_rest()

    app = QApplication(sys.argv)
    aplicar_tema_oscuro(app)

    ventana_principal = None

    def on_login_exitoso(usuario_id: int, rol: str) -> None:
        from services.sesion import iniciar_sesion
        iniciar_sesion(usuario_id, rol)
        nonlocal ventana_principal
        ventana_principal = VentanaPrincipal(usuario_id, rol, on_login_exitoso, app, alternar_tema)
        ventana_principal.show()
        QTimer.singleShot(1000, lambda: verificar_actualizacion(ventana_principal))

    login = LoginWindow(on_login_exitoso)
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    iniciar_app()