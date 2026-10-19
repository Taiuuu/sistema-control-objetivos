# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado, edición y eliminación de pasadas registradas
# =============================================================================

import logging
import sqlite3

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QDateEdit, QTimeEdit, QComboBox, QMessageBox, QDialog,
    QSpinBox, QLineEdit, QMenu, QHeaderView, QProgressBar, QInputDialog
)
from PyQt6.QtCore import QDate, QSignalBlocker, QTime, Qt

from database.db import DB_PATH
from services.operaciones_seguras import (
    eliminar_pasadas_mes,
    obtener_vista_previa_borrado_mes,
)
from services.sincronizacion import obtener_sincronizador
from services.sesion import get_rol
from services.validador_horas_limite import validar_hora_turno_nocturno
from services.background_task import run_background_task
from services.queries_tabla import (
    cargar_equipos_reportables,
    cargar_objetivos_reportables,
    cargar_supervisores,
)
from services.reportes_unificados.consultas import crear_datos_para_exportar
from services.reportes_unificados.datos import COLUMNAS_DIARIAS
from ui.reportes.acciones_exportacion import mostrar_dialogo_exportar
from ui.atajos import registrar_atajo
from ui.form_pasada import FormPasada
from ui.components import GlassCard, PillButton, SearchInput, StatusBadge
from ui.components.calendar import configure_calendar_theme
from ui.components.base import wrap_content_in_glass_card
from ui.tabla_lotes import cargar_tabla_en_lotes

logger = logging.getLogger(__name__)


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
    try:
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
            WHERE COALESCE(p.fecha_operativa, p.fecha) = ?
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
        return cursor.fetchall()
    finally:
        conexion.close()


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
    try:
        from services.backups.backup import crear_backup
        crear_backup("manual", conexion_origen=conexion)
        conexion.execute("BEGIN")
        cursor = conexion.execute(
            "DELETE FROM pasadas WHERE COALESCE(fecha_operativa, fecha) = ?",
            (fecha,),
        )
        eliminadas = cursor.rowcount
        conexion.commit()
        return eliminadas
    except Exception:
        conexion.rollback()
        import logging
        logging.getLogger(__name__).exception(
            "No se pudieron eliminar las pasadas del día %s", fecha
        )
        raise
    finally:
        conexion.close()


def _eliminar_pasadas_por_mes(año: int, mes: int, confirmacion: str) -> int:
    conexion = sqlite3.connect(DB_PATH)
    try:
        return eliminar_pasadas_mes(conexion, año, mes, confirmacion)
    finally:
        conexion.close()


