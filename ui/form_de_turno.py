# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar el equipo de turno del día
# =============================================================================

from services.cache import obtener_supervisores_cache
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import QDate, Qt
from ui.animaciones import animar_entrada
from models.equipos import guardar_equipo_turno


def _cargar_supervisores() -> list:
    return obtener_supervisores_cache(generar_si_falta=True)


class FormTurno(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar turno")
        self.setGeometry(300, 300, 370, 320)
        self._supervisores = _cargar_supervisores()
        self._tiene_tercero = False

        self._layout = QVBoxLayout()
        self._layout.setSpacing(6)
        self._layout.setContentsMargins(16, 16, 16, 16)

        # Fecha
        self._layout.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        self._layout.addWidget(self.input_fecha)

        # Turno
        self._layout.addWidget(QLabel("Turno:"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self._layout.addWidget(self.input_turno)

        # Supervisor 1
        self._layout.addWidget(QLabel("Supervisor 1:"))
        self.input_sup1 = QComboBox()
        self._poblar_combo(self.input_sup1)
        self._layout.addWidget(self.input_sup1)

        # Supervisor 2
        self._layout.addWidget(QLabel("Supervisor 2:"))
        self.input_sup2 = QComboBox()
        self._poblar_combo(self.input_sup2)
        self._layout.addWidget(self.input_sup2)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        self._layout.addWidget(sep)

        # Botón agregar supervisor 3
        self.btn_agregar_sup3 = QPushButton("＋  Agregar supervisor")
        self.btn_agregar_sup3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar_sup3.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4ade80;
                border: 1px dashed #4ade80;
                border-radius: 6px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #14532d;
            }
        """)
        self.btn_agregar_sup3.clicked.connect(self._mostrar_sup3)
        self._layout.addWidget(self.btn_agregar_sup3)

        # Bloque supervisor 3 (oculto por defecto)
        self._fila_sup3 = QWidget()
        fila_layout = QVBoxLayout(self._fila_sup3)
        fila_layout.setContentsMargins(0, 0, 0, 0)
        fila_layout.setSpacing(4)

        cabecera_sup3 = QHBoxLayout()
        lbl_sup3 = QLabel("Supervisor 3:")
        self.btn_quitar_sup3 = QPushButton("✕ Quitar")
        self.btn_quitar_sup3.setFixedWidth(70)
        self.btn_quitar_sup3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quitar_sup3.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f87171;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover { color: #dc2626; }
        """)
        self.btn_quitar_sup3.clicked.connect(self._ocultar_sup3)
        cabecera_sup3.addWidget(lbl_sup3)
        cabecera_sup3.addStretch()
        cabecera_sup3.addWidget(self.btn_quitar_sup3)
        fila_layout.addLayout(cabecera_sup3)

        self.input_sup3 = QComboBox()
        self._poblar_combo(self.input_sup3)
        fila_layout.addWidget(self.input_sup3)

        self._fila_sup3.setVisible(False)
        self._layout.addWidget(self._fila_sup3)

        # Guardar
        self.boton_guardar = QPushButton("Guardar turno")
        self.boton_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_guardar.clicked.connect(self._guardar)
        self._layout.addWidget(self.boton_guardar)

        self.setLayout(self._layout)
        animar_entrada(self)

    def _poblar_combo(self, combo: QComboBox) -> None:
        for s in self._supervisores:
            combo.addItem(s[1], s[0])

    def _mostrar_sup3(self) -> None:
        self._tiene_tercero = True
        self._fila_sup3.setVisible(True)
        self.btn_agregar_sup3.setVisible(False)
        self.setFixedHeight(400)

    def _ocultar_sup3(self) -> None:
        self._tiene_tercero = False
        self._fila_sup3.setVisible(False)
        self.btn_agregar_sup3.setVisible(True)
        self.setFixedHeight(320)

    def _guardar(self) -> None:
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        sup1  = self.input_sup1.currentData()
        sup2  = self.input_sup2.currentData()
        sup3  = self.input_sup3.currentData() if self._tiene_tercero else None

        ids = [sup1, sup2]
        if sup3 is not None:
            ids.append(sup3)

        if len(ids) != len(set(ids)):
            QMessageBox.warning(self, "Error", "Los supervisores deben ser distintos entre sí.")
            return

        guardar_equipo_turno(fecha, turno, sup1, sup2, sup3)
        QMessageBox.information(self, "Listo", "Turno registrado correctamente.")
        self.close()