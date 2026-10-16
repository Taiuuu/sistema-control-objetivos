import pytest
import sqlite3
from types import SimpleNamespace
from PyQt6.QtWidgets import QApplication

from services.cache import invalidar_supervisores


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_lista_pasadas_abre_con_base_vacia(db_initialized, monkeypatch, app):
    from ui import lista_pasadas

    monkeypatch.setattr(lista_pasadas, "DB_PATH", db_initialized)

    ventana = lista_pasadas.ListaPasadas()
    try:
        assert ventana.tabla.rowCount() == 0
    finally:
        ventana.close()


def test_form_pasada_explica_por_que_no_hay_opciones(
    db_initialized, monkeypatch, app
):
    from ui import form_pasada

    monkeypatch.setattr(form_pasada, "DB_PATH", db_initialized)

    ventana = form_pasada.FormPasada()
    try:
        assert ventana.input_objetivo.itemText(0) == (
            "No hay objetivos activos en esta fecha"
        )
        assert ventana.input_supervisor.itemText(0) == (
            "Registrá primero el equipo de este turno"
        )
    finally:
        ventana.close()


def test_form_turno_explica_si_faltan_supervisores(db_initialized, app):
    from ui.form_de_turno import FormTurno

    invalidar_supervisores()
    ventana = FormTurno()
    try:
        assert not ventana.boton_guardar.isEnabled()
        assert ventana.input_sup1.itemText(0) == (
            "No hay supervisores para seleccionar"
        )
    finally:
        ventana.close()
        invalidar_supervisores()


def test_form_turno_preselecciona_supervisores_distintos(
    db_initialized, monkeypatch, app
):
    from ui import form_de_turno

    conexion = sqlite3.connect(db_initialized)
    conexion.executemany(
        "INSERT INTO supervisores (nombre, fecha_alta) VALUES (?, ?)",
        [("Supervisor A", "2026-01-01"), ("Supervisor B", "2026-01-01")],
    )
    conexion.commit()
    conexion.close()

    invalidar_supervisores()
    guardado = []
    monkeypatch.setattr(
        form_de_turno,
        "guardar_equipo_turno",
        lambda *args: guardado.append(args),
    )
    monkeypatch.setattr(
        form_de_turno,
        "QMessageBox",
        SimpleNamespace(information=lambda *args: None),
    )

    ventana = form_de_turno.FormTurno()
    cambios = []
    ventana.turno_registrado.connect(lambda: cambios.append(True))
    try:
        assert ventana.input_sup1.currentData() != ventana.input_sup2.currentData()

        ventana._guardar()

        assert len(guardado) == 1
        assert cambios == [True]
    finally:
        ventana.close()
        invalidar_supervisores()
