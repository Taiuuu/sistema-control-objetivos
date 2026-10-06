# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para agregar objetivos
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QDateEdit, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import QDate, Qt
from ui.animaciones import animar_entrada
from models.objetivos import agregar_objetivo
from services.validaciones import validar_objetivo, ErrorValidacion
from ui.components import GlassCard, PillButton
from ui.theme.theme_manager import get_theme_manager


# Mapeo de días de la semana a su número (formato ISO: 1=lunes, 7=domingo)
DIAS_MAP = {
    "Lunes": "1", "Martes": "2", "Miércoles": "3",
    "Jueves": "4", "Viernes": "5", "Sábado": "6", "Domingo": "7",
    "Feriados": "8"
}


# =============================================================================
# FORMULARIO DE OBJETIVO
# =============================================================================

class FormObjetivo(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar objetivo")
        self.setMinimumSize(440, 520)
        self._theme_manager = get_theme_manager()

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

        self.selector_tipo = QComboBox()
        self.selector_tipo.addItem("Puntual", "puntual")
        self.selector_tipo.addItem("Intermitente", "intermitente")

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
            checkbox.setChecked(True)
            checkbox.setFixedHeight(28)

        self.boton_guardar = PillButton("Guardar objetivo", "primary")
        self.boton_guardar.setObjectName("ObjectiveSaveButton")
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
        form_layout.addRow(QLabel("Tipo de objetivo"), self.selector_tipo)
        form_layout.addRow(self.checkbox_fin, self.input_fin)

        dias_widget = QFrame()
        dias_layout = QVBoxLayout(dias_widget)
        dias_layout.setContentsMargins(0, 0, 0, 0)
        dias_layout.setSpacing(6)
        for checkbox in self.dias.values():
            dias_layout.addWidget(checkbox)

        form_layout.addRow(QLabel("Días de cobertura"), dias_widget)

        card = GlassCard()
        card_layout = card.content_layout
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

        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())
        animar_entrada(self)

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self._titulo.setStyleSheet(
            f"color: {tokens['text_primary']}; font-size: {tokens['font_size_title']}; "
            "font-weight: 600; background: transparent;"
        )
        self._subtitulo.setStyleSheet(
            f"color: {tokens['text_secondary']}; font-size: {tokens['font_size_sm']}; "
            "background: transparent;"
        )
        self.boton_guardar.setStyleSheet(
            f"""
            QPushButton {{
                color: #FFFFFF;
                background-color: #0A6506;
                border: 1px solid #0A6506;
                border-radius: {tokens['radius_lg']};
                padding: 0 16px;
                min-height: 42px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                background-color: #075704;
                border-color: #075704;
            }}
            QPushButton:pressed {{
                color: #FFFFFF;
                background-color: #064A03;
            }}
            """
        )

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
        try:
            agregar_objetivo(nombre, inicio, dias_str, fecha_fin, self.selector_tipo.currentData())
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el objetivo: {error}")
            return

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(get_usuario_id(), f"Agregó objetivo: {nombre} | Inicio: {inicio} | Días: {dias_str}")

        QMessageBox.information(self, "Listo", f"Objetivo '{nombre}' guardado correctamente.")
        self.close()