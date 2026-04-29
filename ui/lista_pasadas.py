# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado, edición y eliminación de pasadas registradas
# =============================================================================

<<<<<<< HEAD
import sqlite3
=======
import logging
>>>>>>> 61b5766 (arreglando varios errores de la app, poco a poco, olvide ir commiteando el proceso pero como avance mucho durante el mediodia y tarde lo pongo. Errores del tipo anote mañana tarde noche en vez de diurno nocturno, algunas funciones duplicadas, etc.)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QDateEdit, QTimeEdit, QComboBox, QMessageBox, QDialog
)
from PyQt6.QtCore import QDate, QTime
<<<<<<< HEAD
from database.db import DB_PATH
from services.sincronizacion import obtener_sincronizador


def _cargar_pasadas(fecha: str) -> list:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.id, p.hora, p.turno, o.nombre, s.nombre, p.objetivo_id, p.supervisor_id
=======
from database.gestor_db import gestor_db
from services.sincronizacion import obtener_sincronizador

logger = logging.getLogger("lista_pasadas")
logger.setLevel(logging.DEBUG)


# =============================================================================
# HELPERS
# =============================================================================

def _valor(fila, indice=None, clave=None, default=""):
    """
    Compatible con tuple/list/dict/sqlite.Row
    """
    try:
        if clave is not None:
            return fila[clave]
    except Exception:
        pass

    try:
        if indice is not None:
            return fila[indice]
    except Exception:
        pass

    return default


# =============================================================================
# CONSULTAS
# =============================================================================

def _cargar_pasadas(fecha: str):
    logger.debug(f"Cargando pasadas para fecha {fecha}")

    return gestor_db.ejecutar("""
        SELECT
            p.id,
            p.hora,
            p.turno,
            o.nombre AS objetivo,
            s.nombre AS supervisor,
            p.objetivo_id,
            p.supervisor_id
>>>>>>> 61b5766 (arreglando varios errores de la app, poco a poco, olvide ir commiteando el proceso pero como avance mucho durante el mediodia y tarde lo pongo. Errores del tipo anote mañana tarde noche en vez de diurno nocturno, algunas funciones duplicadas, etc.)
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha = ?
        ORDER BY p.hora
    """, (fecha,))
<<<<<<< HEAD
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
=======


def _eliminar_pasada(pasada_id: int):
    gestor_db.ejecutar(
        "DELETE FROM pasadas WHERE id = ?",
        (pasada_id,),
        commit=True
    )


def _obtener_info_pasada(pasada_id: int):
    return gestor_db.ejecutar("""
        SELECT
            p.id,
            p.fecha,
            p.hora,
            p.turno,
            p.objetivo_id,
            p.supervisor_id,
            o.nombre,
            s.nombre
>>>>>>> 61b5766 (arreglando varios errores de la app, poco a poco, olvide ir commiteando el proceso pero como avance mucho durante el mediodia y tarde lo pongo. Errores del tipo anote mañana tarde noche en vez de diurno nocturno, algunas funciones duplicadas, etc.)
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.id = ?
<<<<<<< HEAD
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
=======
    """, (pasada_id,), unico=True)


def _actualizar_pasada(pasada_id, hora, turno, objetivo_id, supervisor_id):
    gestor_db.ejecutar("""
        UPDATE pasadas
        SET hora = ?, turno = ?, objetivo_id = ?, supervisor_id = ?
        WHERE id = ?
    """, (hora, turno, objetivo_id, supervisor_id, pasada_id), commit=True)


def _cargar_objetivos():
    return gestor_db.ejecutar(
        "SELECT id, nombre FROM objetivos ORDER BY nombre"
    )


def _cargar_supervisores():
    return gestor_db.ejecutar(
        "SELECT id, nombre FROM supervisores ORDER BY nombre"
    )
>>>>>>> 61b5766 (arreglando varios errores de la app, poco a poco, olvide ir commiteando el proceso pero como avance mucho durante el mediodia y tarde lo pongo. Errores del tipo anote mañana tarde noche en vez de diurno nocturno, algunas funciones duplicadas, etc.)


# =============================================================================
# DIALOGO EDITAR
# =============================================================================

