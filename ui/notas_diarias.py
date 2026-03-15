from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTextEdit, QListWidget, QMessageBox
)
from PyQt6.QtCore import QDate
import sqlite3


def cargar_notas(fecha):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nota FROM notas WHERE fecha = ?', (fecha,))
    resultado = cursor.fetchall()
    conexion.close()
    return resultado


def guardar_nota(fecha, nota):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO notas (fecha, nota) VALUES (?, ?)', (fecha, nota))
    conexion.commit()
    conexion.close()


def eliminar_nota(nota_id):
    conexion = sqlite3.connect('seguridad.db')
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM notas WHERE id = ?', (nota_id,))
    conexion.commit()
    conexion.close()


class NotasDiarias(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notas del día")
        self.setGeometry(300, 300, 500, 450)

        layout = QVBoxLayout()

        # Selector de fecha
        fila = QHBoxLayout()
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.cargar_lista)
        fila.addWidget(QLabel("Fecha:"))
        fila.addWidget(self.selector_fecha)
        fila.addWidget(boton_buscar)
        fila.addStretch()
        layout.addLayout(fila)

        # Lista de notas
        layout.addWidget(QLabel("Notas del día:"))
        self.lista_notas = QListWidget()
        layout.addWidget(self.lista_notas)

        # Boton eliminar
        boton_eliminar = QPushButton("Eliminar nota seleccionada")
        boton_eliminar.clicked.connect(self.eliminar_seleccionada)
        layout.addWidget(boton_eliminar)

        # Escribir nueva nota
        layout.addWidget(QLabel("Nueva nota:"))
        self.input_nota = QTextEdit()
        self.input_nota.setFixedHeight(80)
        layout.addWidget(self.input_nota)

        boton_guardar = QPushButton("Guardar nota")
        boton_guardar.clicked.connect(self.guardar)
        layout.addWidget(boton_guardar)

        self.setLayout(layout)
        self.notas_ids = []
        self.cargar_lista()

    def cargar_lista(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        notas = cargar_notas(fecha)

        self.lista_notas.clear()
        self.notas_ids = []

        for n in notas:
            self.lista_notas.addItem(n[1])
            self.notas_ids.append(n[0])

    def guardar(self):
        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        nota = self.input_nota.toPlainText().strip()

        if not nota:
            QMessageBox.warning(self, "Error", "La nota no puede estar vacía.")
            return

        guardar_nota(fecha, nota)
        self.input_nota.clear()
        self.cargar_lista()

    def eliminar_seleccionada(self):
        fila = self.lista_notas.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccioná una nota para eliminar.")
            return

        confirmar = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que querés eliminar esta nota?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            eliminar_nota(self.notas_ids[fila])
            self.cargar_lista()