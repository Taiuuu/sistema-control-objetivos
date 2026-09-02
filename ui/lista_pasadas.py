# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado, edición y eliminación de pasadas registradas
# =============================================================================

import sqlite3

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QDateEdit, QTimeEdit, QComboBox, QMessageBox, QDialog,
    QSpinBox, QLineEdit
)
from PyQt6.QtCore import QDate, QTime
from PyQt6.QtGui import QColor

from database.db import DB_PATH
from services.sincronizacion import obtener_sincronizador
from services.sesion import get_rol
from services.validador_horas_limite import validar_hora_turno_nocturno


# =============================================================================
# FUNCIONES DB
# =============================================================================

def _cargar_pasadas(
    fecha: str,
    supervisor_id: int | None = None,
    turno: str | None = None,
    busqueda: str = "",
) -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    query = """
        SELECT
            p.id,
            p.hora,
            p.turno,
            o.nombre,
            s.nombre,
            p.objetivo_id,
            p.supervisor_id
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
    """
    params = [fecha]

    if supervisor_id:
        query += " AND p.supervisor_id = ?"
        params.append(supervisor_id)

    if turno:
        query += " AND p.turno = ?"
        params.append(turno)

    if busqueda:
        query += " AND (LOWER(o.nombre) LIKE ? OR LOWER(s.nombre) LIKE ?)"
        termino = f"%{busqueda.lower()}%"
        params.extend([termino, termino])

    query += " ORDER BY p.hora"

    cursor.execute(query, tuple(params))

    datos = cursor.fetchall()
    conexion.close()
    return datos


def _eliminar_pasada(pasada_id: int) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM pasadas WHERE id = ?",
        (pasada_id,)
    )

    conexion.commit()
    conexion.close()


def _eliminar_pasadas_por_fecha(fecha: str) -> int:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM pasadas WHERE fecha = ?", (fecha,))
    eliminadas = cursor.rowcount

    conexion.commit()
    conexion.close()
    return eliminadas


def _eliminar_pasadas_por_mes(año: int, mes: int) -> int:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # Calcular primer y último día del mes
    from datetime import date
    import calendar
    
    primer_dia = date(año, mes, 1)
    ultimo_dia = date(año, mes, calendar.monthrange(año, mes)[1])
    
    cursor.execute(
        "DELETE FROM pasadas WHERE fecha >= ? AND fecha <= ?",
        (primer_dia.strftime('%Y-%m-%d'), ultimo_dia.strftime('%Y-%m-%d'))
    )
    eliminadas = cursor.rowcount

    conexion.commit()
    conexion.close()
    return eliminadas


