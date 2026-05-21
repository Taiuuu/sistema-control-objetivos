# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para agregar objetivos
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QDateEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import QDate, Qt
from ui.animaciones import animar_entrada
from models.objetivos import agregar_objetivo
from services.tema import obtener_tema
from services.validaciones import validar_objetivo, ErrorValidacion


# Mapeo de días de la semana a su número (formato ISO: 1=lunes, 7=domingo)
DIAS_MAP = {
    "Lunes": "1", "Martes": "2", "Miércoles": "3",
    "Jueves": "4", "Viernes": "5", "Sábado": "6", "Domingo": "7"
}


# =============================================================================
# FORMULARIO DE OBJETIVO
# =============================================================================

class FormObjetivo(QWidget):

    def __init__(self):
        super().__init__()
        self._tema = obtener_tema()
        self.setWindowTitle("Agregar objetivo")
        self.setMinimumSize(440, 520)
        self.setStyleSheet(self._generar_estilos())

        self._titulo = QLabel("Agregar objetivo")
        self._titulo.setObjectName("TituloPrincipal")

        self._subtitulo = QLabel("Define los datos básicos del objetivo y su cobertura semanal.")
        self._subtitulo.setObjectName("Subtitulo")
        self._subtitulo.setWordWrap(True)

        self.input_nombre = QLineEdit()
        self.input_nombre.setFixedHeight(34)

        self.input_inicio = QDateEdit()
        self.input_inicio.setDate(QDate.currentDate())
        self.input_inicio.setCalendarPopup(True)
        self.input_inicio.setDisplayFormat("dd/MM/yyyy")
        self.input_inicio.setFixedHeight(34)

        self.checkbox_fin = QCheckBox("Definir fecha fin")
        self.checkbox_fin.setFixedHeight(30)

        self.input_fin = QDateEdit()
        self.input_fin.setDate(QDate.currentDate())
        self.input_fin.setCalendarPopup(True)
        self.input_fin.setDisplayFormat("dd/MM/yyyy")
        self.input_fin.setEnabled(False)
        self.input_fin.setFixedHeight(34)
        self.checkbox_fin.stateChanged.connect(lambda: self.input_fin.setEnabled(self.checkbox_fin.isChecked()))

        self.dias = {dia: QCheckBox(dia) for dia in DIAS_MAP}
        for checkbox in self.dias.values():
            checkbox.setFixedHeight(28)

        self.boton_guardar = QPushButton("Guardar objetivo")
        self.boton_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_guardar.setFixedHeight(42)
        self.boton_guardar.clicked.connect(self._guardar)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow(QLabel("Nombre del objetivo"), self.input_nombre)
        form_layout.addRow(QLabel("Fecha inicio"), self.input_inicio)
        form_layout.addRow(self.checkbox_fin, self.input_fin)

        dias_widget = QFrame()
        dias_layout = QVBoxLayout(dias_widget)
        dias_layout.setContentsMargins(0, 0, 0, 0)
        dias_layout.setSpacing(6)
        for checkbox in self.dias.values():
            dias_layout.addWidget(checkbox)

        form_layout.addRow(QLabel("Días de cobertura"), dias_widget)

        card = QFrame()
        card.setObjectName("CardContenedor")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(16)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.boton_guardar)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(14)
        layout_principal.addWidget(self._titulo)
        layout_principal.addWidget(self._subtitulo)
        layout_principal.addWidget(card)

        self.setLayout(layout_principal)
        animar_entrada(self)

    def _generar_estilos(self) -> str:
        tema = self._tema
        return f"""
            QWidget {{
                background-color: {tema['background']};
                color: {tema['texto']};
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 13px;
            }}
            QLabel#TituloPrincipal {{
                color: {tema['texto']};
                font-size: 18px;
                font-weight: 700;
            }}
            QLabel#Subtitulo {{
                color: {tema['texto_secundario']};
                font-size: 12px;
            }}
            QFrame#CardContenedor {{
                background-color: {tema['background_secundario']};
                border: 1px solid {tema['border']};
                border-radius: 14px;
            }}
            QLineEdit, QDateEdit {{
                background-color: {tema['input_background']};
                color: {tema['texto']};
                border: 1px solid {tema['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
            QCheckBox {{
                color: {tema['texto']};
            }}
            QPushButton {{
                background-color: {tema['primario']};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-weight: 700;
                padding: 10px 18px;
            }}
            QPushButton:hover {{
                background-color: {tema['primario_hover']};
            }}
        """

    def _guardar(self) -> None:
        """Valida los datos y registra el nuevo objetivo en la base de datos."""
        nombre = self.input_nombre.text().strip()
        inicio = self.input_inicio.date().toString("yyyy-MM-dd")
        dias_seleccionados = [
            DIAS_MAP[dia] for dia, cb in self.dias.items() if cb.isChecked()
        ]

        if not dias_seleccionados:
            QMessageBox.warning(self, "Error", "Seleccioná al menos un día.")
            return

        dias_str = ",".join(dias_seleccionados)

        # Obtener fecha_fin solo si el checkbox está activo
        fecha_fin = self.input_fin.date().toString("yyyy-MM-dd") if self.checkbox_fin.isChecked() else None

        try:
            validar_objetivo(nombre, dias_str)
        except ErrorValidacion as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
            return

        # CORRECCIÓN: el orden correcto es (nombre, fecha_inicio, dias_semana, fecha_fin)
        agregar_objetivo(nombre, inicio, dias_str, fecha_fin)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó objetivo: {nombre} | Inicio: {inicio} | Días: {dias_str}")

        QMessageBox.information(self, "Listo", f"Objetivo '{nombre}' guardado correctamente.")
        self.close()