# =============================================================================
# VESP Organizations - Widgets de UI reutilizables
# Badges y componentes pequeños para ventana principal
# =============================================================================

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


# =============================================================================
# PALETAS DE COLOR (compartidas)
# =============================================================================

PALETA_OSCURA = {
    "estado_verde_bg":   "#14532d",
    "estado_verde_fg":   "#4ade80",
    "estado_rojo_bg":    "#7f1d1d",
    "estado_rojo_fg":    "#fca5a5",
    "estado_amarillo_bg": "#78350f",
    "estado_amarillo_fg": "#fcd34d",
    "badge_bg":          "#1e2128",
    "text_secondary":    "#94a3b8",
}

PALETA_CLARA = {
    "estado_verde_bg":   "#dcfce7",
    "estado_verde_fg":   "#15803d",
    "estado_rojo_bg":    "#fee2e2",
    "estado_rojo_fg":    "#dc2626",
    "estado_amarillo_bg": "#fef9c3",
    "estado_amarillo_fg": "#b45309",
    "badge_bg":          "#f1f5f9",
    "text_secondary":    "#475569",
}


def p(key: str, oscuro: bool) -> str:
    """Acceso rápido a paleta."""
    return (PALETA_OSCURA if oscuro else PALETA_CLARA)[key]


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
        bg = p(bg_key, oscuro)
        fg = p(fg_key, oscuro)
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
            bg = p("estado_rojo_bg", oscuro)
            fg = p("estado_rojo_fg", oscuro)
        elif numero == 1:
            bg = p("estado_amarillo_bg", oscuro)
            fg = p("estado_amarillo_fg", oscuro)
        else:
            bg = p("estado_verde_bg", oscuro)
            fg = p("estado_verde_fg", oscuro)
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