def _obtener_info_pasada(pasada_id: int):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.fecha,
            p.hora,
            p.turno,
            p.objetivo_id,
            p.supervisor_id,
            o.nombre,
            s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.id = ?
    """, (pasada_id,))

    dato = cursor.fetchone()
    conexion.close()
    return dato


def _actualizar_pasada(
    pasada_id: int,
    hora: str,
    turno: str,
    objetivo_id: int,
    supervisor_id: int,
    fecha: str | None = None
) -> None:

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    if fecha:
        cursor.execute("""
            UPDATE pasadas
            SET fecha = ?, hora = ?, turno = ?, objetivo_id = ?, supervisor_id = ?
            WHERE id = ?
        """, (
            fecha,
            hora,
            turno,
            objetivo_id,
            supervisor_id,
            pasada_id
        ))
    else:
        cursor.execute("""
            UPDATE pasadas
            SET hora = ?, turno = ?, objetivo_id = ?, supervisor_id = ?
            WHERE id = ?
        """, (
            hora,
            turno,
            objetivo_id,
            supervisor_id,
            pasada_id
        ))

    conexion.commit()
    conexion.close()


def _cargar_objetivos() -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("SELECT id, nombre FROM objetivos ORDER BY nombre")
    datos = cursor.fetchall()

    conexion.close()
    return datos


def _cargar_supervisores() -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("SELECT id, nombre FROM supervisores ORDER BY nombre")
    datos = cursor.fetchall()

    conexion.close()
    return datos


# =============================================================================
# DIALOGO EDITAR
# =============================================================================

class DialogoEditarPasada(QDialog):

    def __init__(self, pasada_id: int, parent=None):
        super().__init__(parent)

        self.pasada_id = pasada_id
        self.setWindowTitle("Editar pasada")
        self.setFixedSize(360, 300)

        info = _obtener_info_pasada(pasada_id)

        if not info:
            QMessageBox.warning(self, "Error", "No se encontró la pasada.")
            self.reject()
            return

        (
            _,
            fecha,
            hora,
            turno,
            objetivo_id,
            supervisor_id,
            _,
            _
        ) = info

        self.pasada_id = pasada_id
        self.fecha_original = fecha

        layout = QVBoxLayout()

        # Hora
        layout.addWidget(QLabel("Hora:"))

        self.input_hora = QTimeEdit()
        self.input_hora.setDisplayFormat("HH:mm")

        tiempo = QTime.fromString(hora, "HH:mm")
        if tiempo.isValid():
            self.input_hora.setTime(tiempo)
        else:
            self.input_hora.setTime(QTime(0, 0))

        layout.addWidget(self.input_hora)

        # Turno
        layout.addWidget(QLabel("Turno:"))

        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self.input_turno.setCurrentText(turno)

        layout.addWidget(self.input_turno)

        # Objetivo
        layout.addWidget(QLabel("Objetivo:"))

        self.input_objetivo = QComboBox()

        for item in _cargar_objetivos():
            self.input_objetivo.addItem(item[1], item[0])

            if item[0] == objetivo_id:
                self.input_objetivo.setCurrentIndex(
                    self.input_objetivo.count() - 1
                )

        layout.addWidget(self.input_objetivo)

        # Supervisor
        layout.addWidget(QLabel("Supervisor:"))

        self.input_supervisor = QComboBox()

        for item in _cargar_supervisores():
            self.input_supervisor.addItem(item[1], item[0])

            if item[0] == supervisor_id:
                self.input_supervisor.setCurrentIndex(
                    self.input_supervisor.count() - 1
                )

        layout.addWidget(self.input_supervisor)

        # Botones
        fila_botones = QHBoxLayout()

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self._guardar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        fila_botones.addWidget(btn_guardar)
        fila_botones.addWidget(btn_cancelar)

        layout.addLayout(fila_botones)

        self.setLayout(layout)

    def _guardar(self):

        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()
        fecha = self.fecha_original

        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

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

        _actualizar_pasada(
            self.pasada_id,
            hora,
            turno,
            objetivo_id,
            supervisor_id,
            fecha
        )

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id

        registrar_accion(
            get_usuario_id(),
            f"Editó pasada ID {self.pasada_id} | "
            f"Hora: {hora} | "
            f"Turno: {turno} | "
            f"Objetivo: {objetivo_nombre} | "
            f"Supervisor: {supervisor_nombre}"
        )

        QMessageBox.information(
            self,
            "Correcto",
            "Pasada actualizada correctamente."
        )

        self.accept()


# =============================================================================
# LISTA
# =============================================================================

class ListaPasadas(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Listado de Pasadas")
        self.resize(900, 500)

        layout = QVBoxLayout()

        # Filtros principales
        fila = QHBoxLayout()

        fila.addWidget(QLabel("Fecha:"))

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.dateChanged.connect(self._cargar_tabla)

        fila.addWidget(self.selector_fecha)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar objetivo o supervisor...")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.textChanged.connect(self._cargar_tabla)
        fila.addWidget(self.buscador, 1)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setCheckable(True)
        self.btn_filtrar.toggled.connect(self._alternar_filtros)
        fila.addWidget(self.btn_filtrar)

        self.btn_eliminar_dia = QPushButton("Eliminar día (Admin)")
        self.btn_eliminar_dia.clicked.connect(self._eliminar_dia_actual)
        self.btn_eliminar_dia.setVisible(False)

        fila.addWidget(self.btn_eliminar_dia)
        fila.addStretch()

        layout.addLayout(fila)

        # Filtros avanzados colapsables
        self.panel_filtros = QWidget()
        panel_layout = QHBoxLayout(self.panel_filtros)
        panel_layout.setContentsMargins(0, 8, 0, 8)
        panel_layout.addWidget(QLabel("Supervisor:"))
        self.selector_supervisor = QComboBox()
        self.selector_supervisor.addItem("Todos", 0)
        for sup_id, sup_nombre in _cargar_supervisores():
            self.selector_supervisor.addItem(sup_nombre, sup_id)
        self.selector_supervisor.currentIndexChanged.connect(self._cargar_tabla)
        panel_layout.addWidget(self.selector_supervisor)

        panel_layout.addWidget(QLabel("Turno:"))
        self.selector_turno = QComboBox()
        self.selector_turno.addItems(["Todos", "diurno", "nocturno"])
        self.selector_turno.currentTextChanged.connect(self._cargar_tabla)
        panel_layout.addWidget(self.selector_turno)
        panel_layout.addStretch()
        self.panel_filtros.setVisible(False)

        layout.addWidget(self.panel_filtros)

        # Filtros para mes
        fila_mes = QHBoxLayout()

        fila_mes.addWidget(QLabel("Eliminar pasadas por mes (Admin):"))

        fila_mes.addWidget(QLabel("Mes:"))
        self.selector_mes = QComboBox()
        self.selector_mes.addItems([
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ])
        self.selector_mes.setCurrentIndex((QDate.currentDate().month() - 1) % 12)
        fila_mes.addWidget(self.selector_mes)

        fila_mes.addWidget(QLabel("Año:"))
        self.selector_ano = QSpinBox()
        self.selector_ano.setMinimum(2020)
        self.selector_ano.setMaximum(2099)
        self.selector_ano.setValue(QDate.currentDate().year())
        fila_mes.addWidget(self.selector_ano)

        self.btn_eliminar_mes = QPushButton("Eliminar mes (Admin)")
        self.btn_eliminar_mes.clicked.connect(self._eliminar_mes_actual)
        self.btn_eliminar_mes.setVisible(False)

        fila_mes.addWidget(self.btn_eliminar_mes)
        fila_mes.addStretch()

        layout.addLayout(fila_mes)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)

        self.tabla.setHorizontalHeaderLabels([
            "Hora",
            "Turno",
            "Objetivo",
            "Supervisor",
            "Editar",
            "Eliminar"
        ])

        self.tabla.setColumnWidth(0, 90)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 250)
        self.tabla.setColumnWidth(3, 180)
        self.tabla.setColumnWidth(4, 100)
        self.tabla.setColumnWidth(5, 100)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSortingEnabled(True)

        layout.addWidget(self.tabla)

        self.setLayout(layout)

        self._actualizar_permisos()
        self._cargar_tabla()

        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(
            self._on_datos_cambiados
        )

    def _actualizar_permisos(self):
        rol_actual = str(get_rol() or "").lower()
        es_admin = rol_actual in {"admin", "administrador"}
        self.btn_eliminar_dia.setVisible(es_admin)
        self.btn_eliminar_mes.setVisible(es_admin)

    def _alternar_filtros(self, visibles: bool) -> None:
        self.panel_filtros.setVisible(visibles)
        self.btn_filtrar.setText("Ocultar filtros" if visibles else "Filtrar")

    def _cargar_tabla(self):

        self._actualizar_permisos()
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        supervisor_id = self.selector_supervisor.currentData() or None
        turno = self.selector_turno.currentText()
        if turno == "Todos":
            turno = None

        datos = _cargar_pasadas(fecha, supervisor_id, turno, self.buscador.text().strip())

        self.tabla.setRowCount(len(datos))

        COLOR_DIURNO = QColor("#fff9db")
        COLOR_NOCTURNO = QColor("#dbeafe")
        COLOR_TEXTO = QColor("#111111")

        for fila, item in enumerate(datos):

            pasada_id = item[0]
            turno_pasada = item[2]
            color = COLOR_DIURNO if turno_pasada == "diurno" else COLOR_NOCTURNO

            def _item(texto):
                it = QTableWidgetItem(texto)
                it.setBackground(color)
                it.setForeground(COLOR_TEXTO)
                return it

            self.tabla.setItem(fila, 0, _item(item[1]))
            self.tabla.setItem(fila, 1, _item(item[2].capitalize()))
            self.tabla.setItem(fila, 2, _item(item[3]))
            self.tabla.setItem(fila, 3, _item(item[4]))

            btn_editar = QPushButton("Editar")
            btn_editar.clicked.connect(
                lambda _, pid=pasada_id: self._editar(pid)
            )
            self.tabla.setCellWidget(fila, 4, btn_editar)

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.clicked.connect(
                lambda _, pid=pasada_id: self._eliminar(pid)
            )
            self.tabla.setCellWidget(fila, 5, btn_eliminar)

    def _editar(self, pasada_id: int):

        dialogo = DialogoEditarPasada(pasada_id, self)

        if dialogo.exec():
            self._cargar_tabla()

    def _eliminar_dia_actual(self):
        rol_actual = str(get_rol() or "").lower()
        if rol_actual not in {"admin", "administrador"}:
            QMessageBox.warning(self, "Acceso denegado", "Solo los administradores pueden borrar todas las pasadas de un día.")
            return

        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación masiva",
            f"¿Seguro que querés eliminar TODAS las pasadas del día {fecha}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        eliminadas = _eliminar_pasadas_por_fecha(fecha)
        from services.logger import registrar_accion
        from services.sesion import get_usuario_id

        registrar_accion(
            get_usuario_id(),
            f"Eliminó {eliminadas} pasadas del día {fecha}"
        )
        self.sincronizador.notificar_cambio("pasadas", "DELETE", {"fecha": fecha, "cantidad": eliminadas})

        if eliminadas == 0:
            QMessageBox.information(self, "Sin resultados", f"No había pasadas para eliminar en {fecha}.")
        else:
            QMessageBox.information(self, "Listo", f"Se eliminaron {eliminadas} pasadas del día {fecha}.")

        self._cargar_tabla()

    def _eliminar_mes_actual(self):
        rol_actual = str(get_rol() or "").lower()
        if rol_actual not in {"admin", "administrador"}:
            QMessageBox.warning(self, "Acceso denegado", "Solo los administradores pueden borrar todas las pasadas de un mes.")
            return

        mes_idx = self.selector_mes.currentIndex()
        mes = mes_idx + 1
        año = self.selector_ano.value()
        
        meses_nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = meses_nombres[mes_idx]

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación masiva",
            f"¿Seguro que querés eliminar TODAS las pasadas de {mes_nombre} {año}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        eliminadas = _eliminar_pasadas_por_mes(año, mes)
        from services.logger import registrar_accion
        from services.sesion import get_usuario_id

        registrar_accion(
            get_usuario_id(),
            f"Eliminó {eliminadas} pasadas del mes {mes_nombre} {año}"
        )
        self.sincronizador.notificar_cambio("pasadas", "DELETE", {"mes": mes, "año": año, "cantidad": eliminadas})

        if eliminadas == 0:
            QMessageBox.information(self, "Sin resultados", f"No había pasadas para eliminar en {mes_nombre} {año}.")
        else:
            QMessageBox.information(self, "Listo", f"Se eliminaron {eliminadas} pasadas de {mes_nombre} {año}.")

        self._cargar_tabla()

    def _eliminar(self, pasada_id: int):

        respuesta = QMessageBox.question(
            self,
            "Confirmar",
            "¿Seguro que querés eliminar esta pasada?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        info = _obtener_info_pasada(pasada_id)

        _eliminar_pasada(pasada_id)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id

        if info:
            registrar_accion(
                get_usuario_id(),
                f"Eliminó pasada | "
                f"Fecha: {info[1]} | "
                f"Hora: {info[2]} | "
                f"Turno: {info[3]} | "
                f"Objetivo: {info[6]} | "
                f"Supervisor: {info[7]}"
            )

        self._cargar_tabla()

    def _on_datos_cambiados(self, tabla, operacion, datos):

        if tabla in ["pasadas", "objetivos", "supervisores"]:
            self._cargar_tabla()