def _vista_previa_pasadas_mes(año: int, mes: int) -> dict:
    conexion = sqlite3.connect(DB_PATH)
    try:
        return obtener_vista_previa_borrado_mes(conexion, año, mes)
    finally:
        conexion.close()


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
        btn_guardar.setObjectName("PrimaryButton")
        btn_guardar.clicked.connect(self._guardar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        fila_botones.addWidget(btn_guardar)
        fila_botones.addWidget(btn_cancelar)

        layout.addLayout(fila_botones)

        self.setLayout(layout)
        wrap_content_in_glass_card(self)

    def _guardar(self):

        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()
        fecha = self.fecha_original

        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        # La hora no determina el turno cuando los ciclos se superponen.
        es_valida, sugerencia = validar_hora_turno_nocturno(fecha, hora, turno)
        
        if not es_valida:
            QMessageBox.warning(
                self,
                "Horario inválido",
                sugerencia["razon"],
            )
            return

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
        self.resize(900, 560)
        self.setMinimumSize(560, 360)
        self._carga_id = 0
        self._tareas_carga = {}
        self._timer_render = None

        layout = QVBoxLayout()
        card = GlassCard()
        card_layout = card.content_layout

        # Filtros principales
        fila = QHBoxLayout()

        fila.addWidget(QLabel("Fecha:"))

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setCalendarPopup(True)
        configure_calendar_theme(self.selector_fecha)
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.dateChanged.connect(self._cargar_tabla)

        fila.addWidget(self.selector_fecha)

        self.buscador = SearchInput("Buscar objetivo o supervisor...")
        self.buscador.setToolTip(
            "Buscar objetivo o supervisor (Ctrl+F); Esc limpia la búsqueda"
        )
        self.buscador.setClearButtonEnabled(True)
        self.buscador.textChanged.connect(self._cargar_tabla)
        fila.addWidget(self.buscador, 1)

        self.btn_filtrar = PillButton("Filtrar", "secondary")
        self.btn_filtrar.setToolTip("Mostrar u ocultar filtros adicionales")
        self.btn_filtrar.setCheckable(True)
        self.btn_filtrar.toggled.connect(self._alternar_filtros)
        fila.addWidget(self.btn_filtrar)
        self.contador_filtros = QLabel("0 filtros activos")
        self.contador_filtros.setAccessibleName("Cantidad de filtros activos")
        fila.addWidget(self.contador_filtros)
        self.btn_limpiar_filtros = PillButton("Limpiar filtros", "ghost")
        self.btn_limpiar_filtros.setToolTip("Restablecer los filtros")
        self.btn_limpiar_filtros.clicked.connect(self._limpiar_filtros)
        fila.addWidget(self.btn_limpiar_filtros)

        self.btn_exportar_excel = PillButton("Exportar Excel", "primary")
        self.btn_exportar_excel.setToolTip("Exportar (Ctrl+E)")
        self.btn_exportar_excel.clicked.connect(self._exportar_excel)
        fila.addWidget(self.btn_exportar_excel)

        self.btn_exportar_pdf = PillButton("Exportar PDF", "secondary")
        self.btn_exportar_pdf.setToolTip("Abrir opciones de exportación")
        self.btn_exportar_pdf.clicked.connect(self._exportar_pdf)
        fila.addWidget(self.btn_exportar_pdf)

        self.btn_eliminar_dia = PillButton("Eliminar día (Admin)", "danger")
        self.btn_eliminar_dia.clicked.connect(self._eliminar_dia_actual)
        self.btn_eliminar_dia.setVisible(False)

        fila.addWidget(self.btn_eliminar_dia)
        fila.addStretch()

        card_layout.addLayout(fila)

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

        card_layout.addWidget(self.panel_filtros)

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

        self.btn_eliminar_mes = PillButton("Eliminar mes (Admin)", "danger")
        self.btn_eliminar_mes.clicked.connect(self._eliminar_mes_actual)
        self.btn_eliminar_mes.setVisible(False)

        fila_mes.addWidget(self.btn_eliminar_mes)
        fila_mes.addStretch()

        card_layout.addLayout(fila_mes)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)

        self.tabla.setHorizontalHeaderLabels([
            "Hora",
            "Turno",
            "Objetivo",
            "Supervisor",
            "Acciones"
        ])

        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(42)
        self.tabla.setShowGrid(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setWordWrap(True)
        header = self.tabla.horizontalHeader()
        header.setMinimumSectionSize(58)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for columna in (0, 1, 4):
            header.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabla.setSortingEnabled(True)

        card_layout.addWidget(self.tabla)
        self.estado_carga = QLabel()
        card_layout.addWidget(self.estado_carga)
        self.barra_carga = QProgressBar()
        self.barra_carga.setRange(0, 0)
        self.barra_carga.setTextVisible(False)
        self.barra_carga.setMaximumHeight(5)
        self.barra_carga.hide()
        card_layout.addWidget(self.barra_carga)

        layout.addWidget(card)
        self.setLayout(layout)

        self._actualizar_permisos()
        registrar_atajo(self, "Ctrl+F", self.buscador.setFocus)
        registrar_atajo(self, "Ctrl+N", self._nueva_pasada)
        registrar_atajo(self, "F5", self._cargar_tabla)
        registrar_atajo(
            self,
            "Ctrl+E",
            self._exportar_excel,
        )
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
        self._actualizar_contador_filtros()

    def _nueva_pasada(self) -> None:
        self._form_pasada = FormPasada(
            fecha_inicial=self.selector_fecha.date().toString("yyyy-MM-dd")
        )
        self._form_pasada.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._form_pasada.pasada_registrada.connect(self._cargar_tabla)
        self._form_pasada.show()

    def _limpiar_filtros(self) -> None:
        blockers = [
            QSignalBlocker(widget)
            for widget in (
                self.selector_fecha,
                self.buscador,
                self.selector_supervisor,
                self.selector_turno,
            )
        ]
        self.selector_fecha.setDate(QDate.currentDate())
        self.buscador.clear()
        self.selector_supervisor.setCurrentIndex(0)
        self.selector_turno.setCurrentText("Todos")
        del blockers
        self._cargar_tabla()

    def _actualizar_contador_filtros(self) -> None:
        filtros_activos = sum(
            (
                self.selector_fecha.date() != QDate.currentDate(),
                bool(self.buscador.text().strip()),
                self.selector_supervisor.currentData() not in (None, 0),
                self.selector_turno.currentText() != "Todos",
            )
        )
        sufijo = "" if filtros_activos == 1 else "s"
        self.contador_filtros.setText(f"{filtros_activos} filtro{sufijo} activo{sufijo}")
        self.btn_filtrar.setText(
            f"Más filtros ({filtros_activos})"
            if filtros_activos
            else "Más filtros"
        )

    def _cargar_tabla(self, *_args):
        self._cancelar_renderizado()
        self._actualizar_permisos()
        self._carga_id += 1
        solicitud = self._carga_id
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        supervisor_id = self.selector_supervisor.currentData() or None
        turno = self.selector_turno.currentText()
        if turno == "Todos":
            turno = None

        self.estado_carga.setText("Cargando pasadas…")
        self.barra_carga.show()
        self.tabla.setEnabled(False)
        tarea = run_background_task(
            _cargar_pasadas,
            fecha,
            supervisor_id,
            turno,
            self.buscador.text().strip(),
        )
        self._tareas_carga[solicitud] = tarea
        tarea.signals.finished.connect(
            lambda datos, id_solicitud=solicitud:
                self._mostrar_pasadas(id_solicitud, datos)
        )
        tarea.signals.error.connect(
            lambda mensaje, id_solicitud=solicitud:
                self._error_carga(id_solicitud, mensaje)
        )

    def _mostrar_pasadas(self, solicitud: int, datos: list) -> None:
        self._tareas_carga.pop(solicitud, None)
        if solicitud != self._carga_id:
            return

        self.tabla.setSortingEnabled(False)
        self.tabla.setRowCount(len(datos))

        def poblar_fila(fila: int) -> None:
            item = datos[fila]
            pasada_id = item[0]
            turno_pasada = item[2]

            def _item(texto):
                celda = QTableWidgetItem(texto)
                celda.setToolTip(texto)
                return celda

            self.tabla.setItem(fila, 0, _item(item[1]))
            badge_turno = StatusBadge(
                item[2].capitalize(), "info" if turno_pasada == "diurno" else "warning"
            )
            self.tabla.setCellWidget(fila, 1, self._centrar_widget(badge_turno))
            self.tabla.setItem(fila, 2, _item(item[3]))
            self.tabla.setItem(fila, 3, _item(item[4]))

            menu = QMenu(self)
            menu.addAction(
                "Editar",
                lambda checked=False, pid=pasada_id: self._editar(pid),
            )
            accion_eliminar = menu.addAction(
                "Eliminar",
                lambda checked=False, pid=pasada_id: self._eliminar(pid),
            )
            accion_eliminar.setProperty("danger", True)
            boton_acciones = QPushButton("⋯")
            boton_acciones.setObjectName("ObjectiveActions")
            boton_acciones.setToolTip("Acciones de la pasada")
            boton_acciones.setMenu(menu)
            self.tabla.setCellWidget(fila, 4, self._centrar_widget(boton_acciones))

        self._timer_render = cargar_tabla_en_lotes(
            self.tabla,
            len(datos),
            poblar_fila,
            lambda: self._finalizar_render(solicitud, datos),
        )

    def _finalizar_render(self, solicitud: int, datos: list) -> None:
        if solicitud != self._carga_id:
            return
        self._timer_render = None
        self.tabla.setSortingEnabled(True)
        self.tabla.setEnabled(True)
        self.barra_carga.hide()
        self.estado_carga.setText(
            "" if datos else "Todavía no hay pasadas para esta fecha."
        )

    def _cancelar_renderizado(self) -> None:
        timer = self._timer_render
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            self._timer_render = None
        self.tabla.setSortingEnabled(True)

    def _error_carga(self, solicitud: int, mensaje: str) -> None:
        self._tareas_carga.pop(solicitud, None)
        if solicitud != self._carga_id:
            return
        self.tabla.setSortingEnabled(True)
        self.tabla.setEnabled(True)
        self.barra_carga.hide()
        self.estado_carga.setText("No se pudieron cargar las pasadas.")
        logger.error("No se pudo cargar la lista de pasadas: %s", mensaje)
        self._actualizar_contador_filtros()

    @staticmethod
    def _centrar_widget(widget: QWidget) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addStretch()
        layout.addWidget(widget)
        layout.addStretch()
        return contenedor

    def _exportar_excel(self) -> None:
        self._abrir_dialogo_exportar("excel")

    def _exportar_pdf(self) -> None:
        self._abrir_dialogo_exportar("pdf")

    def _abrir_dialogo_exportar(self, formato: str) -> None:
        fecha = self.selector_fecha.date().toPyDate()
        filtros = {
            "supervisor_id": self.selector_supervisor.currentData() or None,
            "turno": (
                None
                if self.selector_turno.currentText() == "Todos"
                else self.selector_turno.currentText()
            ),
            "busqueda": self.buscador.text().strip(),
        }
        mostrar_dialogo_exportar(
            self,
            "detalle",
            fecha,
            fecha,
            crear_datos_para_exportar,
            COLUMNAS_DIARIAS,
            filtros_iniciales=filtros,
            objetivos=cargar_objetivos_reportables(),
            supervisores=cargar_supervisores(),
            equipos=cargar_equipos_reportables(),
            periodo_inicial="dia",
            formato_inicial=formato,
        )

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

        try:
            eliminadas = _eliminar_pasadas_por_fecha(fecha)
        except Exception as error:
            QMessageBox.critical(
                self,
                "No se borraron las pasadas",
                f"No se pudo crear la copia previa o completar el borrado:\n{error}",
            )
            return
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

        try:
            vista = _vista_previa_pasadas_mes(año, mes)
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo preparar la vista previa:\n{error}")
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación masiva",
            f"Se eliminarán {vista['cantidad']} pasadas de {mes_nombre} {año}.\n"
            f"Rango encontrado: {vista['fecha_desde'] or 'sin fechas'} a "
            f"{vista['fecha_hasta'] or 'sin fechas'}.\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        confirmacion, aceptada = QInputDialog.getText(
            self,
            "Confirmación requerida",
            f"Escribí {vista['mes']} para confirmar el borrado:",
        )
        if not aceptada or confirmacion != vista["mes"]:
            QMessageBox.warning(self, "Borrado cancelado", "La confirmación no coincide.")
            return

        try:
            eliminadas = _eliminar_pasadas_por_mes(año, mes, confirmacion)
        except Exception as error:
            QMessageBox.critical(
                self,
                "No se borraron las pasadas",
                f"No se pudo crear/verificar la copia previa o completar el borrado:\n{error}",
            )
            return
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