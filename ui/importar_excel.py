# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla para importar datos desde Excel existente
# =============================================================================

import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QTextEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt
from database.db import DB_PATH
from openpyxl import load_workbook


# =============================================================================
# IMPORTACIÓN
# =============================================================================

def _obtener_o_crear_objetivo(cursor, nombre: str) -> int:
    """Busca un objetivo por nombre o lo crea si no existe. Retorna su ID."""
    cursor.execute("SELECT id FROM objetivos WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]

    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO objetivos (nombre, fecha_inicio, dias_semana)
        VALUES (?, ?, ?)
    """, (nombre, hoy, "1,2,3,4,5,6,7"))
    return cursor.lastrowid


def _obtener_o_crear_supervisor(cursor, nombre: str) -> int:
    """Busca un supervisor por nombre o lo crea si no existe. Retorna su ID."""
    if not nombre or nombre.strip() == "":
        return None

    cursor.execute("SELECT id FROM supervisores WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]

    cursor.execute("INSERT INTO supervisores (nombre) VALUES (?)", (nombre,))
    return cursor.lastrowid


def importar_desde_excel(ruta: str, col_objetivo: int, col_turno: int,
                          col_supervisor: int, col_veces: int,
                          col_fecha: int, fila_inicio: int) -> tuple:
    """
    Importa pasadas desde un archivo Excel.
    Retorna (pasadas_importadas, errores).
    """
    wb = load_workbook(ruta)
    ws = wb.active

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    pasadas_importadas = 0
    errores = []

    for fila_num, fila in enumerate(ws.iter_rows(min_row=fila_inicio, values_only=True), fila_inicio):
        try:
            if not fila or all(v is None for v in fila):
                continue

            # Obtener valores de las columnas configuradas
            objetivo_nombre = str(fila[col_objetivo - 1]).strip() if fila[col_objetivo - 1] else None
            turno_raw = str(fila[col_turno - 1]).strip().lower() if fila[col_turno - 1] else None
            supervisor_nombre = str(fila[col_supervisor - 1]).strip() if col_supervisor and fila[col_supervisor - 1] else ""
            veces = int(fila[col_veces - 1]) if fila[col_veces - 1] else 0
            fecha_raw = fila[col_fecha - 1] if col_fecha and fila[col_fecha - 1] else None

            if not objetivo_nombre or objetivo_nombre.lower() in ("none", "objetivo", ""):
                continue

            if veces == 0:
                continue

            # Normalizar turno
            if turno_raw in ("diurno", "dia", "d", "day"):
                turno = "diurno"
            elif turno_raw in ("nocturno", "noche", "n", "night"):
                turno = "nocturno"
            else:
                turno = "diurno"

            # Normalizar fecha
            if isinstance(fecha_raw, datetime.datetime):
                fecha = fecha_raw.strftime("%Y-%m-%d")
            elif isinstance(fecha_raw, str):
                try:
                    fecha = datetime.datetime.strptime(fecha_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                except Exception:
                    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            else:
                fecha = datetime.datetime.now().strftime("%Y-%m-%d")

            objetivo_id = _obtener_o_crear_objetivo(cursor, objetivo_nombre)
            supervisor_id = _obtener_o_crear_supervisor(cursor, supervisor_nombre)

            # Registrar la cantidad de veces que se pasó
            for _ in range(veces):
                cursor.execute("""
                    INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (fecha, "00:00", turno, objetivo_id, supervisor_id))

            pasadas_importadas += veces

        except Exception as e:
            errores.append(f"Fila {fila_num}: {e}")

    conexion.commit()
    conexion.close()

    return pasadas_importadas, errores


# =============================================================================
# PANTALLA DE IMPORTACIÓN
# =============================================================================

