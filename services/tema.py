# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Gestión de temas de la aplicación
# =============================================================================

# Estado global del tema
tema_actual = "oscuro"

import json
from pathlib import Path
from typing import Optional

# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Gestión de temas de la aplicación
# =============================================================================

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List

# =============================================================================
# CONFIGURACIÓN DE TEMAS
# =============================================================================

class TemaManager:
    """Gestor avanzado de temas con validación y personalización."""

    # Temas predefinidos
    TEMAS_PREDEFINIDOS = {
        'oscuro': {
            'nombre': 'oscuro',
            'background': '#1a1a1a',
            'background_secundario': '#2d2d2d',
            'texto': '#ffffff',
            'texto_secundario': '#cccccc',
            'primario': '#1f9e49',
            'primario_hover': '#45a049',
            'error': '#f44336',
            'warning': '#ff9800',
            'success': '#4caf50',
            'border': '#404040',
            'input_background': '#333333',
            'button_disabled': '#666666'
        },
        'claro': {
            'nombre': 'claro',
            'background': '#f5f5f5',
            'background_secundario': '#ffffff',
            'texto': '#212121',
            'texto_secundario': '#757575',
            'primario': '#1f9e49',
            'primario_hover': '#45a049',
            'error': '#d32f2f',
            'warning': '#f57c00',
            'success': '#388e3c',
            'border': '#e0e0e0',
            'input_background': '#ffffff',
            'button_disabled': '#cccccc'
        },
        'azul': {
            'nombre': 'azul',
            'background': '#0f1419',
            'background_secundario': '#1c2938',
            'texto': '#ffffff',
            'texto_secundario': '#8899a6',
            'primario': '#1da1f2',
            'primario_hover': '#1991db',
            'error': '#e0245e',
            'warning': '#ffad1f',
            'success': '#17bf63',
            'border': '#2f3336',
            'input_background': '#253341',
            'button_disabled': '#4a5d6b'
        }
    }

    def __init__(self):
        self.config_dir = Path.home() / "VESP Control"
        self.config_file = self.config_dir / "tema.json"
        self.temas_personalizados_file = self.config_dir / "temas_personalizados.json"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.tema_actual = self._cargar_preferencia()
        self.temas_personalizados = self._cargar_temas_personalizados()

    def _cargar_preferencia(self) -> str:
        """Carga la preferencia de tema guardada."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tema = data.get('tema', 'oscuro')
                    if self._validar_tema(tema):
                        return tema
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"⚠️ Error cargando configuración de tema: {e}")

        return 'oscuro'

    def _cargar_temas_personalizados(self) -> Dict[str, Dict[str, Any]]:
        """Carga temas personalizados desde archivo."""
        if self.temas_personalizados_file.exists():
            try:
                with open(self.temas_personalizados_file, 'r', encoding='utf-8') as f:
                    temas = json.load(f)
                    # Validar cada tema personalizado
                    temas_validos = {}
                    for nombre, config in temas.items():
                        if self._validar_config_tema(config):
                            temas_validos[nombre] = config
                    return temas_validos
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error cargando temas personalizados: {e}")

        return {}

    def _validar_tema(self, nombre_tema: str) -> bool:
        """Valida que un tema existe."""
        return (nombre_tema in self.TEMAS_PREDEFINIDOS or
                nombre_tema in self.temas_personalizados)

    def _validar_config_tema(self, config: Dict[str, Any]) -> bool:
        """Valida que una configuración de tema sea completa y válida."""
        campos_requeridos = [
            'nombre', 'background', 'texto', 'primario',
            'error', 'warning', 'success'
        ]

        # Verificar campos requeridos
        for campo in campos_requeridos:
            if campo not in config:
                return False

        # Verificar que los colores sean válidos (formato hex)
        campos_color = [k for k in config.keys() if k != 'nombre']
        for campo in campos_color:
            color = config[campo]
            if not isinstance(color, str) or not color.startswith('#'):
                return False
            try:
                int(color[1:], 16)  # Validar formato hex
                if len(color) != 7:  # Debe ser #RRGGBB
                    return False
            except ValueError:
                return False

        return True

    def cambiar_tema(self, nombre_tema: str) -> Dict[str, Any]:
        """
        Cambia el tema actual con validaciones robustas.

        Args:
            nombre_tema: Nombre del tema a aplicar

        Returns:
            Configuración del tema aplicado

        Raises:
            ValueError: Si el tema no es válido
        """
        if not isinstance(nombre_tema, str):
            raise ValueError("El nombre del tema debe ser una cadena")

        nombre_tema = nombre_tema.strip().lower()

        if not self._validar_tema(nombre_tema):
            temas_disponibles = list(self.TEMAS_PREDEFINIDOS.keys()) + list(self.temas_personalizados.keys())
            raise ValueError(f"Tema '{nombre_tema}' no válido. Temas disponibles: {temas_disponibles}")

        try:
            # Aplicar cambio
            self.tema_actual = nombre_tema

            # Guardar preferencia
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'tema': nombre_tema}, f, ensure_ascii=False, indent=2)

            print(f"✅ Tema cambiado a: {nombre_tema}")
            return self.obtener_tema()

        except IOError as e:
            raise RuntimeError(f"Error guardando configuración de tema: {e}")

    def obtener_tema(self) -> Dict[str, Any]:
        """Obtiene la configuración del tema actual."""
        if self.tema_actual in self.TEMAS_PREDEFINIDOS:
            return self.TEMAS_PREDEFINIDOS[self.tema_actual].copy()
        elif self.tema_actual in self.temas_personalizados:
            return self.temas_personalizados[self.tema_actual].copy()
        else:
            # Fallback a tema oscuro
            print(f"⚠️ Tema '{self.tema_actual}' no encontrado, usando tema oscuro")
            self.tema_actual = 'oscuro'
            return self.TEMAS_PREDEFINIDOS['oscuro'].copy()

    def crear_tema_personalizado(self, nombre: str, config: Dict[str, Any]) -> None:
        """
        Crea un tema personalizado.

        Args:
            nombre: Nombre único del tema
            config: Configuración del tema

        Raises:
            ValueError: Si el nombre o configuración no son válidos
        """
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del tema no puede estar vacío")

        nombre = nombre.strip().lower()

        if nombre in self.TEMAS_PREDEFINIDOS:
            raise ValueError(f"El nombre '{nombre}' está reservado para un tema predefinido")

        if len(nombre) > 50:
            raise ValueError("El nombre del tema es demasiado largo")

        if not self._validar_config_tema(config):
            raise ValueError("Configuración de tema inválida")

        # Añadir nombre a la configuración
        config['nombre'] = nombre

        # Guardar tema personalizado
        self.temas_personalizados[nombre] = config

        try:
            with open(self.temas_personalizados_file, 'w', encoding='utf-8') as f:
                json.dump(self.temas_personalizados, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise RuntimeError(f"Error guardando tema personalizado: {e}")

    def eliminar_tema_personalizado(self, nombre: str) -> None:
        """
        Elimina un tema personalizado.

        Args:
            nombre: Nombre del tema a eliminar

        Raises:
            ValueError: Si el tema no existe o es predefinido
        """
        if nombre in self.TEMAS_PREDEFINIDOS:
            raise ValueError("No se pueden eliminar temas predefinidos")

        if nombre not in self.temas_personalizados:
            raise ValueError(f"Tema personalizado '{nombre}' no encontrado")

        # Si es el tema actual, cambiar a oscuro
        if self.tema_actual == nombre:
            self.cambiar_tema('oscuro')

        del self.temas_personalizados[nombre]

        try:
            with open(self.temas_personalizados_file, 'w', encoding='utf-8') as f:
                json.dump(self.temas_personalizados, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise RuntimeError(f"Error guardando cambios: {e}")

    def listar_temas(self) -> Dict[str, List[str]]:
        """Lista todos los temas disponibles."""
        return {
            'predefinidos': list(self.TEMAS_PREDEFINIDOS.keys()),
            'personalizados': list(self.temas_personalizados.keys())
        }

    def obtener_preview_tema(self, nombre_tema: str) -> Optional[Dict[str, Any]]:
        """Obtiene preview de un tema sin cambiar el actual."""
        if nombre_tema in self.TEMAS_PREDEFINIDOS:
            return self.TEMAS_PREDEFINIDOS[nombre_tema].copy()
        elif nombre_tema in self.temas_personalizados:
            return self.temas_personalizados[nombre_tema].copy()
        return None

_tema_manager: Optional[TemaManager] = None

def obtener_tema_manager() -> TemaManager:
    """Obtiene la instancia global del gestor de temas."""
    global _tema_manager
    if _tema_manager is None:
        _tema_manager = TemaManager()
    return _tema_manager

# =============================================================================
# FUNCIONES DE ACCESO RÁPIDO (LEGACY)
# =============================================================================

def cambiar_tema(tema: str) -> Dict[str, Any]:
    """
    Función legacy para cambiar tema.
    Usa el TemaManager para compatibilidad hacia atrás.
    """
    try:
        manager = obtener_tema_manager()
        return manager.cambiar_tema(tema)
    except Exception as e:
        print(f"❌ Error cambiando tema: {e}")
        # Fallback al tema oscuro
        return TemaManager.TEMAS_PREDEFINIDOS['oscuro'].copy()

def obtener_tema_actual() -> str:
    """Obtiene el nombre del tema actual."""
    try:
        manager = obtener_tema_manager()
        return manager.tema_actual
    except Exception:
        return 'oscuro'

def obtener_tema() -> Dict[str, Any]:
    """Obtiene la configuración del tema actual."""
    try:
        manager = obtener_tema_manager()
        return manager.obtener_tema()
    except Exception as e:
        print(f"❌ Error obteniendo tema: {e}")
        return TemaManager.TEMAS_PREDEFINIDOS['oscuro'].copy()

# =============================================================================
# FUNCIONES DE GESTIÓN AVANZADA
# =============================================================================

def crear_tema_personalizado(nombre: str, config: Dict[str, Any]) -> None:
    """Crea un tema personalizado."""
    manager = obtener_tema_manager()
    manager.crear_tema_personalizado(nombre, config)

def eliminar_tema_personalizado(nombre: str) -> None:
    """Elimina un tema personalizado."""
    manager = obtener_tema_manager()
    manager.eliminar_tema_personalizado(nombre)

def listar_temas_disponibles() -> Dict[str, List[str]]:
    """Lista todos los temas disponibles."""
    manager = obtener_tema_manager()
    return manager.listar_temas()

def obtener_preview_tema(nombre_tema: str) -> Optional[Dict[str, Any]]:
    """Obtiene preview de un tema."""
    manager = obtener_tema_manager()
    return manager.obtener_preview_tema(nombre_tema)

def obtener_tema_actual():
    """Retorna el tema actual de la aplicación."""
    return obtener_tema_manager().tema_actual


def establecer_tema_actual(tema):
    """Establece el tema actual de la aplicación."""
    obtener_tema_manager().cambiar_tema(tema)