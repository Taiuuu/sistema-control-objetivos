# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo para resolver rutas de assets correctamente
# tanto en desarrollo como en el ejecutable instalado
# =============================================================================

import os
import sys


def ruta_asset(relativa: str) -> str:
    """
    Retorna la ruta correcta al asset.
    En desarrollo usa la ruta relativa normal.
    En el ejecutable instalado usa la ruta temporal de PyInstaller.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relativa)
    return relativa