class ImportarExcel(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Importar desde Excel")
        self.setGeometry(200, 200, 600, 550)
        self.ruta_archivo = None

        layout = QVBoxLayout()

        titulo = QLabel("Importar datos desde Excel")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(titulo)

        desc = QLabel(
            "Seleccioná el archivo Excel e indicá en qué columna está cada dato.\n"
            "Las columnas se numeran desde 1 (A=1, B=2, C=3...)"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(desc)

        layout.addSpacing(10)

        # Selector de archivo
        fila_archivo = QHBoxLayout()
        self.label_archivo = QLabel("Ningún archivo seleccionado")
        self.label_archivo.setStyleSheet("color: #888;")
        boton_archivo = QPushButton("Seleccionar Excel")
        boton_archivo.clicked.connect(self._seleccionar_archivo)
        fila_archivo.addWidget(self.label_archivo)
        fila_archivo.addWidget(boton_archivo)
        layout.addLayout(fila_archivo)

        layout.addSpacing(10)

        # Configuración de columnas
        layout.addWidget(QLabel("Configuración de columnas:"))

        grid = QHBoxLayout()

        col_layout = QVBoxLayout()
        col_layout.addWidget(QLabel("Columna Objetivo:"))
        self.col_objetivo = QComboBox()
        self.col_objetivo.addItems([str(i) for i in range(1, 21)])
        self.col_objetivo.setCurrentIndex(3)  # D por defecto
        col_layout.addWidget(self.col_objetivo)
        grid.addLayout(col_layout)

        col_layout2 = QVBoxLayout()
        col_layout2.addWidget(QLabel("Columna Turno:"))
        self.col_turno = QComboBox()
        self.col_turno.addItems([str(i) for i in range(1, 21)])
        self.col_turno.setCurrentIndex(0)  # A por defecto
        col_layout2.addWidget(self.col_turno)
        grid.addLayout(col_layout2)

        col_layout3 = QVBoxLayout()
        col_layout3.addWidget(QLabel("Columna Supervisor:"))
        self.col_supervisor = QComboBox()
        self.col_supervisor.addItems(["No hay"] + [str(i) for i in range(1, 21)])
        self.col_supervisor.setCurrentIndex(2)
        col_layout3.addWidget(self.col_supervisor)
        grid.addLayout(col_layout3)

        col_layout4 = QVBoxLayout()
        col_layout4.addWidget(QLabel("Columna Veces:"))
        self.col_veces = QComboBox()
        self.col_veces.addItems([str(i) for i in range(1, 21)])
        self.col_veces.setCurrentIndex(4)  # E por defecto
        col_layout4.addWidget(self.col_veces)
        grid.addLayout(col_layout4)

        col_layout5 = QVBoxLayout()
        col_layout5.addWidget(QLabel("Columna Fecha:"))
        self.col_fecha = QComboBox()
        self.col_fecha.addItems(["No hay"] + [str(i) for i in range(1, 21)])
        col_layout5.addWidget(self.col_fecha)
        grid.addLayout(col_layout5)

        layout.addLayout(grid)

        layout.addSpacing(5)

        fila_inicio_layout = QHBoxLayout()
        fila_inicio_layout.addWidget(QLabel("Fila donde empiezan los datos:"))
        self.fila_inicio = QComboBox()
        self.fila_inicio.addItems([str(i) for i in range(1, 11)])
        self.fila_inicio.setCurrentIndex(2)  # Fila 3 por defecto
        fila_inicio_layout.addWidget(self.fila_inicio)
        fila_inicio_layout.addStretch()
        layout.addLayout(fila_inicio_layout)

        layout.addSpacing(10)

        boton_importar = QPushButton("Importar datos")
        boton_importar.setFixedHeight(40)
        boton_importar.clicked.connect(self._importar)
        layout.addWidget(boton_importar)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(100)
        self.log.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.log)

        self.setLayout(layout)

    def _seleccionar_archivo(self) -> None:
        """Abre el diálogo para seleccionar el archivo Excel."""
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "",
            "Excel (*.xlsx *.xls)"
        )
        if ruta:
            self.ruta_archivo = ruta
            self.label_archivo.setText(ruta.split("/")[-1])
            self.label_archivo.setStyleSheet("color: #4CAF50;")

    def _importar(self) -> None:
        """Ejecuta la importación con la configuración seleccionada."""
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "Seleccioná un archivo Excel primero.")
            return

        col_supervisor = None if self.col_supervisor.currentText() == "No hay" else int(self.col_supervisor.currentText())
        col_fecha = None if self.col_fecha.currentText() == "No hay" else int(self.col_fecha.currentText())

        self.log.clear()
        self.log.append("Importando...")

        try:
            pasadas, errores = importar_desde_excel(
                self.ruta_archivo,
                col_objetivo=int(self.col_objetivo.currentText()),
                col_turno=int(self.col_turno.currentText()),
                col_supervisor=col_supervisor,
                col_veces=int(self.col_veces.currentText()),
                col_fecha=col_fecha,
                fila_inicio=int(self.fila_inicio.currentText())
            )

            self.log.append(f"✓ {pasadas} pasadas importadas correctamente.")

            if errores:
                self.log.append(f"⚠ {len(errores)} errores:")
                for e in errores[:5]:
                    self.log.append(f"  {e}")

            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            registrar_accion(get_usuario_id(), f"Importó Excel: {pasadas} pasadas")

            QMessageBox.information(
                self, "Listo",
                f"Se importaron {pasadas} pasadas correctamente."
            )

        except Exception as e:
            self.log.append(f"✗ Error: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo importar: {e}")