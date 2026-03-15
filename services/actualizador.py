# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de verificación de actualizaciones desde GitHub
# =============================================================================

import webbrowser
import requests
from PyQt6.QtWidgets import QMessageBox


# URL del archivo version.txt en el repositorio remoto
URL_VERSION_REMOTA = "https://raw.githubusercontent.com/Taiuuu/sistema-control-objetivos/main/version.txt"
URL_RELEASES = "https://github.com/Taiuuu/sistema-control-objetivos/releases/latest"


# =============================================================================
# VERSIÓN
# =============================================================================

def _leer_version_local() -> str:
    """Lee la versión actual del archivo version.txt local."""
    try:
        with open("version.txt") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def _version_es_mayor(v1: str, v2: str) -> bool:
    """Retorna True si v1 es mayor que v2 en formato semver (X.Y.Z)."""
    partes1 = [int(x) for x in v1.split(".")]
    partes2 = [int(x) for x in v2.split(".")]
    return partes1 > partes2


# =============================================================================
# VERIFICACIÓN
# =============================================================================

def verificar_actualizacion(parent=None) -> None:
    """
    Consulta el repositorio remoto y compara con la versión local.
    Si hay una versión más nueva disponible, notifica al usuario
    y le ofrece ir a la página de descarga.
    Falla silenciosamente si no hay conexión a internet.
    """
    version_local = _leer_version_local()

    try:
        respuesta = requests.get(URL_VERSION_REMOTA, timeout=5)
        if respuesta.status_code != 200:
            return

        version_remota = respuesta.text.strip()

        if not _version_es_mayor(version_remota, version_local):
            return

        resultado = QMessageBox.question(
            parent,
            "Actualización disponible",
            f"Nueva versión disponible: {version_remota}\n"
            f"Versión actual: {version_local}\n\n"
            f"¿Querés ir a descargarla?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resultado == QMessageBox.StandardButton.Yes:
            webbrowser.open(URL_RELEASES)

    except Exception:
        # Falla silenciosamente si no hay conexión
        pass