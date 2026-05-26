import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import import_history


def test_guardar_importacion_persiste_historial(tmp_path, monkeypatch):
    ruta = tmp_path / "import_history.json"
    monkeypatch.setattr(import_history, "DEFAULT_HISTORY_PATH", ruta)

    historial = import_history.guardar_importacion(
        {
            "timestamp": "2026-05-26T10:00:00",
            "archivo": "CONTROL RECORRIDOS.xlsx",
            "importados": 3,
            "duplicados": 1,
            "errores": 0,
            "estado": "ok",
            "backup_file": "seguridad_test.db",
        }
    )

    assert historial[0]["archivo"] == "CONTROL RECORRIDOS.xlsx"
    assert historial[0]["importados"] == 3
    assert historial[0]["duplicados"] == 1
    assert historial[0]["backup_file"] == "seguridad_test.db"

    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    assert contenido[0]["estado"] == "ok"


def test_obtener_historial_devuelve_vacio_si_no_existe(tmp_path, monkeypatch):
    ruta = tmp_path / "import_history.json"
    monkeypatch.setattr(import_history, "DEFAULT_HISTORY_PATH", ruta)

    assert import_history.obtener_historial() == []
