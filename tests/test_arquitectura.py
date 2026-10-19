import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {"api", "core", "database", "models", "scripts", "services", "ui"}

MODEL_DATABASE_EXCEPTIONS = {
    # El modelo de equipos usa el gestor SQLite directamente.
    "models/equipos.py": "El acceso SQLite del modelo aún no está en un servicio.",
    # El modelo de objetivos realiza persistencia a través del gestor SQLite.
    "models/objetivos.py": "El acceso SQLite del modelo aún no está en un servicio.",
    # El modelo de supervisores realiza persistencia a través del gestor SQLite.
    "models/supervisores.py": "El acceso SQLite del modelo aún no está en un servicio.",
    # El modelo de turnos usa el gestor SQLite directamente.
    "models/turnos.py": "El acceso SQLite del modelo aún no está en un servicio.",
}

SERVICE_PYQT_EXCEPTIONS = {
    # El actualizador muestra QMessageBox durante el flujo de escritorio.
    "services/actualizaciones/actualizador.py": "Notificación modal propia del escritorio.",
    # Esta abstracción ejecuta trabajos con QRunnable y señales Qt.
    "services/background_task.py": "Adaptador de tareas en segundo plano para Qt.",
    # Este módulo implementa notificaciones de bandeja del escritorio.
    "services/notificaciones.py": "Notificaciones nativas de escritorio.",
    # La sincronización usa señales y temporizadores Qt.
    "services/sincronizacion.py": "Coordinación temporal integrada con Qt.",
}

UI_DATABASE_EXCEPTIONS = {
    # El diálogo cambia contraseñas directamente en SQLite.
    "ui/cambiar_password.py": "Persistencia directa durante el cambio de contraseña.",
    # El formulario consulta SQLite para validar y guardar pasadas.
    "ui/form_pasada.py": "Persistencia directa del formulario de pasadas.",
    # La pantalla de usuarios administra registros directamente en SQLite.
    "ui/gestionar_usuarios.py": "Persistencia directa de la administración de usuarios.",
    # El importador de pantalla coordina la conexión de la base.
    "ui/importar_excel.py": "Entrega la conexión SQLite al servicio de importación.",
    # La lista de pasadas ejecuta consultas para la vista tabular.
    "ui/lista_pasadas.py": "Consultas SQL directas desde la lista de pasadas.",
    # El login valida credenciales y actualiza estado de acceso directamente.
    "ui/login.py": "Validación y actualización directa de credenciales.",
    # La pantalla de notas guarda y consulta sus registros directamente.
    "ui/notas_diarias.py": "Persistencia directa de notas diarias.",
    # Los reportes consultan SQLite desde las ventanas.
    "ui/reporte_mensual.py": "Consulta directa de datos del reporte mensual.",
    # El reporte por objetivo arma sus datos con consultas SQLite directas.
    "ui/reporte_objetivo.py": "Consultas directas del reporte por objetivo.",
    # La tabla diaria consulta y modifica registros desde la interfaz.
    "ui/tabla_diaria.py": "Consultas y escrituras directas de la tabla diaria.",
    # La transferencia importa/exporta datos con acceso SQLite desde la UI.
    "ui/transferir_datos.py": "Acceso directo durante la transferencia de datos.",
    # La ventana principal realiza algunas consultas y cambios de configuración.
    "ui/ventana_principal.py": "Consultas directas heredadas de la ventana principal.",
    # La vista de auditoría consulta la base de datos directamente.
    "ui/vista_auditoria.py": "Consulta directa de registros de auditoría.",
    # La vista de logs obtiene metadatos directamente de SQLite.
    "ui/vista_logs.py": "Consulta directa de metadatos para la vista de logs.",
    # El widget calcula coberturas consultando la base de datos.
    "ui/widgets/tabla_cobertura.py": "Consulta directa para construir la tabla de cobertura.",
}


def _python_files(package: str):
    return sorted(
        path
        for path in (ROOT / package).rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _module_parts(path: Path) -> list[str]:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return parts


def _package_parts(path: Path) -> list[str]:
    parts = _module_parts(path)
    return parts if path.name == "__init__.py" else parts[:-1]


def _imports(path: Path, node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    base = _package_parts(path)
    if node.level:
        base = base[: len(base) - node.level + 1]
    if node.module:
        base.extend(node.module.split("."))
    return [".".join(base)]


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imports_database(tree: ast.Module, path: Path) -> bool:
    return any(
        target == "database" or target.startswith("database.")
        for node in ast.walk(tree)
        for target in _imports(path, node)
    )


def _uses_sql(tree: ast.Module) -> bool:
    sql_methods = {"execute", "executemany", "executescript"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr.lower() in sql_methods:
            return True
        if (
            node.func.attr == "connect"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "sqlite3"
        ):
            return True
    return False


def _package_graph() -> dict[str, set[str]]:
    graph = {package: set() for package in PACKAGES}
    for package in PACKAGES:
        for path in _python_files(package):
            for node in ast.walk(_tree(path)):
                for target in _imports(path, node):
                    imported_package = target.split(".", 1)[0]
                    if imported_package in PACKAGES and imported_package != package:
                        graph[package].add(imported_package)
    return graph


def _package_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    cycles = []
    active = []
    complete = set()

    def visit(package: str) -> None:
        if package in active:
            cycle = active[active.index(package) :] + [package]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if package in complete:
            return
        active.append(package)
        for dependency in sorted(graph[package]):
            visit(dependency)
        active.pop()
        complete.add(package)

    for package in sorted(graph):
        visit(package)
    return cycles


def test_database_no_depende_de_services_ni_ui():
    violations = {
        str(path.relative_to(ROOT))
        for path in _python_files("database")
        for node in ast.walk(_tree(path))
        for target in _imports(path, node)
        if target.split(".", 1)[0] in {"services", "ui"}
    }
    assert not violations


def test_models_no_depende_de_otros_paquetes_de_infraestructura():
    violations = {
        str(path.relative_to(ROOT))
        for path in _python_files("models")
        for node in ast.walk(_tree(path))
        for target in _imports(path, node)
        if target.split(".", 1)[0] in {"database", "services", "ui"}
    }
    assert violations <= set(MODEL_DATABASE_EXCEPTIONS), sorted(violations)


def test_services_no_importa_pyqt_fuera_de_excepciones_conocidas():
    violations = set()
    for path in _python_files("services"):
        for node in ast.walk(_tree(path)):
            if any(
                target.startswith(("PyQt", "PySide"))
                for target in _imports(path, node)
            ):
                violations.add(str(path.relative_to(ROOT)))
    assert violations <= set(SERVICE_PYQT_EXCEPTIONS), sorted(violations)


def test_ui_no_importa_database_ni_ejecuta_sql_fuera_de_excepciones():
    violations = set()
    for path in _python_files("ui"):
        tree = _tree(path)
        if _imports_database(tree, path) or _uses_sql(tree):
            violations.add(str(path.relative_to(ROOT)))
    assert violations <= set(UI_DATABASE_EXCEPTIONS), sorted(violations)


def test_no_hay_ciclos_entre_paquetes():
    cycles = _package_cycles(_package_graph())
    assert not cycles, cycles


def test_no_hay_modulos_en_archivo_importados():
    violations = set()
    for package in PACKAGES:
        for path in _python_files(package):
            for node in ast.walk(_tree(path)):
                if any(
                    target == "_archivo" or target.startswith("_archivo.")
                    for target in _imports(path, node)
                ):
                    violations.add(str(path.relative_to(ROOT)))
    assert not violations, sorted(violations)