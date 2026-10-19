import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "rutas_viejas.txt"
HISTORICAL_FILES = {
    "docs/estructura_antes.md",
    "docs/reorganizacion_inventario.md",
    "docs/reorganizacion_plan.md",
    "tests/rutas_viejas.txt",
}
TEXT_SUFFIXES = {
    ".bat",
    ".ini",
    ".iss",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".qss",
    ".spec",
    ".txt",
    ".yaml",
    ".yml",
}


def _manifest() -> tuple[list[str], list[str]]:
    paths = []
    modules = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        kind, value = line.split(":", 1)
        if kind == "path":
            paths.append(value.strip())
        elif kind == "module":
            modules.append(value.strip())
        else:
            raise AssertionError(f"Tipo de ruta vieja desconocido: {kind}")
    return paths, modules


def _text_files():
    excluded_parts = {".git", ".pytest_cache", "__pycache__", ".venv", "venv"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in HISTORICAL_FILES:
            continue
        if excluded_parts.intersection(path.relative_to(ROOT).parts):
            continue
        yield path, relative


def test_no_existen_las_rutas_fisicas_anteriores():
    paths, _ = _manifest()
    existentes = [route for route in paths if (ROOT / route).exists()]
    assert not existentes, existentes


def test_no_hay_referencias_activas_a_modulos_anteriores():
    _, modules = _manifest()
    archivos = list(_text_files())
    encontrados = []
    for module in modules:
        pattern = re.compile(rf"(?<![\w.]){re.escape(module)}(?![\w.])")
        for path, relative in archivos:
            contenido = path.read_text(encoding="utf-8", errors="ignore")
            if pattern.search(contenido):
                encontrados.append(f"{relative}: {module}")
    assert not encontrados, encontrados


def test_no_hay_referencias_activas_a_rutas_anteriores():
    paths, _ = _manifest()
    rutas_textuales = [route for route in paths if "/" in route]
    archivos = list(_text_files())
    encontrados = []
    for route in rutas_textuales:
        for path, relative in archivos:
            contenido = path.read_text(encoding="utf-8", errors="ignore")
            if route in contenido:
                encontrados.append(f"{relative}: {route}")
    assert not encontrados, encontrados