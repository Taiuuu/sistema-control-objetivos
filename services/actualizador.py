import os
import sys
import requests
from PyQt6.QtWidgets import QMessageBox


VERSION_ACTUAL = open("version.txt").read().strip()
URL_VERSION = "https://raw.githubusercontent.com/Taiuuu/sistema-control-objetivos/main/version.txt"
URL_REPO = "https://github.com/Taiuuu/sistema-control-objetivos"

def verificar_actualizacion(parent=None):
    try:
        respuesta = requests.get(URL_VERSION, timeout=5)
        if respuesta.status_code != 200:
            return

        version_remota = respuesta.text.strip()

        if version_remota == VERSION_ACTUAL:
            return

        if version_mayor(version_remota, VERSION_ACTUAL):
            resultado = QMessageBox.question(
                parent,
                "Actualización disponible",
                f"Hay una nueva versión disponible: {version_remota}\n"
                f"Versión actual: {VERSION_ACTUAL}\n\n"
                f"¿Querés ir a descargarla?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resultado == QMessageBox.StandardButton.Yes:
                import webbrowser
                webbrowser.open(URL_REPO + "/releases/latest")

    except Exception:
        pass


def version_mayor(v1, v2):
    partes1 = [int(x) for x in v1.split(".")]
    partes2 = [int(x) for x in v2.split(".")]
    return partes1 > partes2