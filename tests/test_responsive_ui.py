"""Pruebas visuales de tamaño para las pantallas principales."""

import importlib
import os
import re
from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QWidget

from ui.theme.theme_manager import get_theme_manager


TAMANOS = ((1920, 1080), (1366, 768), (1024, 600))
TEMAS = ("Claro", "Verde", "Negro", "Grafito")
MODULOS_CON_DB_PATH = (
    "ui.ventana_principal",
    "ui.login",
    "ui.form_pasada",
    "ui.lista_pasadas",
    "ui.lista_supervisores",
    "ui.notas_diarias",
    "ui.tabla_diaria",
    "ui.vista_logs",
    "ui.reportes.reporte_mensual",
    "ui.reportes.reporte_objetivo",
)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_pantallas_se_adaptan_a_tamanos_y_temas(
    db_initialized, tmp_path, monkeypatch, app
):
    """Instancia las pantallas, cambia sus dimensiones y revisa widgets visibles."""
    from services.backups import backup
    from ui import configuracion, feriados, form_de_turno, form_objetivo
    from ui import form_pasada
    from ui import form_supervisor, gestionar_usuarios, lista_objetivos
    from ui import tabla_diaria, transferir_datos, vista_auditoria
    from ui import vista_indexacion, vista_sincronizacion
    from ui.importador import importar_excel
    from ui.reportes import reporte_mensual, reporte_objetivo
    from ui import ayuda, login, lista_pasadas
    from ui import lista_supervisores, notas_diarias, ventana_principal, vista_logs

    for nombre_modulo in MODULOS_CON_DB_PATH:
        modulo = importlib.import_module(nombre_modulo)
        monkeypatch.setattr(modulo, "DB_PATH", db_initialized)

    monkeypatch.setattr(backup, "listar_backups", lambda: [])
    monkeypatch.setattr(
        configuracion, "obtener_ruta_backup_externo", lambda: None
    )
    monkeypatch.setattr(gestionar_usuarios, "cargar_usuarios", lambda: [])
    monkeypatch.setattr(
        vista_indexacion.VistaIndexacion, "actualizar_datos", lambda self: None
    )
    monkeypatch.setattr(
        vista_sincronizacion.VistaSincronizacion,
        "actualizar_datos",
        lambda self: None,
    )

    theme_manager = get_theme_manager()
    original_theme = theme_manager.current()
    monkeypatch.setattr(theme_manager, "_config_file", tmp_path / "tema.json")
    formato_configuracion = QSettings.defaultFormat()
    ruta_configuracion = QSettings.path(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope
    )
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )

    pantallas = (
        ("Inicio", lambda: ventana_principal.VentanaPrincipal(rol="admin", app=app)),
        ("Login", lambda: login.LoginWindow(lambda *_: None)),
        ("Ayuda", ayuda.Ayuda),
        ("Configuracion", configuracion.ConfiguracionDialog),
        ("FormPasada", form_pasada.FormPasada),
        ("FormTurno", form_de_turno.FormTurno),
        ("FormObjetivo", form_objetivo.FormObjetivo),
        ("FormSupervisor", form_supervisor.FormSupervisor),
        ("ListaPasadas", lista_pasadas.ListaPasadas),
        ("ListaObjetivos", lista_objetivos.ListaObjetivos),
        ("ListaSupervisores", lista_supervisores.ListaSupervisores),
        ("ReporteMensual", reporte_mensual.ReporteMensual),
        ("ReporteObjetivo", reporte_objetivo.ReporteObjetivo),
        ("TablaDiaria", tabla_diaria.TablaDiaria),
        ("Feriados", feriados.VistaFeriados),
        ("Notas", notas_diarias.NotasDiarias),
        ("Auditoria", vista_auditoria.VistaAuditoria),
        ("Logs", vista_logs.VistaLogs),
        ("Indexacion", vista_indexacion.VistaIndexacion),
        ("Sincronizacion", vista_sincronizacion.VistaSincronizacion),
        ("TransferirDatos", transferir_datos.TransferirDatos),
        ("GestionarUsuarios", gestionar_usuarios.GestionarUsuarios),
        ("ImportarExcel", importar_excel.ImportarExcel),
    )

    capturar = os.environ.get("VESP_GENERAR_CAPTURAS_UI") == "1"
    ruta_capturas = Path(__file__).resolve().parents[1] / "docs" / "capturas_despues"
    if capturar:
        ruta_capturas.mkdir(parents=True, exist_ok=True)

    try:
        for nombre, crear in pantallas:
            pantalla = crear()
            try:
                for tema in TEMAS:
                    theme_manager.set_theme(tema)
                    for ancho, alto in TAMANOS:
                        if nombre != "Login":
                            pantalla.resize(ancho, alto)
                        pantalla.show()
                        app.processEvents()

                        assert pantalla.width() > 0 and pantalla.height() > 0
                        for widget in pantalla.findChildren(QWidget):
                            if widget.isVisible():
                                assert widget.width() > 0 and widget.height() > 0, (
                                    f"{nombre}/{tema}/{ancho}x{alto}: "
                                    f"{widget.objectName() or widget.__class__.__name__}"
                                )

                        if capturar:
                            nombre_seguro = re.sub(
                                r"[^a-zA-Z0-9_-]+", "-", nombre
                            ).strip("-")
                            ruta = ruta_capturas / (
                                f"{nombre_seguro}_{tema}_{ancho}x{alto}.png"
                            )
                            assert pantalla.grab().save(str(ruta)), (
                                f"No se pudo guardar la captura {ruta}"
                            )
            finally:
                pantalla.hide()
                pantalla.deleteLater()
                app.processEvents()
    finally:
        theme_manager.set_theme(original_theme)
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            ruta_configuracion,
        )
        QSettings.setDefaultFormat(formato_configuracion)
