"""Smoke test de imports, pantallas principales y rutas de la API."""

from __future__ import annotations

import importlib
import os
import re
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def _project_modules() -> list[str]:
    modules = []
    for package in (
        "api",
        "core",
        "database",
        "models",
        "scripts",
        "services",
        "ui",
    ):
        package_dir = PROJECT_ROOT / package
        for path in sorted(package_dir.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(PROJECT_ROOT).with_suffix("")
            parts = list(relative.parts)
            if parts[-1] == "__init__":
                parts.pop()
            modules.append(".".join(parts))
    return modules


def _exercise_api(app) -> None:
    client = app.test_client()
    failures = []
    for rule in app.url_map.iter_rules():
        path = rule.rule
        for converter, variable in re.findall(r"<(?:(\w+):)?(\w+)>", path):
            value = "1" if converter == "int" else "2026-01-01"
            path = path.replace(f"<{converter + ':' if converter else ''}{variable}>", value)
        method = "GET" if "GET" in rule.methods else "OPTIONS"
        response = client.open(path, method=method)
        if response.status_code >= 500:
            failures.append(f"{method} {path}: HTTP {response.status_code}")
    if failures:
        raise RuntimeError("Fallaron rutas de la API: " + "; ".join(failures))
    print(f"API: {len(list(app.url_map.iter_rules()))} rutas consultadas.")


def _exercise_screens() -> None:
    from PyQt6.QtCore import QThreadPool, QTimer
    from PyQt6.QtWidgets import QApplication, QMessageBox

    from ui.ayuda import Ayuda
    from ui.cambiar_password import CambiarPassword
    from ui.configuracion import ConfiguracionDialog
    from ui.feriados import VistaFeriados
    from ui.form_de_turno import FormTurno
    from ui.form_objetivo import FormObjetivo
    from ui.form_pasada import FormPasada
    from ui.form_supervisor import FormSupervisor
    from ui.gestionar_usuarios import GestionarUsuarios
    from ui.importador.importar_excel import ImportarExcel
    from ui.lista_objetivos import ListaObjetivos
    from ui.lista_pasadas import ListaPasadas
    from ui.lista_supervisores import ListaSupervisores
    from ui.login import LoginWindow
    from ui.notas_diarias import NotasDiarias
    from ui.reporte_mensual import ReporteMensual
    from ui.reporte_objetivo import ReporteObjetivo
    from ui.tabla_diaria import TablaDiaria
    from ui.transferir_datos import TransferirDatos
    from ui.ventana_principal import VentanaPrincipal
    from ui.vista_auditoria import VistaAuditoria
    from ui.vista_indexacion import VistaIndexacion
    from ui.vista_logs import VistaLogs
    from ui.vista_sincronizacion import VistaSincronizacion

    application = QApplication.instance() or QApplication([])
    screens = (
        ("LoginWindow", lambda: LoginWindow(lambda *_args: None)),
        ("CambiarPassword", lambda: CambiarPassword(1, lambda *_args: None)),
        (
            "VentanaPrincipal",
            lambda: VentanaPrincipal(1, "admin", lambda *_args: None, app=application),
        ),
        ("FormObjetivo", FormObjetivo),
        ("FormSupervisor", FormSupervisor),
        ("FormPasada", FormPasada),
        ("FormTurno", FormTurno),
        ("ListaObjetivos", ListaObjetivos),
        ("ListaSupervisores", ListaSupervisores),
        ("ListaPasadas", ListaPasadas),
        ("ReporteMensual", ReporteMensual),
        ("ReporteObjetivo", ReporteObjetivo),
        ("ImportarExcel", ImportarExcel),
        ("GestionarUsuarios", GestionarUsuarios),
        ("NotasDiarias", NotasDiarias),
        ("TablaDiaria", TablaDiaria),
        ("VistaFeriados", VistaFeriados),
        ("Ayuda", Ayuda),
        ("TransferirDatos", TransferirDatos),
        ("VistaAuditoria", VistaAuditoria),
        ("VistaIndexacion", VistaIndexacion),
        ("VistaLogs", VistaLogs),
        ("VistaSincronizacion", VistaSincronizacion),
        ("ConfiguracionDialog", ConfiguracionDialog),
    )
    modal_errors = []
    failures = []
    for name, factory in screens:
        print(f"Qt: probando {name}.", flush=True)
        widget = None
        modal_timer = QTimer()

        def process_modal():
            modal = application.activeModalWidget()
            if not isinstance(modal, QMessageBox):
                return
            if name == "VentanaPrincipal" and modal.windowTitle() == "Confirmar salida":
                boton = modal.button(QMessageBox.StandardButton.Yes)
                if boton is not None:
                    boton.click()
                return
            modal_errors.append(
                f"{name}: {modal.windowTitle()} - {modal.text()}"
            )
            modal.reject()

        modal_timer.timeout.connect(process_modal)
        modal_timer.start(10)
        try:
            widget = factory()
            widget.close()
            widget.deleteLater()
            application.processEvents()
        except Exception as error:
            failures.append(f"{name}: {type(error).__name__}: {error}")
            if widget is not None:
                widget.close()
                widget.deleteLater()
        finally:
            modal_timer.stop()
    application.processEvents()
    failures.extend(f"Modal inesperado: {message}" for message in modal_errors)
    if not QThreadPool.globalInstance().waitForDone(5000):
        failures.append("Quedaron tareas Qt en segundo plano sin finalizar.")
    if failures:
        raise RuntimeError("Fallaron pantallas: " + "; ".join(failures))
    print(f"Qt: {len(screens)} pantallas instanciadas y cerradas.", flush=True)


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory(prefix="vesp-verificar-") as temporary:
        temp_path = Path(temporary)
        os.environ.update(
            {
                "QT_QPA_PLATFORM": "offscreen",
                "VESP_DB_PATH": str(temp_path / "seguridad.db"),
                "VESP_JWT_SECRET": "verificador-jwt-temporal-no-usar",
                "VESP_ENCRYPTION_KEY": "verificador-encryption-temporal-no-usar",
                "VESP_SSE_PUBLISH_TOKEN": "verificador-sse-temporal-no-usar",
                "VESP_RATE_LIMIT_STORAGE_URI": "memory://",
                "VESP_REDIS_URL": "redis://127.0.0.1:1/0",
                "USERPROFILE": temporary,
                "HOME": temporary,
            }
        )

        modules = _project_modules()
        for module_name in modules:
            try:
                importlib.import_module(module_name)
            except Exception as error:
                failures.append(
                    f"Import {module_name}: {type(error).__name__}: {error}"
                )
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}", file=sys.stderr)
            return 1
        print(f"Imports: {len(modules)} modulos cargados.", flush=True)

        from database import db

        try:
            db.crear_base_datos()
            db.migrar_supervisor3()
            db.migrar_supervisores_alta_baja()
            db.migrar_usuarios_activo()
            db.migrar_feriados()
            _exercise_screens()
            from api.app import app

            app.config.update(TESTING=True, REDIS_URL="redis://127.0.0.1:1/0")
            _exercise_api(app)
        except Exception as error:
            print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
            return 1
        finally:
            db.cerrar_todas_las_conexiones()
    print("Verificación de estructura completa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
