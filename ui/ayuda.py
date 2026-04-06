# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de ayuda con atajos de teclado disponibles
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from services.tema import obtener_tema_actual
from PyQt6.QtGui import QPixmap
from services.assets import ruta_asset


SHORTCUTS = [
    ("Ctrl + P", "Registrar pasada"),
    ("Ctrl + O", "Agregar objetivo"),
    ("Ctrl + S", "Agregar supervisor"),
    ("Ctrl + T", "Registrar turno"),
    ("Ctrl + N", "Notas del día"),
    ("Ctrl + R", "Reporte mensual"),
    ("Ctrl + B", "Actualizar tabla principal"),
    ("Ctrl + H", "Abrir esta ayuda"),
    ("Ctrl + =", "Aumentar zoom"),
    ("Ctrl + -", "Reducir zoom"),
    ("Ctrl + ←", "Día anterior"),
    ("Ctrl + →", "Día siguiente"),
]


class Ayuda(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ayuda - Atajos de teclado")
        self.setGeometry(300, 300, 500, 550)

        layout = QVBoxLayout()

        logo = QLabel()
        pixmap = QPixmap(ruta_asset("assets/vesp.png")).scaled(
            60, 60,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        titulo = QLabel("Atajos de teclado")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_color = "#4CAF50" if obtener_tema_actual() == "oscuro" else "#2E7D32"
        titulo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {titulo_color};")
        layout.addWidget(titulo)

        subtitulo = QLabel("Usá estos atajos para trabajar más rápido")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo_color = "#888" if obtener_tema_actual() == "oscuro" else "#666"
        subtitulo.setStyleSheet(f"font-size: 11px; color: {subtitulo_color};")
        layout.addWidget(subtitulo)

        tabla = QTableWidget()
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["Atajo", "Acción"])
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla.setColumnWidth(0, 120)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.setRowCount(len(SHORTCUTS))

        for i, (atajo, accion) in enumerate(SHORTCUTS):
            item_atajo = QTableWidgetItem(atajo)
            item_atajo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_atajo.setForeground(Qt.GlobalColor.green)
            tabla.setItem(i, 0, item_atajo)
            tabla.setItem(i, 1, QTableWidgetItem(accion))

        layout.addWidget(tabla)

        nota = QLabel("Tip: los atajos funcionan desde la ventana principal.")
        nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nota_color = "#666" if obtener_tema_actual() == "oscuro" else "#888"
        nota.setStyleSheet(f"font-size: 10px; color: {nota_color}; padding: 8px;")
        layout.addWidget(nota)

        self.setLayout(layout)