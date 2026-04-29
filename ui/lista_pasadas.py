# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado, edición y eliminación de pasadas registradas
# =============================================================================

import sqlite3

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QDateEdit, QTimeEdit, QComboBox, QMessageBox, QDialog
)
from PyQt6.QtCore import QDate, QTime

from database.db import DB_PATH
from services.sincronizacion import obtener_sincronizador


# =============================================================================
# FUNCIONES DB
# =============================================================================

def _cargar_pasadas(fecha: str) -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("""
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
        ORDER BY p.hora
    """, (fecha,))

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
    supervisor_id: int
) -> None:

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

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

        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        _actualizar_pasada(
            self.pasada_id,
            hora,
            turno,
            objetivo_id,
            supervisor_id
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

        # Filtros
        fila = QHBoxLayout()

        fila.addWidget(QLabel("Fecha:"))

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.setDate(QDate.currentDate())

        fila.addWidget(self.selector_fecha)

        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self._cargar_tabla)

        fila.addWidget(btn_buscar)
        fila.addStretch()

        layout.addLayout(fila)

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

        layout.addWidget(self.tabla)

        self.setLayout(layout)

        self._cargar_tabla()

        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(
            self._on_datos_cambiados
        )

    def _cargar_tabla(self):

        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        datos = _cargar_pasadas(fecha)

        self.tabla.setRowCount(len(datos))

        for fila, item in enumerate(datos):

            pasada_id = item[0]

            self.tabla.setItem(fila, 0, QTableWidgetItem(item[1]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item[2]))
            self.tabla.setItem(fila, 2, QTableWidgetItem(item[3]))
            self.tabla.setItem(fila, 3, QTableWidgetItem(item[4]))

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