# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Gestión de temas de la aplicación
# =============================================================================

# Estado global del tema
tema_actual = "oscuro"

import json
from pathlib import Path
from typing import Optional

class TemaManager:
    """Gestor avanzado de temas."""
    
    TEMA_OSCURO = {'nombre': 'oscuro', 'background': '#1a1a1a', 'texto': '#ffffff', 'primario': '#1f9e49'}
    TEMA_CLARO = {'nombre': 'claro', 'background': '#f5f5f5', 'texto': '#212121', 'primario': '#1f9e49'}
    
    def __init__(self):
        self.config_dir = Path.home() / "VESP Control"
        self.config_file = self.config_dir / "tema.json"
        self.tema_actual = self._cargar_preferencia()
    
    def _cargar_preferencia(self) -> str:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f).get('tema', 'oscuro')
            except:
                pass
        return 'oscuro'
    
    def cambiar_tema(self, tema: str) -> dict:
        if tema in ['oscuro', 'claro']:
            self.tema_actual = tema
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'tema': tema}, f)
        return self.obtener_tema()
    
    def obtener_tema(self) -> dict:
        return self.TEMA_CLARO.copy() if self.tema_actual == 'claro' else self.TEMA_OSCURO.copy()

_tema_manager: Optional[TemaManager] = None

def obtener_tema_manager() -> TemaManager:
    global _tema_manager
    if _tema_manager is None:
        _tema_manager = TemaManager()
    return _tema_manager

def obtener_tema_actual():
    """Retorna el tema actual de la aplicación."""
    return obtener_tema_manager().tema_actual


def establecer_tema_actual(tema):
    """Establece el tema actual de la aplicación."""
    obtener_tema_manager().cambiar_tema(tema)