# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla para exportar e importar la base de datos entre PCs
# =============================================================================

import os
import shutil
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from database.db import DB_PATH


# =============================================================================
# PANTALLA DE TRANSFERENCIA
# =============================================================================

class TransferirDatos(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transferir datos entre PCs")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Transferir datos entre PCs")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(titulo)

        # Descripción
        descripcion = QLabel(
            "Exportá la base de datos para llevarla a otra PC,\n"
            "o importá una base de datos de otra PC."
        )
        descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descripcion.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(descripcion)

        layout.addSpacing(20)

        # Exportar
        grupo_exportar = QVBoxLayout()
        label_exportar = QLabel("📤 Exportar datos")
        label_exportar.setStyleSheet("font-size: 13px; font-weight: bold;")
        grupo_exportar.addWidget(label_exportar)

        desc_exportar = QLabel("Guarda una copia de todos los datos del sistema en un archivo.")
        desc_exportar.setStyleSheet("color: #888; font-size: 11px;")
        grupo_exportar.addWidget(desc_exportar)

        boton_exportar = QPushButton("Exportar base de datos")
        boton_exportar.setFixedHeight(40)
        boton_exportar.clicked.connect(self._exportar)
        grupo_exportar.addWidget(boton_exportar)

        layout.addLayout(grupo_exportar)
        layout.addSpacing(20)

        # Importar
        grupo_importar = QVBoxLayout()
        label_importar = QLabel("📥 Importar datos")
        label_importar.setStyleSheet("font-size: 13px; font-weight: bold;")
        grupo_importar.addWidget(label_importar)

        desc_importar = QLabel(
            "⚠️ Reemplaza TODOS los datos actuales con los del archivo importado.\n"
            "Se hará un backup automático antes de importar."
        )
        desc_importar.setStyleSheet("color: #FFD700; font-size: 11px;")
        grupo_importar.addWidget(desc_importar)

        boton_importar = QPushButton("Importar base de datos")
        boton_importar.setFixedHeight(40)
        boton_importar.clicked.connect(self._importar)
        grupo_importar.addWidget(boton_importar)

        layout.addLayout(grupo_importar)
        layout.addSpacing(20)

        # Log de operaciones
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(80)
        self.log.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.log)

        self.setLayout(layout)

    def _exportar(self) -> None:
        """Exporta la base de datos a un archivo elegido por el usuario."""
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar base de datos",
            "VESP_datos.db",
            "Base de datos (*.db)"
        )
        if not ruta:
            return

        try:
            shutil.copy2(DB_PATH, ruta)
            self.log.append(f"✓ Datos exportados correctamente a: {ruta}")
            QMessageBox.information(self, "Listo", "Base de datos exportada correctamente.")
        except Exception as e:
            self.log.append(f"✗ Error al exportar: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {e}")

    def _importar(self) -> None:
        """Importa una base de datos reemplazando la actual, con backup previo."""
        confirmar = QMessageBox.question(
            self, "Confirmar importación",
            "⚠️ Esto reemplazará TODOS los datos actuales.\n"
            "Se hará un backup automático antes de continuar.\n\n"
            "¿Seguro que querés importar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar base de datos",
            "",
            "Base de datos (*.db)"
        )
        if not ruta:
            return

        try:
            # Verificar que el archivo es una base de datos válida
            conn = sqlite3.connect(ruta)
            tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            conn.close()

            tablas_requeridas = {"objetivos", "supervisores", "pasadas", "usuarios"}
            tablas_encontradas = {t[0] for t in tablas}

            if not tablas_requeridas.issubset(tablas_encontradas):
                QMessageBox.critical(
                    self, "Error",
                    "El archivo no es una base de datos válida del sistema VESP."
                )
                return

            # Backup antes de importar
            from services.backup import hacer_backup
            hacer_backup()
            self.log.append("✓ Backup realizado antes de importar.")

            # Reemplazar base de datos
            shutil.copy2(ruta, DB_PATH)
            self.log.append(f"✓ Datos importados correctamente desde: {ruta}")

            QMessageBox.information(
                self, "Listo",
                "Base de datos importada correctamente.\n"
                "Reiniciá el programa para que los cambios tomen efecto."
            )

        except Exception as e:
            self.log.append(f"✗ Error al importar: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo importar: {e}")