class DialogoEditarPasada(QDialog):

    def __init__(self, pasada_id, parent=None):
        super().__init__(parent)

        self.pasada_id = pasada_id
        self.setWindowTitle("Editar pasada")
        self.setFixedSize(360, 280)

        info = _obtener_info_pasada(pasada_id)
        if not info:
            self.reject()
            return

        fecha = _valor(info, 1)
        hora = _valor(info, 2)
        turno = _valor(info, 3)
        objetivo_id = _valor(info, 4)
        supervisor_id = _valor(info, 5)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Hora"))
        self.input_hora = QTimeEdit()
        self.input_hora.setDisplayFormat("HH:mm")
        self.input_hora.setTime(QTime.fromString(hora, "HH:mm"))
        layout.addWidget(self.input_hora)

        layout.addWidget(QLabel("Turno"))
        self.input_turno = QComboBox()
        self.input_turno.addItems(["diurno", "nocturno"])
        self.input_turno.setCurrentText(turno)
        layout.addWidget(self.input_turno)

        layout.addWidget(QLabel("Objetivo"))
        self.input_objetivo = QComboBox()
        for fila in _cargar_objetivos():
            oid = _valor(fila, 0)
            nombre = _valor(fila, 1)
            self.input_objetivo.addItem(nombre, oid)
            if oid == objetivo_id:
                self.input_objetivo.setCurrentIndex(
                    self.input_objetivo.count() - 1
                )
        layout.addWidget(self.input_objetivo)

        layout.addWidget(QLabel("Supervisor"))
        self.input_supervisor = QComboBox()
        for fila in _cargar_supervisores():
            sid = _valor(fila, 0)
            nombre = _valor(fila, 1)
            self.input_supervisor.addItem(nombre, sid)
            if sid == supervisor_id:
                self.input_supervisor.setCurrentIndex(
                    self.input_supervisor.count() - 1
                )
        layout.addWidget(self.input_supervisor)

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

        _actualizar_pasada(
            self.pasada_id,
            hora,
            turno,
            objetivo_id,
            supervisor_id
        )

        QMessageBox.information(
            self,
            "Correcto",
            "Pasada actualizada correctamente."
        )
        self.accept()


# =============================================================================
# VISTA PRINCIPAL
# =============================================================================

class ListaPasadas(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lista de Pasadas")
        self.setGeometry(200, 200, 850, 420)

        layout = QVBoxLayout()

        fila = QHBoxLayout()

        self.selector_fecha = QDateEdit()
        self.selector_fecha.setCalendarPopup(True)
        self.selector_fecha.setDate(QDate.currentDate())

        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self._cargar_tabla)

        fila.addWidget(QLabel("Fecha"))
        fila.addWidget(self.selector_fecha)
        fila.addWidget(btn_buscar)
        fila.addStretch()

        layout.addLayout(fila)

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
        self.tabla.setColumnWidth(2, 260)
        self.tabla.setColumnWidth(3, 220)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.setColumnWidth(5, 90)

        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(
            self._on_datos_cambiados
        )

        self._cargar_tabla()

    # =========================================================================

    def _cargar_tabla(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        pasadas = _cargar_pasadas(fecha)

        self.tabla.setRowCount(0)
        self.tabla.setRowCount(len(pasadas))

        for i, p in enumerate(pasadas):

            pasada_id = _valor(p, 0, "id")
            hora = _valor(p, 1, "hora")
            turno = _valor(p, 2, "turno")
            objetivo = _valor(p, 3, "objetivo")
            supervisor = _valor(p, 4, "supervisor")

            self.tabla.setItem(i, 0, QTableWidgetItem(str(hora)))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(turno)))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(objetivo)))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(supervisor)))

            btn_editar = QPushButton("Editar")
            btn_editar.clicked.connect(
                lambda checked=False, pid=pasada_id: self._editar(pid)
            )
            self.tabla.setCellWidget(i, 4, btn_editar)

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.clicked.connect(
                lambda checked=False, pid=pasada_id: self._eliminar(pid)
            )
            self.tabla.setCellWidget(i, 5, btn_eliminar)

    # =========================================================================

    def _editar(self, pasada_id):
        dlg = DialogoEditarPasada(pasada_id, self)
        if dlg.exec():
            self._cargar_tabla()

    def _eliminar(self, pasada_id):
        confirmar = QMessageBox.question(
            self,
            "Confirmar",
            "¿Eliminar pasada?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if confirmar == QMessageBox.StandardButton.Yes:
            _eliminar_pasada(pasada_id)
            self._cargar_tabla()

    def _on_datos_cambiados(self, tabla, operacion, datos):
        if tabla in ("pasadas", "objetivos", "supervisores"):
            self._cargar_tabla()