# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado y gestión de supervisores con alta/baja
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox,
    QDialog, QLabel, QLineEdit, QDateEdit, QFormLayout,
    QDialogButtonBox, QHeaderView
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor
from models.supervisores import (
    listar_supervisores, actualizar_supervisor,
    dar_de_baja_supervisor, reactivar_supervisor
)
from services.sincronizacion import obtener_sincronizador


# =============================================================================
# DIÁLOGO DE EDICIÓN
# =============================================================================

class DialogoEditarSupervisor(QDialog):

    def __init__(self, supervisor_id: int, nombre: str,
                 fecha_alta: str | None, fecha_baja: str | None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar supervisor")
        self.setFixedWidth(320)
        self.supervisor_id = supervisor_id

        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        self.input_nombre = QLineEdit(nombre)
        layout.addRow("Nombre:", self.input_nombre)

        self.input_alta = QDateEdit()
        self.input_alta.setCalendarPopup(True)
        self.input_alta.setDisplayFormat("dd/MM/yyyy")
        if fecha_alta:
            self.input_alta.setDate(QDate.fromString(fecha_alta, "yyyy-MM-dd"))
        else:
            self.input_alta.setDate(QDate.currentDate())
        layout.addRow("Fecha de alta:", self.input_alta)

        self.input_baja = QDateEdit()
        self.input_baja.setCalendarPopup(True)
        self.input_baja.setDisplayFormat("dd/MM/yyyy")
        self.input_baja.setSpecialValueText("Sin baja")  # cuando está en fecha mínima = sin baja
        self.input_baja.setMinimumDate(QDate(2000, 1, 1))
        self._sin_baja = True

        # Checkbox simulado con botón toggle
        self.btn_toggle_baja = QPushButton("+ Agregar fecha de baja")
        self.btn_toggle_baja.setCheckable(True)
        self.btn_toggle_baja.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_baja.clicked.connect(self._toggle_baja)

        self._widget_baja = QWidget()
        baja_lay = QVBoxLayout(self._widget_baja)
        baja_lay.setContentsMargins(0, 0, 0, 0)
        baja_lay.addWidget(QLabel("Fecha de baja:"))
        baja_lay.addWidget(self.input_baja)
        self._widget_baja.setVisible(False)

        if fecha_baja:
            self.input_baja.setDate(QDate.fromString(fecha_baja, "yyyy-MM-dd"))
            self._widget_baja.setVisible(True)
            self.btn_toggle_baja.setText("✕ Quitar fecha de baja")
            self.btn_toggle_baja.setChecked(True)
            self._sin_baja = False

        layout.addRow(self.btn_toggle_baja)
        layout.addRow(self._widget_baja)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

        self.setLayout(layout)

    def _toggle_baja(self, checked: bool) -> None:
        self._sin_baja = not checked
        self._widget_baja.setVisible(checked)
        self.btn_toggle_baja.setText(
            "✕ Quitar fecha de baja" if checked else "+ Agregar fecha de baja"
        )

    def _guardar(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        fecha_alta = self.input_alta.date().toString("yyyy-MM-dd")
        fecha_baja = None if self._sin_baja else self.input_baja.date().toString("yyyy-MM-dd")

        if fecha_baja and fecha_baja < fecha_alta:
            QMessageBox.warning(self, "Error", "La fecha de baja no puede ser anterior al alta.")
            return

        actualizar_supervisor(self.supervisor_id, nombre, fecha_alta, fecha_baja)
        self.accept()


# =============================================================================
# PANTALLA PRINCIPAL
# =============================================================================

class ListaSupervisores(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Listado de supervisores")
        self.setGeometry(200, 200, 580, 380)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Leyenda de colores
        leyenda = QHBoxLayout()
        for color, texto in [("#c8f7c5", "Activo"), ("#ffd6d6", "Dado de baja")]:
            lbl = QLabel(f"  {texto}  ")
            lbl.setStyleSheet(f"background-color: {color}; border-radius: 4px; padding: 2px 8px; font-size: 11px;")
            leyenda.addWidget(lbl)
        leyenda.addStretch()
        layout.addLayout(leyenda)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre", "Fecha alta", "Fecha baja", "Estado", "Acciones"
        ])
        self.tabla.setColumnWidth(0, 180)
        self.tabla.setColumnWidth(1, 95)
        self.tabla.setColumnWidth(2, 95)
        self.tabla.setColumnWidth(3, 80)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self._cargar_tabla()

        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(self._on_datos_cambiados)

    # ------------------------------------------------------------------

    def _cargar_tabla(self) -> None:
        supervisores = listar_supervisores(solo_activos=False)
        self.tabla.setUpdatesEnabled(False)
        self.tabla.clearContents()
        self.tabla.setRowCount(len(supervisores))

        COLOR_ACTIVO = QColor("#c8f7c5")
        COLOR_BAJA   = QColor("#ffd6d6")
        COLOR_TEXTO  = QColor("#111111")

        for i, s in enumerate(supervisores):
            sup_id, nombre, fecha_alta, fecha_baja = s
            activo = fecha_baja is None
            color  = COLOR_ACTIVO if activo else COLOR_BAJA

            def _item(texto):
                it = QTableWidgetItem(texto or "—")
                it.setBackground(color)
                it.setForeground(COLOR_TEXTO)
                return it

            self.tabla.setItem(i, 0, _item(nombre))
            self.tabla.setItem(i, 1, _item(
                self._formatear_fecha(fecha_alta)
            ))
            self.tabla.setItem(i, 2, _item(
                self._formatear_fecha(fecha_baja) if fecha_baja else "—"
            ))
            self.tabla.setItem(i, 3, _item("Activo" if activo else "Baja"))

            # Botones de acción
            contenedor = QWidget()
            fila_btn = QHBoxLayout(contenedor)
            fila_btn.setContentsMargins(4, 2, 4, 2)
            fila_btn.setSpacing(6)
            contenedor.setStyleSheet(f"background-color: {'#c8f7c5' if activo else '#ffd6d6'};")

            btn_editar = QPushButton("✏ Editar")
            btn_editar.setFixedHeight(26)
            btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_editar.clicked.connect(
                lambda _, sid=sup_id, n=nombre, fa=fecha_alta, fb=fecha_baja:
                self._editar(sid, n, fa, fb)
            )
            fila_btn.addWidget(btn_editar)

            if activo:
                btn_baja = QPushButton("📅 Dar de baja")
                btn_baja.setFixedHeight(26)
                btn_baja.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_baja.setStyleSheet("color: #c0392b; font-weight: 600;")
                btn_baja.clicked.connect(
                    lambda _, sid=sup_id, n=nombre: self._dar_de_baja(sid, n)
                )
                fila_btn.addWidget(btn_baja)
            else:
                btn_reactivar = QPushButton("↩ Reactivar")
                btn_reactivar.setFixedHeight(26)
                btn_reactivar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_reactivar.setStyleSheet("color: #27ae60; font-weight: 600;")
                btn_reactivar.clicked.connect(
                    lambda _, sid=sup_id, n=nombre: self._reactivar(sid, n)
                )
                fila_btn.addWidget(btn_reactivar)

            self.tabla.setCellWidget(i, 4, contenedor)
            self.tabla.setRowHeight(i, 36)

        self.tabla.setUpdatesEnabled(True)

    def _formatear_fecha(self, fecha_iso: str | None) -> str:
        if not fecha_iso:
            return "—"
        try:
            from datetime import datetime
            return datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return fecha_iso

    # ------------------------------------------------------------------

    def _editar(self, sup_id, nombre, fecha_alta, fecha_baja) -> None:
        dialogo = DialogoEditarSupervisor(sup_id, nombre, fecha_alta, fecha_baja, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._cargar_tabla()

    def _dar_de_baja(self, sup_id: int, nombre: str) -> None:
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Fecha de baja")
        dialogo.setFixedWidth(280)
        lay = QVBoxLayout(dialogo)
        lay.addWidget(QLabel(f"Seleccioná la fecha de baja de <b>{nombre}</b>:"))
        date_edit = QDateEdit(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd/MM/yyyy")
        lay.addWidget(date_edit)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        lay.addWidget(botones)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            fecha_baja = date_edit.date().toString("yyyy-MM-dd")
            dar_de_baja_supervisor(sup_id, fecha_baja)
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            registrar_accion(get_usuario_id(), f"Dio de baja supervisor id={sup_id} fecha={fecha_baja}")
            self._cargar_tabla()

    def _reactivar(self, sup_id: int, nombre: str) -> None:
        confirmar = QMessageBox.question(
            self, "Reactivar supervisor",
            f"¿Reactivar a <b>{nombre}</b>?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            reactivar_supervisor(sup_id)
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            registrar_accion(get_usuario_id(), f"Reactivó supervisor id={sup_id}")
            self._cargar_tabla()

    def _on_datos_cambiados(self, tabla, operacion, datos):
        if tabla == "supervisores":
            self._cargar_tabla()