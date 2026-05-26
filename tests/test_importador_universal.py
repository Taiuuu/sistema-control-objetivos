import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.importador_universal import ImportadorUniversal


def test_parsear_nombre_sheet_acepta_barra():
    importador = ImportadorUniversal()

    resultado = importador._parsear_nombre_sheet("27/5 (D)")

    assert resultado == (date.today().replace(month=5, day=27), "diurno")


def test_parsear_hoja_control_recorridos_limpia_texto():
    importador = ImportadorUniversal()
    wb = Workbook()
    ws = wb.active
    ws.title = "27-5 (D)"

    ws["A1"] = "Objetivo"
    ws["B1"] = "Supervisor"
    ws["C1"] = "Hora"
    ws["D1"] = "Veces"
    ws["E1"] = "Notas"

    ws["A2"] = "Revisar\nplaca"
    ws["B2"] = "Juan   Perez"
    ws["C2"] = "08:30"
    ws["D2"] = "1"
    ws["E2"] = "sin observaciones"

    registros = importador._parsear_hoja_control_recorridos(ws, date(2026, 5, 27), "diurno")

    assert len(registros) == 1
    assert registros[0].objetivo == "Revisar placa"
    assert registros[0].supervisor == "Juan Perez"
    assert registros[0].notas == "sin observaciones"


def test_crear_pasada_offline_calcula_fecha_operativa(monkeypatch):
    import services.sync_manager as sync_module

    captured = {}

    class DummyProvider:
        def crear_pasada(self, pasada):
            captured["fecha_operativa"] = pasada.fecha_operativa
            return True

    def fake_agregar_cambio_pendiente(self, tipo, operacion, datos):
        captured["cambio"] = {
            "tipo": tipo,
            "operacion": operacion,
            "datos": datos,
        }

    monkeypatch.setattr(sync_module, "get_data_provider", lambda: DummyProvider())
    monkeypatch.setattr(sync_module.SyncManager, "_guardar_cambios_pendientes", lambda self: None)
    monkeypatch.setattr(sync_module.SyncManager, "_cargar_cambios_pendientes", lambda self: None)

    manager = sync_module.SyncManager.__new__(sync_module.SyncManager)
    manager.cambios_pendientes = []
    manager.agregar_cambio_pendiente = fake_agregar_cambio_pendiente.__get__(manager, sync_module.SyncManager)

    resultado = manager.crear_pasada_offline(
        fecha="2026-05-26",
        hora="03:00",
        turno="nocturno",
        supervisor_id=7,
        objetivo_id=9,
        notas="prueba",
    )

    assert resultado is True
    assert captured["fecha_operativa"] == "2026-05-25"
    assert captured["cambio"]["datos"]["fecha_operativa"] == "2026-05-25"


def test_procesar_registros_control_recorridos_acepta_horas_fuera_de_rango(monkeypatch):
    import services.sync_manager as sync_module
    from services.importador_universal import RegistroImportacion

    importador = ImportadorUniversal()
    importador.sync_manager = sync_module.get_sync_manager()

    class DummyProvider:
        def crear_pasada(self, pasada):
            return True

    class DummySyncManager:
        def agregar_cambio_pendiente(self, *args, **kwargs):
            return None

        def crear_pasada_offline(self, *args, **kwargs):
            return True

    monkeypatch.setattr(sync_module, "get_data_provider", lambda: DummyProvider())
    monkeypatch.setattr(sync_module.SyncManager, "_guardar_cambios_pendientes", lambda self: None)
    monkeypatch.setattr(sync_module.SyncManager, "_cargar_cambios_pendientes", lambda self: None)
    monkeypatch.setattr(importador, "_obtener_supervisor_id", lambda nombre: 7)
    monkeypatch.setattr(importador, "_obtener_objetivo_id", lambda nombre: 9)
    monkeypatch.setattr(importador, "sync_manager", DummySyncManager())
    monkeypatch.setattr("services.gestor_turnos.GestorTurnos.calcular_fecha_operativa", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("Hora fuera del rango")))

    registros = [
        RegistroImportacion(
            fecha="2026-05-27",
            hora="03:11",
            turno="diurno",
            supervisor="Supervisor test",
            objetivo="Objetivo test",
            notas="prueba",
            fuente="excel",
            sheet_title="27-5 (D)",
        )
    ]

    resultado = importador._procesar_registros(registros)

    assert resultado.registros_validos == 1
    assert resultado.registros_errores == 0
    assert resultado.exitoso is True


def test_no_agrega_objetivos_faltantes(monkeypatch):
    import services.sync_manager as sync_module
    from services.importador_universal import RegistroImportacion

    importador = ImportadorUniversal()
    importador.sync_manager = sync_module.get_sync_manager()

    class DummyProvider:
        def crear_pasada(self, pasada):
            return True

    class DummySyncManager:
        def agregar_cambio_pendiente(self, *args, **kwargs):
            return None

        def crear_pasada_offline(self, *args, **kwargs):
            return True

    monkeypatch.setattr(sync_module, "get_data_provider", lambda: DummyProvider())
    monkeypatch.setattr(sync_module.SyncManager, "_guardar_cambios_pendientes", lambda self: None)
    monkeypatch.setattr(sync_module.SyncManager, "_cargar_cambios_pendientes", lambda self: None)
    monkeypatch.setattr(importador, "_obtener_supervisor_id", lambda nombre: 7)
    monkeypatch.setattr(importador, "_obtener_objetivo_id", lambda nombre: None)
    monkeypatch.setattr(importador, "sync_manager", DummySyncManager())

    registros = [
        RegistroImportacion(
            fecha="2026-05-27",
            hora="08:30",
            turno="diurno",
            supervisor="Supervisor test",
            objetivo="OBJETIVO INEXISTENTE",
            notas="prueba",
            fuente="excel",
            sheet_title="27-5 (D)",
        )
    ]

    resultado = importador._procesar_registros(registros)

    assert resultado.registros_validos == 0
    assert resultado.registros_errores == 1
    assert "Objetivo no encontrado" in resultado.errores[0]
    assert resultado.exitoso is False
