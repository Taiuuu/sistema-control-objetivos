"""Pruebas visuales de tamaño para las pantallas y diálogos principales."""

import importlib
import os
import re
from pathlib import Path
from datetime import date

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
    from models.types import Objetivo
    from ui import cambiar_password, configuracion, feriados, form_de_turno, form_objetivo
    from ui import form_pasada
    from ui import form_supervisor, gestionar_usuarios, lista_objetivos
    from ui import tabla_diaria, transferir_datos, vista_auditoria
    from ui import vista_indexacion, vista_sincronizacion
    from ui.importador import importar_excel
    from ui.reportes import dialogo_exportar, reporte_mensual, reporte_objetivo
    from ui.widgets import dialogos
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
        lista_pasadas,
        "_obtener_info_pasada",
        lambda _id: (1, "2026-09-01", "10:00", "diurno", 1, 1, None, None),
    )
    monkeypatch.setattr(lista_pasadas, "_cargar_objetivos", lambda: [(1, "Objetivo")])
    monkeypatch.setattr(
        lista_pasadas, "_cargar_supervisores", lambda: [(1, "Supervisor")]
    )
    monkeypatch.setattr(dialogo_exportar, "tiene_permiso", lambda _permiso: True)
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
        (
            "CambioPassword",
            lambda: cambiar_password.CambiarPassword(1, lambda: None),
        ),
        ("Ayuda", ayuda.Ayuda),
        ("Configuracion", configuracion.ConfiguracionDialog),
        ("FormPasada", form_pasada.FormPasada),
        ("FormTurno", form_de_turno.FormTurno),
        ("FormObjetivo", form_objetivo.FormObjetivo),
        ("FormSupervisor", form_supervisor.FormSupervisor),
        ("ListaPasadas", lista_pasadas.ListaPasadas),
        ("ListaObjetivos", lista_objetivos.ListaObjetivos),
        ("ListaSupervisores", lista_supervisores.ListaSupervisores),
        (
            "EditarObjetivo",
            lambda: lista_objetivos.DialogoEditarObjetivo(
                Objetivo(
                    nombre="Objetivo de prueba",
                    fecha_inicio="2026-09-01",
                    dias_semana="1",
                    id=1,
                )
            ),
        ),
        (
            "EditarSupervisor",
            lambda: lista_supervisores.DialogoEditarSupervisor(
                1, "Supervisor de prueba", "2026-09-01", None
            ),
        ),
        ("EditarPasada", lambda: lista_pasadas.DialogoEditarPasada(1)),
        ("ReporteMensual", reporte_mensual.ReporteMensual),
        ("ReporteObjetivo", reporte_objetivo.ReporteObjetivo),
        (
            "Exportar",
            lambda: dialogo_exportar.DialogoExportar(
                "mensual", date.today(), date.today()
            ),
        ),
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
        (
            "ResolverCoincidencias",
            lambda: importar_excel.DialogoResolverCoincidencias(
                "Resolver objetivos", [], []
            ),
        ),
        (
            "DialogoMensaje",
            lambda: dialogos.DialogoMensaje("Aviso", "Mensaje de prueba"),
        ),
    )
    assert len(pantallas) == 30

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
