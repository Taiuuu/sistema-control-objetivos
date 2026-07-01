# =============================================================================
# VESP Organizations - Pantalla visual de feriados
# =============================================================================

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate

from services.feriados import eliminar_feriado, listar_feriados, registrar_feriado
from services.tema import obtener_tema


class VistaFeriados(QWidget):
    def __init__(self):
        super().__init__()
        self._tema = obtener_tema()
        self.setWindowTitle("Feriados")
        self.resize(860, 620)
        self.setStyleSheet(self._estilos())

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

        self._btn_anterior = QPushButton("◀")
        self._btn_anterior.clicked.connect(self._mes_anterior)
        self._btn_actual = QPushButton("Hoy")
        self._btn_actual.clicked.connect(self._ir_hoy)
        self._btn_siguiente = QPushButton("▶")
        self._btn_siguiente.clicked.connect(self._mes_siguiente)
        cabecera.addWidget(self._btn_anterior)
        cabecera.addWidget(self._btn_actual)
        cabecera.addWidget(self._btn_siguiente)
        layout.addLayout(cabecera)

        self._lbl_mes = QLabel()
        self._lbl_mes.setObjectName("Mes")
        layout.addWidget(self._lbl_mes)

        self._calendario = QGridLayout()
        self._calendario.setSpacing(8)
        layout.addLayout(self._calendario)

        self._estado = QLabel("Hacé clic en un día para agregar o quitar un feriado.")
        self._estado.setObjectName("Estado")
        self._estado.setWordWrap(True)
        layout.addWidget(self._estado)

        self._cargar_calendario()

    def _estilos(self) -> str:
        tema = self._tema
        return f"""
            QWidget {{ background-color: {tema['background']}; color: {tema['texto']}; font-family: Segoe UI, Arial, sans-serif; }}
            QLabel#Titulo {{ font-size: 18px; font-weight: 700; }}
            QLabel#Mes {{ font-size: 14px; font-weight: 600; color: {tema['primario']}; }}
            QLabel#Estado {{ color: {tema['texto_secundario']}; font-size: 12px; }}
            QPushButton {{ background-color: {tema['background_secundario']}; color: {tema['texto']}; border: 1px solid {tema['border']}; border-radius: 8px; padding: 6px 10px; }}
            QPushButton:hover {{ background-color: {tema['primario']}; color: white; }}
            QFrame#Dia {{ border: 1px solid {tema['border']}; border-radius: 10px; padding: 8px; background-color: {tema['background_secundario']}; }}
            QFrame#DiaFeriado {{ border: 1px solid {tema['primario']}; border-radius: 10px; padding: 8px; background-color: {tema['primario']}; color: white; }}
        """

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
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight: 700; color: #6b7280;")
            self._calendario.addWidget(label, 0, idx)

        primer_dia = QDate(self._anio_actual, self._mes_actual, 1)
        dias_en_mes = primer_dia.daysInMonth()
        inicio_columna = primer_dia.dayOfWeek() % 7

        for offset in range(1, dias_en_mes + 1):
            fecha = QDate(self._anio_actual, self._mes_actual, offset)
            fila = (offset + inicio_columna - 1) // 7 + 1
            columna = (offset + inicio_columna - 1) % 7
            boton = QPushButton(str(offset))
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setFixedHeight(64)
            fecha_str = fecha.toString("yyyy-MM-dd")
            es_feriado = fecha_str in self._feriados_mes
            boton.setProperty("feriado", es_feriado)
            boton.setObjectName("DiaFeriado" if es_feriado else "Dia")
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
