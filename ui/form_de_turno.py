# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar el equipo de turno del día
# =============================================================================

from services.cache import obtener_supervisores_cache
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QComboBox, QDateEdit, QMessageBox, QSizePolicy,
    QScrollArea, QFrame
)
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from ui.animaciones import animar_entrada
from models.equipos import guardar_equipo_turno
from ui.components import GlassCard, PillButton
from ui.feedback import mostrar_error_usuario
from ui.components.calendar import configure_calendar_theme


def _cargar_supervisores() -> list:
    return obtener_supervisores_cache()


class FormTurno(QWidget):

    turno_registrado = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._supervisores = _cargar_supervisores()
        self._tiene_tercero = False

        self.setWindowTitle("Registrar turno")
        self.setMinimumSize(360, 360)

        self._titulo = QLabel("Registrar equipo de turno")
        self._titulo.setObjectName("TituloPrincipal")

        self._subtitulo = QLabel("Seleccioná los supervisores que estarán de turno hoy.")
        self._subtitulo.setObjectName("Subtitulo")
        self._subtitulo.setWordWrap(True)

        self.input_fecha = QDateEdit()
        self.input_fecha.setCalendarPopup(True)
        configure_calendar_theme(self.input_fecha)
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setFixedHeight(34)

        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self.input_turno.setFixedHeight(34)

        self.input_sup1 = QComboBox()
        self.input_sup1.setFixedHeight(34)
        self._poblar_combo(self.input_sup1)

        self.input_sup2 = QComboBox()
        self.input_sup2.setFixedHeight(34)
        self._poblar_combo(self.input_sup2)

        self.input_sup3 = QComboBox()
        self.input_sup3.setFixedHeight(34)
        self._poblar_combo(self.input_sup3)

        if len(self._supervisores) >= 2:
            self.input_sup2.setCurrentIndex(1)
        if len(self._supervisores) >= 3:
            self.input_sup3.setCurrentIndex(2)

        self.btn_agregar_sup3 = PillButton("＋  Agregar supervisor", "secondary")
        self.btn_agregar_sup3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar_sup3.setFixedHeight(34)
        if len(self._supervisores) < 3:
            self.btn_agregar_sup3.setEnabled(False)
            self.btn_agregar_sup3.setToolTip(
                "Se necesitan al menos tres supervisores para agregar un tercero."
            )
        self.btn_agregar_sup3.clicked.connect(self._mostrar_sup3)

        self.btn_quitar_sup3 = PillButton("✕ Quitar", "ghost")
        self.btn_quitar_sup3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quitar_sup3.setFixedWidth(86)
        self.btn_quitar_sup3.setFixedHeight(30)
        self.btn_quitar_sup3.clicked.connect(self._ocultar_sup3)

        self._fila_sup3 = QWidget()
        fila_layout = QVBoxLayout(self._fila_sup3)
        fila_layout.setContentsMargins(0, 0, 0, 0)
        fila_layout.setSpacing(10)

        cabecera_sup3 = QHBoxLayout()
        cabecera_sup3.addWidget(QLabel("Supervisor 3:"))
        cabecera_sup3.addStretch()
        cabecera_sup3.addWidget(self.btn_quitar_sup3)
        fila_layout.addLayout(cabecera_sup3)
        fila_layout.addWidget(self.input_sup3)
        self._fila_sup3.setVisible(False)

        self.boton_guardar = PillButton("Guardar turno", "primary")
        self.boton_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_guardar.setFixedHeight(42)
        self.boton_guardar.clicked.connect(self._guardar)
        if len(self._supervisores) < 2:
            self.boton_guardar.setEnabled(False)
            self._estado_supervisores = QLabel(
                "Se necesitan al menos dos supervisores. "
                "Agregalos desde la sección Gestión."
            )
            self._estado_supervisores.setObjectName("Subtitulo")
            self._estado_supervisores.setWordWrap(True)
        else:
            self._estado_supervisores = None

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow(QLabel("Fecha"), self.input_fecha)
        form_layout.addRow(QLabel("Turno"), self.input_turno)
        form_layout.addRow(QLabel("Supervisor 1"), self.input_sup1)
        form_layout.addRow(QLabel("Supervisor 2"), self.input_sup2)

        card = GlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(16)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.btn_agregar_sup3)
        card_layout.addWidget(self._fila_sup3)
        if self._estado_supervisores is not None:
            card_layout.addWidget(self._estado_supervisores)
        card_layout.addWidget(self.boton_guardar)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(14)
        layout_principal.addWidget(self._titulo)
        layout_principal.addWidget(self._subtitulo)
        self._area_desplazamiento = QScrollArea()
        self._area_desplazamiento.setWidgetResizable(True)
        self._area_desplazamiento.setFrameShape(QFrame.Shape.NoFrame)
        self._area_desplazamiento.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._area_desplazamiento.setWidget(card)
        layout_principal.addWidget(self._area_desplazamiento, 1)

        self.setLayout(layout_principal)
        animar_entrada(self)

    def _poblar_combo(self, combo: QComboBox) -> None:
        combo.clear()
        if not self._supervisores:
            combo.addItem("No hay supervisores para seleccionar", None)
            return

        for s in self._supervisores:
            if hasattr(s, "id") and hasattr(s, "nombre"):
                combo.addItem(s.nombre, s.id)
            else:
                combo.addItem(s[1], s[0])

    def _mostrar_sup3(self) -> None:
        self._tiene_tercero = True
        self._fila_sup3.setVisible(True)
        self.btn_agregar_sup3.setVisible(False)
        self._area_desplazamiento.ensureWidgetVisible(self._fila_sup3)

    def _ocultar_sup3(self) -> None:
        self._tiene_tercero = False
        self._fila_sup3.setVisible(False)
        self.btn_agregar_sup3.setVisible(True)

    def _guardar(self) -> None:
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()
        sup1  = self.input_sup1.currentData()
        sup2  = self.input_sup2.currentData()
        sup3  = self.input_sup3.currentData() if self._tiene_tercero else None

        if sup1 is None or sup2 is None or (self._tiene_tercero and sup3 is None):
            QMessageBox.warning(self, "Error", "Seleccioná todos los supervisores requeridos.")
            return

        ids = [sup1, sup2]
        if sup3 is not None:
            ids.append(sup3)

        if len(ids) != len(set(ids)):
            QMessageBox.warning(self, "Error", "Los supervisores deben ser distintos entre sí.")
            return

        try:
            guardar_equipo_turno(fecha, turno, sup1, sup2, sup3)
        except Exception as error:
            mostrar_error_usuario(
                self,
                "No se guardó el turno",
                "No se pudo guardar el equipo del turno. Revisá los datos e intentá nuevamente.",
                error,
            )
            return
        self.turno_registrado.emit()
        QMessageBox.information(self, "Listo", "Turno registrado correctamente.")
        self.close()