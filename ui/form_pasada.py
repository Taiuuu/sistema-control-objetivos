# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Formulario para registrar pasadas
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QFrame,
    QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import QDate, QTime, pyqtSignal, Qt

from models.turnos import registrar_turno
from ui.animaciones import animar_entrada
from database.db import DB_PATH
from services.tema import obtener_tema
from services.validaciones import validar_pasada, ErrorValidacion
from services.validador_horas_limite import validar_hora_turno_nocturno
from services.importador.modelos import ResultadoMatchObjetivo, ResultadoMatchSupervisor

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _cargar_objetivos(fecha: str = None) -> list:
    """Retorna objetivos activos según fecha."""
    objetivos = [ResultadoMatchObjetivo(id=None, nombre="Sin supervisor", tipo="no_asignado")]


    if not fecha:
        return objetivos

    objetivos_filtrados = []

    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        for obj in objetivos:
            obj_id = obj[0]

            cursor.execute("""
                SELECT fecha_inicio, fecha_fin
                FROM objetivos
                WHERE id = ?
            """, (obj_id,))

            resultado = cursor.fetchone()

            if resultado:
                fecha_inicio, fecha_fin = resultado

                if (
                    (not fecha_inicio or fecha >= fecha_inicio)
                    and
                    (fecha_fin is None or fecha <= fecha_fin)
                ):
                    objetivos_filtrados.append(obj)

        conexion.close()

    except Exception as e:
        print("Error cargando objetivos:", e)
        return objetivos

    return objetivos_filtrados


