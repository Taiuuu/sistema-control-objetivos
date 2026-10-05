"""Gestor singleton del tema visual global de la aplicación."""

import json
import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from ui.theme.stylesheet import generate_stylesheet
from ui.theme.tokens import THEMES


_CONFIG_FILE = Path.home() / "VESP Control" / "tema.json"
_LEGACY_THEME_NAMES = {"oscuro": "Grafito", "claro": "Claro"}


class ThemeManager(QObject):
    """Mantiene, persiste y aplica el tema elegido a toda la QApplication."""

    theme_changed = pyqtSignal(str)
    font_size_changed = pyqtSignal(int)
    MIN_FONT_SIZE = 9
    MAX_FONT_SIZE = 20
    DEFAULT_FONT_SIZE = 13
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            QObject.__init__(cls._instance)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._config_file = _CONFIG_FILE
        self._current = self._load_preference()
        self._font_size = self._load_font_size()
        self._theme_animations = []
        self._initialized = True

    @classmethod
    def instance(cls) -> "ThemeManager":
        return cls()

    def current(self) -> str:
        return self._current

    def font_size(self) -> int:
        return self._font_size

    def tokens(self, nombre: str | None = None) -> dict[str, str]:
        """Devuelve una copia de los tokens del tema activo o del indicado."""
        theme_name = nombre or self._current
        if theme_name not in THEMES:
            raise ValueError(
                f"Tema no válido: {theme_name!r}. Opciones: {', '.join(THEMES)}"
            )
        return THEMES[theme_name].copy()

    @staticmethod
    def available_themes() -> list[str]:
        return list(THEMES)

    def set_theme(self, nombre: str) -> None:
        if not isinstance(nombre, str):
            raise ValueError("El nombre del tema debe ser una cadena.")

        canonical_name = next(
            (name for name in THEMES if name.casefold() == nombre.strip().casefold()),
            None,
        )
        if canonical_name is None:
            raise ValueError(
                f"Tema no válido: {nombre!r}. Opciones: {', '.join(THEMES)}"
            )

        self._save_preference(canonical_name)
        changed = canonical_name != self._current
        changed = canonical_name != self._current
        self._current = canonical_name
        self._apply_to_application(animate=changed)
        if changed:
            self.theme_changed.emit(canonical_name)

    def set_font_size(self, size: int) -> None:
        if isinstance(size, bool) or not isinstance(size, int):
            raise ValueError("El tamaño de fuente debe ser un entero.")
        if not self.MIN_FONT_SIZE <= size <= self.MAX_FONT_SIZE:
            raise ValueError(
                f"El tamaño de fuente debe estar entre {self.MIN_FONT_SIZE} "
                f"y {self.MAX_FONT_SIZE}."
            )

        changed = size != self._font_size
        if not changed:
            return
        self._save_font_size(size)
        self._font_size = size
        self._apply_to_application()
        self.font_size_changed.emit(size)

    def apply_current(self) -> None:
        """Aplica el tema activo sin modificar la preferencia guardada."""
        self._apply_to_application()

    def _load_preference(self) -> str:
        try:
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return "Grafito"
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("No se pudo leer la preferencia de tema: %s", exc)
            return "Grafito"

        if not isinstance(data, dict):
            logging.warning("La configuración de tema debe ser un objeto JSON.")
            return "Grafito"

        saved_name = data.get("tema_visual")
        if isinstance(saved_name, str):
            match = next(
                (name for name in THEMES if name.casefold() == saved_name.casefold()),
                None,
            )
            if match:
                return match

        legacy_name = data.get("tema")
        if isinstance(legacy_name, str):
            return _LEGACY_THEME_NAMES.get(legacy_name.strip().lower(), "Grafito")
        return "Grafito"

    def _load_font_size(self) -> int:
        try:
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self.DEFAULT_FONT_SIZE
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("No se pudo leer el tamaño de fuente: %s", exc)
            return self.DEFAULT_FONT_SIZE
        if not isinstance(data, dict):
            return self.DEFAULT_FONT_SIZE
        size = data.get("font_size", self.DEFAULT_FONT_SIZE)
        if (
            isinstance(size, int)
            and not isinstance(size, bool)
            and self.MIN_FONT_SIZE <= size <= self.MAX_FONT_SIZE
        ):
            return size
        return self.DEFAULT_FONT_SIZE

    def _save_preference(self, nombre: str) -> None:
        data = self._read_config()
        data["tema"] = "claro" if nombre == "Claro" else "oscuro"
        data["tema_visual"] = nombre
        self._write_config(data)

    def _save_font_size(self, size: int) -> None:
        data = self._read_config()
        data["font_size"] = size
        self._write_config(data)

    def _read_config(self) -> dict:
        try:
            loaded = json.loads(self._config_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("Se reemplazará la configuración inválida: %s", exc)
            return {}
        if isinstance(loaded, dict):
            return loaded
        logging.warning("Se reemplazará la configuración que no sea un objeto JSON.")
        return {}

    def _write_config(self, data: dict) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _apply_to_application(self, *, animate: bool = False) -> None:
        app = QApplication.instance()
        if app is None:
            return

        visible_windows = [
            widget for widget in app.topLevelWidgets()
            if widget.isVisible()
        ] if animate else []
        animations = []
        for window in visible_windows:
            animation = QPropertyAnimation(window, b"windowOpacity", window)
            animation.setDuration(180)
            animation.setStartValue(min(window.windowOpacity(), 0.92))
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animations.append(animation)
            self._theme_animations.append(animation)
            animation.finished.connect(
                lambda current=animation: self._theme_animations.remove(current)
                if current in self._theme_animations else None
            )

        tokens = THEMES[self._current].copy()
        tokens["font_size_md"] = f"{self._font_size}px"
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(tokens["bg_gradient_start"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(tokens["surface_alt"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tokens["surface_alt"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(tokens["text_primary"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(tokens["text_primary"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(tokens["surface_alt"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(tokens["text_primary"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens["accent_text"]))
        app.setPalette(palette)
        app.setStyleSheet(generate_stylesheet(tokens))
        for animation in animations:
            animation.start()


def get_theme_manager() -> ThemeManager:
    """Obtiene la única instancia del gestor de temas."""
    return ThemeManager.instance()
