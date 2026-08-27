"""
ui/analisis_excel.py

Fase 11: pantalla de resumen del análisis (post analizar_excel()).

Esta pantalla es puramente de PRESENTACIÓN: recibe un ResultadoAnalisis
ya calculado y no importa nada de `models.*` ni abre conexión a la base
por su cuenta. Así se garantiza que "Cancelar" (o cerrar la ventana con
la X) nunca puede tocar la base, sin depender de que alguien recuerde
no llamar a nada de persistencia dentro de esta clase.

La resolución de matching pendiente (objetivos/supervisores "para
revisar") no se implementa acá: esta pantalla solo informa cuántos
quedan y bloquea "Continuar" mientras existan. La UI para resolverlos
vendría en una fase posterior (retoma los diálogos DialogoResolverObjetivos
/ DialogoResolverSupervisores del importador viejo, adaptados al nuevo
pipeline).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from importador.modelos import Problema, ResultadoAnalisis
from importador.reporte import generar_reporte_detallado

# Paleta reusada del importador viejo (mismo dark theme del resto de la app).
_COLOR_OK = "#8affc1"
_COLOR_INFO = "#64b5f6"
_COLOR_WARN = "#ffb74d"
_COLOR_ERROR = "#ff8a80"
_COLOR_TEXTO = "#d0d0d0"


class DialogoAnalisisExcel(QDialog):
    """Pantalla de resumen mostrada después de analizar_excel().

    Uso:
        resultado = analizar_excel(path, anio, conexion_bd)
        dialogo = DialogoAnalisisExcel(resultado, parent=self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            # el usuario apretó "Continuar" -> pasar a confirmar_importacion()
            ...
        # si fue Rejected (Cancelar o X), no se tocó la base en ningún momento.
    """

    def __init__(self, resultado: ResultadoAnalisis, parent=None):
        super().__init__(parent)
        self.resultado = resultado
        self.setWindowTitle("Análisis del archivo")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        titulo = QLabel("Análisis del archivo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(titulo)

        pasadas_ya_existentes = resultado.pasadas_omitir + resultado.pasadas_actualizar

        filas = [
            ("✅", f"{resultado.pasadas_nuevas} pasadas listas", _COLOR_OK),
            ("🔵", f"{pasadas_ya_existentes} ya existentes", _COLOR_INFO),
            ("🟡", f"{resultado.pasadas_duplicadas} duplicados", _COLOR_WARN),
            ("🟡", f"{resultado.objetivos_para_revisar} objetivos para revisar", _COLOR_WARN),
            ("🟡", f"{resultado.supervisores_para_revisar} supervisores para revisar", _COLOR_WARN),
            ("🔴", f"{resultado.errores_criticos} errores críticos", _COLOR_ERROR),
        ]
        for icono, texto, color in filas:
            fila_layout = QHBoxLayout()
            label_icono = QLabel(icono)
            label_icono.setStyleSheet("font-size: 14px;")
            label_texto = QLabel(texto)
            label_texto.setStyleSheet(f"font-size: 13px; color: {color};")
            fila_layout.addWidget(label_icono)
            fila_layout.addWidget(label_texto)
            fila_layout.addStretch()
            layout.addLayout(fila_layout)

        if resultado.advertencias:
            label_advertencias = QLabel(
                f"({resultado.advertencias} advertencias adicionales — ver 'Revisar problemas')"
            )
            label_advertencias.setStyleSheet(f"font-size: 11px; color: {_COLOR_TEXTO};")
            layout.addWidget(label_advertencias)

        fila_secundaria = QHBoxLayout()
        self.boton_revisar = QPushButton("Revisar problemas")
        self.boton_revisar.clicked.connect(self._revisar_problemas)
        self.boton_descargar = QPushButton("Descargar análisis detallado")
        self.boton_descargar.clicked.connect(self._descargar_detallado)
        fila_secundaria.addWidget(self.boton_revisar)
        fila_secundaria.addWidget(self.boton_descargar)
        layout.addLayout(fila_secundaria)

        fila_principal = QHBoxLayout()
        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.clicked.connect(self.reject)  # nunca toca la base
        self.boton_continuar = QPushButton("Continuar")
        self.boton_continuar.clicked.connect(self.accept)
        self.boton_continuar.setEnabled(resultado.puede_continuar)
        if not resultado.puede_continuar:
            self.boton_continuar.setToolTip(
                "Resolvé los errores críticos y el matching pendiente "
                "(objetivos/supervisores) antes de continuar. No se "
                "permite importación parcial."
            )
        fila_principal.addStretch()
        fila_principal.addWidget(self.boton_cancelar)
        fila_principal.addWidget(self.boton_continuar)
        layout.addLayout(fila_principal)

    # ------------------------------------------------------------------

    def _revisar_problemas(self) -> None:
        DialogoListaProblemas(self.resultado.problemas, parent=self).exec()

    def _descargar_detallado(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar análisis detallado",
            "analisis_detallado.xlsx",
            "Excel (*.xlsx)",
        )
        if not ruta:
            return
        try:
            contenido = generar_reporte_detallado(self.resultado)
            with open(ruta, "wb") as archivo:
                archivo.write(contenido)
        except Exception as exc:
            QMessageBox.critical(
                self, "Error", f"No se pudo generar el reporte: {exc}"
            )
            return
        QMessageBox.information(self, "Listo", f"Reporte guardado en {ruta}")


class DialogoListaProblemas(QDialog):
    """Detalle de cada Problema (errores, advertencias y para_revisar)."""

    _COLOR_POR_TIPO = {
        "error_critico": _COLOR_ERROR,
        "advertencia": _COLOR_WARN,
        "para_revisar": _COLOR_INFO,
    }

    def __init__(self, problemas: list[Problema], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Problemas detectados")
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)

        tabla = QTableWidget(0, 5)
        tabla.setHorizontalHeaderLabels(["Tipo", "Hoja", "Fila", "Objetivo", "Descripción"])
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.verticalHeader().setVisible(False)

        for problema in problemas:
            fila = tabla.rowCount()
            tabla.insertRow(fila)
            valores = [
                problema.tipo,
                problema.hoja or "",
                str(problema.fila_excel) if problema.fila_excel is not None else "",
                problema.objetivo or "",
                problema.descripcion,
            ]
            color = self._COLOR_POR_TIPO.get(problema.tipo, _COLOR_TEXTO)
            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                item.setForeground(Qt.GlobalColor.white)
                tabla.setItem(fila, columna, item)
            tabla.item(fila, 0).setForeground(_color_a_qcolor(color))

        if not problemas:
            tabla.insertRow(0)
            tabla.setSpan(0, 0, 1, 5)
            tabla.setItem(0, 0, QTableWidgetItem("No se detectaron problemas."))

        layout.addWidget(tabla)

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(self.accept)
        layout.addWidget(boton_cerrar)


def _color_a_qcolor(hex_color: str):
    from PyQt6.QtGui import QColor
    return QColor(hex_color)