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


def _cargar_pasadas(fecha: str) -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre, p.objetivo_id, p.supervisor_id
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    """, (fecha,))
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _eliminar_pasada(pasada_id: int) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM pasadas WHERE id = ?", (pasada_id,))
    conexion.commit()
    conexion.close()


def _obtener_info_pasada(pasada_id: int) -> tuple | None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.id, p.fecha, p.hora, p.turno, p.objetivo_id, p.supervisor_id,
               o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.id = ?
    """, (pasada_id,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def _actualizar_pasada(pasada_id: int, hora: str, turno: str,
                        objetivo_id: int, supervisor_id: int) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE pasadas SET hora = ?, turno = ?, objetivo_id = ?, supervisor_id = ?
        WHERE id = ?
    """, (hora, turno, objetivo_id, supervisor_id, pasada_id))
    conexion.commit()
    conexion.close()


def _cargar_objetivos() -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM objetivos")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def _cargar_supervisores() -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM supervisores")
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


class DialogoEditarPasada(QDialog):

    def __init__(self, pasada_id: int, parent=None):
        super().__init__(parent)
        self.pasada_id = pasada_id
        self.setWindowTitle("Editar pasada")
        self.setFixedSize(350, 280)

        info = _obtener_info_pasada(pasada_id)
        if not info:
            self.close()
            return

        _, fecha, hora, turno, objetivo_id, supervisor_id, _, _ = info

        layout = QVBoxLayout()

        # Hora
        layout.addWidget(QLabel("Hora:"))
        self.input_hora = QTimeEdit()
        try:
            self.input_hora.setTime(QTime.fromString(hora, "HH:mm"))
        except Exception:
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
        for o in _cargar_objetivos():
            self.input_objetivo.addItem(o[1], o[0])
            if o[0] == objetivo_id:
                self.input_objetivo.setCurrentIndex(self.input_objetivo.count() - 1)
        layout.addWidget(self.input_objetivo)

        # Supervisor
        layout.addWidget(QLabel("Supervisor:"))
        self.input_supervisor = QComboBox()
        for s in _cargar_supervisores():
            self.input_supervisor.addItem(s[1], s[0])
            if s[0] == supervisor_id:
                self.input_supervisor.setCurrentIndex(self.input_supervisor.count() - 1)
        layout.addWidget(self.input_supervisor)

        # Botones
        fila_botones = QHBoxLayout()
        boton_guardar = QPushButton("Guardar cambios")
        boton_guardar.clicked.connect(self._guardar)
        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.clicked.connect(self.reject)
        fila_botones.addWidget(boton_guardar)
        fila_botones.addWidget(boton_cancelar)
        layout.addLayout(fila_botones)

        self.setLayout(layout)

    def _guardar(self) -> None:
        hora = self.input_hora.time().toString("HH:mm")
        turno = self.input_turno.currentText()
        objetivo_id = self.input_objetivo.currentData()
        supervisor_id = self.input_supervisor.currentData()
        objetivo_nombre = self.input_objetivo.currentText()
        supervisor_nombre = self.input_supervisor.currentText()

        _actualizar_pasada(self.pasada_id, hora, turno, objetivo_id, supervisor_id)

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(
            get_usuario_id(),
            f"Editó pasada id={self.pasada_id} - Hora: {hora} | Turno: {turno} | "
            f"Objetivo: {objetivo_nombre} | Supervisor: {supervisor_nombre}"
        )

        QMessageBox.information(self, "Listo", "Pasada actualizada correctamente.")
        self.accept()


class ListaPasadas(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pasadas del día")
        self.setGeometry(200, 200, 800, 400)

        layout = QVBoxLayout()

        fila = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self._cargar_tabla)
        fila.addWidget(QLabel("Fecha:"))
        fila.addWidget(self.selector_fecha)
        fila.addWidget(boton_buscar)
        fila.addStretch()
        layout.addLayout(fila)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Hora", "Turno", "Objetivo", "Supervisor", "Editar", "Eliminar"
        ])
        self.tabla.setColumnWidth(0, 80)
        self.tabla.setColumnWidth(1, 90)
        self.tabla.setColumnWidth(2, 200)
        self.tabla.setColumnWidth(3, 150)
        self.tabla.setColumnWidth(4, 100)
        self.tabla.setColumnWidth(5, 100)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self._cargar_tabla()

        # Conectar señales de sincronización
        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(self._on_datos_cambiados)

    def _cargar_tabla(self) -> None:
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        pasadas = _cargar_pasadas(fecha)

        self.tabla.setRowCount(len(pasadas))
        for i, p in enumerate(pasadas):
            self.tabla.setItem(i, 0, QTableWidgetItem(p[1]))
            self.tabla.setItem(i, 1, QTableWidgetItem(p[2]))
            self.tabla.setItem(i, 2, QTableWidgetItem(p[3]))
            self.tabla.setItem(i, 3, QTableWidgetItem(p[4]))

            boton_editar = QPushButton("Editar")
            boton_editar.clicked.connect(lambda checked, pid=p[0]: self._editar(pid))
            self.tabla.setCellWidget(i, 4, boton_editar)

            boton_eliminar = QPushButton("Eliminar")
            boton_eliminar.clicked.connect(lambda checked, pid=p[0]: self._eliminar(pid))
            self.tabla.setCellWidget(i, 5, boton_eliminar)

    def _editar(self, pasada_id: int) -> None:
        self.dialogo_edicion = DialogoEditarPasada(pasada_id, self)
        if self.dialogo_edicion.exec():
            self._cargar_tabla()

    def _eliminar(self, pasada_id: int) -> None:
        confirmar = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que querés eliminar esta pasada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            from services.logger import registrar_accion
            from services.sesion import get_usuario_id

            info = _obtener_info_pasada(pasada_id)
            _eliminar_pasada(pasada_id)

            if info:
                registrar_accion(
                    get_usuario_id(),
                    f"Eliminó pasada - Fecha: {info[1]} | Hora: {info[2]} | "
                    f"Turno: {info[3]} | Objetivo: {info[6]} | Supervisor: {info[7]}"
                )

            self._cargar_tabla()
    def _on_datos_cambiados(self, tabla, operacion, datos):
        """Maneja cambios de datos para refrescar la tabla."""
        if tabla in ["pasadas", "objetivos", "supervisores"]:
            self._cargar_tabla()