def _cargar_supervisores_del_turno(fecha: str, turno: str) -> list:
    """Retorna supervisores asignados al turno."""
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT s.id, s.nombre, eq.posicion
            FROM (
                SELECT supervisor1_id AS supervisor_id, 1 AS posicion
                FROM equipos
                WHERE fecha = ? AND turno = ?

                UNION ALL

                SELECT supervisor2_id AS supervisor_id, 2 AS posicion
                FROM equipos
                WHERE fecha = ? AND turno = ?

                UNION ALL

                SELECT supervisor3_id AS supervisor_id, 3 AS posicion
                FROM equipos
                WHERE fecha = ? AND turno = ?
            ) AS eq
            JOIN supervisores s ON s.id = eq.supervisor_id
            GROUP BY s.id, s.nombre, eq.posicion
            ORDER BY eq.posicion
        """, (
            fecha, turno,
            fecha, turno,
            fecha, turno
        ))

        supervisores = cursor.fetchall()
        conexion.close()

        if supervisores:
            return supervisores

    except Exception as e:
        print("Error cargando supervisores:", e)

    return [ResultadoMatchSupervisor(id=None, nombre="Sin supervisor", tipo="no_asignado")]

# =============================================================================
# MEMORIA DEL ÚLTIMO TURNO
# =============================================================================

_ultimo_turno = "diurno"


# =============================================================================
# FORMULARIO
# =============================================================================

class FormPasada(QWidget):

    pasada_registrada = pyqtSignal()

    def __init__(self, fecha_inicial: str = None):
        super().__init__()

        global _ultimo_turno

        self._tema = obtener_tema()
        self.setWindowTitle("Registrar pasada")
        self.setMinimumSize(420, 420)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setStyleSheet(self._generar_estilos())

        if fecha_inicial:
            fecha = QDate.fromString(fecha_inicial, "yyyy-MM-dd")
        else:
            fecha = QDate.currentDate()

        self.input_fecha = QDateEdit()
        self.input_fecha.setCalendarPopup(True)
        self.input_fecha.setDate(fecha)
        self.input_fecha.setFixedHeight(34)

        self.input_hora = QTimeEdit()
        self.input_hora.setDisplayFormat("HH:mm")
        self.input_hora.setTime(QTime.currentTime())
        self.input_hora.setFixedHeight(34)

        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self.input_turno.setCurrentText(_ultimo_turno)
        self.input_turno.setFixedHeight(34)

        self.input_objetivo = QComboBox()
        self.input_objetivo.setFixedHeight(34)

        self.input_supervisor = QComboBox()
        self.input_supervisor.setFixedHeight(34)

        self.boton_guardar = QPushButton("Registrar pasada")
        self.boton_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_guardar.setFixedHeight(40)
        self.boton_guardar.clicked.connect(self._guardar)

        self._titulo = QLabel("Registrar pasada")
        self._titulo.setObjectName("TituloPrincipal")

        self._subtitulo = QLabel("Completa los datos de la pasada y presiona registrar.")
        self._subtitulo.setObjectName("Subtitulo")
        self._subtitulo.setWordWrap(True)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(0, 0, 0, 0)

        form_layout.addRow(QLabel("Fecha"), self.input_fecha)
        form_layout.addRow(QLabel("Hora"), self.input_hora)
        form_layout.addRow(QLabel("Turno"), self.input_turno)
        form_layout.addRow(QLabel("Objetivo"), self.input_objetivo)
        form_layout.addRow(QLabel("Supervisor"), self.input_supervisor)

        card = QFrame()
        card.setObjectName("CardContenedor")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(20)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.boton_guardar)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(16)
        layout_principal.addWidget(self._titulo)
        layout_principal.addWidget(self._subtitulo)
        layout_principal.addWidget(card)

        self.setLayout(layout_principal)

        # ---------------------------------------------------------------------
        # EVENTOS
        # ---------------------------------------------------------------------
        self.input_fecha.dateChanged.connect(self._actualizar_listas)
        self.input_turno.currentTextChanged.connect(self._actualizar_listas)

        # ---------------------------------------------------------------------
        # CARGA INICIAL
        # ---------------------------------------------------------------------
        self._actualizar_listas()
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
            QComboBox, QDateEdit, QTimeEdit {{
                background-color: {tema['input_background']};
                color: {tema['texto']};
                border: 1px solid {tema['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QPushButton {{
                background-color: {tema['primario']};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-weight: 700;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {tema['primario_hover']};
            }}
            QPushButton:pressed {{
                background-color: {tema['primario']};
            }}
            QLabel {{
                color: {tema['texto']};
            }}
        """

    # =========================================================================
    # ACTUALIZAR COMBOS
    # =========================================================================
    def _actualizar_listas(self):
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        turno = self.input_turno.currentText()

        # Objetivos
        self.input_objetivo.clear()

        objetivos = _cargar_objetivos(fecha)

        for obj in objetivos:
            self.input_objetivo.addItem(obj[1], obj[0])

        # Supervisores
        self.input_supervisor.clear()

        supervisores = _cargar_supervisores_del_turno(fecha, turno)

        for sup in supervisores:
            if len(sup) >= 3:
                label = f"Sup {sup[2]} - {sup[1]}"
            else:
                label = sup[1]
            self.input_supervisor.addItem(label, sup[0])

    # =========================================================================
    # GUARDAR
    # =========================================================================
    def _guardar(self):
        global _ultimo_turno

        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()

        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()

        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        if not objetivo_id or not supervisor_id:
            QMessageBox.warning(
                self,
                "Error",
                "Seleccioná un objetivo y un supervisor."
            )
            return

        try:
            validar_pasada(
                fecha,
                hora,
                turno,
                objetivo_id,
                supervisor_id
            )

        except ErrorValidacion as e:
            QMessageBox.warning(
                self,
                "Error de validación",
                str(e)
            )
            return

        # Validar horas límite (07:00-07:59) para turnos nocturnos
        es_valida, sugerencia = validar_hora_turno_nocturno(fecha, hora, turno)
        
        if not es_valida and sugerencia and sugerencia.get('tipo') == 'hora_limite':
            respuesta = QMessageBox.question(
                self,
                "⚠️ Hora límite de turno nocturno",
                f"{sugerencia['razon']}\n\n"
                f"Hora actual: {hora}\n"
                f"Fecha actual: {fecha}\n"
                f"{sugerencia['pregunta']}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.Yes:
                fecha = sugerencia['fecha_sugerida']
                QMessageBox.information(
                    self,
                    "Fecha ajustada",
                    f"La pasada se registrará con fecha: {fecha}\n"
                    f"(Correspondiente al turno nocturno anterior)"
                )
            else:
                QMessageBox.information(
                    self,
                    "Fecha mantenida",
                    f"La pasada se registrará en la fecha: {fecha}"
                )

        try:
            registrar_turno(
                fecha=fecha,
                turno=turno,
                objetivo_id=objetivo_id,
                supervisor_id=supervisor_id,
                hora=hora
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )
            return

        _ultimo_turno = turno

        # Log
        try:
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id

            registrar_accion(
                get_usuario_id(),
                f"Registró pasada - "
                f"Objetivo: {objetivo_nombre} | "
                f"Supervisor: {supervisor_nombre} | "
                f"Turno: {turno} | "
                f"Fecha: {fecha} | "
                f"Hora: {hora}"
            )

        except Exception:
            pass

        self.pasada_registrada.emit()

        QMessageBox.information(
            self,
            "Correcto",
            f"Pasada registrada en {objetivo_nombre}"
        )

        # Reiniciar hora actual
        self.input_hora.setTime(QTime.currentTime())