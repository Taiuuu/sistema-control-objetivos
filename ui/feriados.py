# =============================================================================
# VESP Organizations - Pantalla visual de feriados
# =============================================================================

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout
)
from PyQt6.QtCore import Qt, QDate

from services.feriados import (
    eliminar_feriado,
    registrar_feriado,
    obtener_feriados_mes,
    es_feriado,
)
from ui.components import GlassCard, PillButton, StatusBadge
from ui.components.base import wrap_content_in_glass_card
from ui.theme.theme_manager import get_theme_manager


class VistaFeriados(QWidget):
    def __init__(self):
        super().__init__()
        self._theme_manager = get_theme_manager()
        self.setWindowTitle("Feriados")
        self.resize(860, 620)

        self._fecha_actual = QDate.currentDate()
        self._mes_actual = self._fecha_actual.month()
        self._anio_actual = self._fecha_actual.year()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        cabecera = QHBoxLayout()
        self._titulo = QLabel("Gestión visual de feriados")
        self._titulo.setObjectName("Titulo")
        cabecera.addWidget(self._titulo)
        cabecera.addStretch()

        self._btn_anterior = PillButton("◀", "secondary")
        self._btn_anterior.clicked.connect(self._mes_anterior)
        self._btn_actual = PillButton("Hoy", "ghost")
        self._btn_actual.clicked.connect(self._ir_hoy)
        self._btn_siguiente = PillButton("▶", "secondary")
        self._btn_siguiente.clicked.connect(self._mes_siguiente)
        cabecera.addWidget(self._btn_anterior)
        cabecera.addWidget(self._btn_actual)
        cabecera.addWidget(self._btn_siguiente)
        layout.addLayout(cabecera)

        self._lbl_mes = QLabel()
        self._lbl_mes.setObjectName("Mes")
        layout.addWidget(self._lbl_mes)

        calendario_card = GlassCard(shadow=True)
        self._calendario = QGridLayout()
        self._calendario.setSpacing(8)
        calendario_card.add_layout(self._calendario)
        layout.addWidget(calendario_card, 1)

        self._estado = StatusBadge(
            "Hacé clic en un día para agregar o quitar un feriado.", "info"
        )
        self._estado.setWordWrap(True)
        layout.addWidget(self._estado)

        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())
        wrap_content_in_glass_card(self)
        self._cargar_calendario()

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.setStyleSheet(f"""
            QLabel#Titulo {{ color: {tokens['text_primary']}; font-size: {tokens['font_size_title']}; font-weight: 700; }}
            QLabel#Mes {{ color: {tokens['accent']}; font-size: {tokens['font_size_lg']}; font-weight: 600; }}
            QLabel#Weekday {{ color: {tokens['text_secondary']}; font-weight: 700; }}
            QPushButton#HolidayDay {{
                background: {tokens['surface_alt']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']};
                font-weight: 600;
            }}
            QPushButton#HolidayDay:hover {{
                border-color: {tokens['accent']};
                background: {tokens['sidebar_active_bg']};
            }}
            QPushButton#HolidayDay[feriado="true"] {{
                background: {tokens['accent']};
                color: {tokens['accent_text']};
                border-color: {tokens['accent']};
            }}
            QPushButton#HolidayDay[feriado="true"]:hover {{
                background: {tokens['accent_hover']};
            }}
        """)

    def _cargar_calendario(self) -> None:
        for i in reversed(range(self._calendario.count())):
            widget = self._calendario.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self._lbl_mes.setText(self._formatear_mes())
        self._feriados_mes = {f["fecha"] for f in obtener_feriados_mes(self._anio_actual, self._mes_actual)}

        nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for idx, nombre in enumerate(nombres):
            label = QLabel(nombre)
            label.setObjectName("Weekday")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._calendario.addWidget(label, 0, idx)

        primer_dia = QDate(self._anio_actual, self._mes_actual, 1)
        dias_en_mes = primer_dia.daysInMonth()
        inicio_columna = primer_dia.dayOfWeek() % 7

        for offset in range(1, dias_en_mes + 1):
            fecha = QDate(self._anio_actual, self._mes_actual, offset)
            fila = (offset + inicio_columna - 1) // 7 + 1
            columna = (offset + inicio_columna - 1) % 7
            boton = QPushButton(str(offset))
            boton.setObjectName("HolidayDay")
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setFixedHeight(64)
            fecha_str = fecha.toString("yyyy-MM-dd")
            boton.setProperty("feriado", fecha_str in self._feriados_mes)
            boton.clicked.connect(lambda checked=False, f=fecha_str: self._alternar_feriado(f))
            self._calendario.addWidget(boton, fila, columna)

        for _ in range(42 - (dias_en_mes + inicio_columna)):
            placeholder = QLabel("")
            placeholder.setFixedHeight(64)
            self._calendario.addWidget(placeholder, fila + 1, 0)

    def _formatear_mes(self) -> str:
        return datetime(self._anio_actual, self._mes_actual, 1).strftime("%B %Y").title()

    def _mes_anterior(self) -> None:
        if self._mes_actual == 1:
            self._mes_actual = 12
            self._anio_actual -= 1
        else:
            self._mes_actual -= 1
        self._cargar_calendario()

    def _mes_siguiente(self) -> None:
        if self._mes_actual == 12:
            self._mes_actual = 1
            self._anio_actual += 1
        else:
            self._mes_actual += 1
        self._cargar_calendario()

    def _ir_hoy(self) -> None:
        self._anio_actual = self._fecha_actual.year()
        self._mes_actual = self._fecha_actual.month()
        self._cargar_calendario()

    def _alternar_feriado(self, fecha: str) -> None:
        if es_feriado(fecha):
            eliminar_feriado(fecha)
            self._estado.setText(f"Se quitó el feriado de {fecha}.")
        else:
            registrar_feriado(fecha)
            self._estado.setText(f"Se registró el feriado de {fecha}.")
        self._cargar_calendario()
