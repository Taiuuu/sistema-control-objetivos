# =============================================================================
# VESP Organizations - Widgets de UI reutilizables
# Badges y componentes pequeños para ventana principal
# =============================================================================

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from ui.widgets.estilos import obtener_color


# =============================================================================
# WIDGET BADGE ESTADO (pill coloreado)
# =============================================================================

class BadgeEstado(QLabel):
    """Label con forma de pill para mostrar el estado de cobertura."""

    _MAPA = {
        "Pasaron los dos": ("estado_verde_bg",    "estado_verde_fg",    "✔  Pasaron los dos"),
        "No pasó noche":   ("estado_amarillo_bg",  "estado_amarillo_fg", "🌙  No pasó noche"),
        "No pasó día":     ("estado_amarillo_bg",  "estado_amarillo_fg", "☀  No pasó día"),
        "No pasó nadie":   ("estado_rojo_bg",      "estado_rojo_fg",     "✖  No pasó nadie"),
    }

    def __init__(self, estado: str, oscuro: bool, parent=None):
        super().__init__(parent)
        bg_key, fg_key, texto = self._MAPA.get(
            estado,
            ("badge_bg", "text_secondary", estado)
        )
        bg = obtener_color(bg_key, oscuro)
        fg = obtener_color(fg_key, oscuro)
        self.setText(texto)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)


# =============================================================================
# WIDGET BADGE NUMÉRICO (conteo de pasadas)
# =============================================================================

class BadgeNumero(QLabel):
    def __init__(self, numero: int, oscuro: bool, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if numero == 0:
            bg = obtener_color("estado_rojo_bg", oscuro)
            fg = obtener_color("estado_rojo_fg", oscuro)
        elif numero == 1:
            bg = obtener_color("estado_amarillo_bg", oscuro)
            fg = obtener_color("estado_amarillo_fg", oscuro)
        else:
            bg = obtener_color("estado_verde_bg", oscuro)
            fg = obtener_color("estado_verde_fg", oscuro)
        self.setText(str(numero))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 12px;
                padding: 2px 10px;
                font-size: 12px;
                font-weight: 700;
            }}
        """)