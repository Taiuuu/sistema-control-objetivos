import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_HISTORY_PATH = Path.home() / "VESP Control" / "import_history.json"


def _obtener_ruta() -> Path:
    return DEFAULT_HISTORY_PATH


def _asegurar_directorio() -> None:
    _obtener_ruta().parent.mkdir(parents=True, exist_ok=True)


def obtener_historial() -> List[Dict[str, Any]]:
    ruta = _obtener_ruta()
    if not ruta.exists():
        return []

    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            if isinstance(datos, list):
                return datos
    except Exception:
        return []

    return []


def guardar_importacion(evento: Dict[str, Any]) -> List[Dict[str, Any]]:
    _asegurar_directorio()
    ruta = _obtener_ruta()

    historial = obtener_historial()
    evento_normalizado = {
        "timestamp": evento.get("timestamp"),
        "archivo": evento.get("archivo", ""),
        "importados": int(evento.get("importados", 0)),
        "duplicados": int(evento.get("duplicados", 0)),
        "errores": int(evento.get("errores", 0)),
        "estado": evento.get("estado", "ok"),
        "backup_file": evento.get("backup_file"),
    }

    historial.insert(0, evento_normalizado)
    historial = historial[:50]

    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, ensure_ascii=False, indent=2)

    return historial


def limpiar_historial() -> None:
    _asegurar_directorio()
    _obtener_ruta().write_text("[]", encoding="utf-8")
