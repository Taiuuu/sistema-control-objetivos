# =============================================================================
# VESP Organizations - Estilos y Paletas Centralizadas
# =============================================================================


from services.tema import PALETAS_UI, obtener_color_ui
from ui.theme.theme_manager import get_theme_manager

PALETA_OSCURA = PALETAS_UI["oscuro"]
PALETA_CLARA = PALETAS_UI["claro"]


# =========================================================================
# UTILIDAD
# =========================================================================

def obtener_color(key: str, oscuro: bool) -> str:
    tokens = get_theme_manager().tokens()
    aliases = {
        "bg_main": "bg_gradient_start",
        "bg_header": "surface_alt",
        "bg_sidebar": "surface",
        "badge_bg": "surface_alt",
        "bg_tabla": "surface",
        "bg_tabla_alt": "surface_alt",
        "accent": "accent",
        "accent_dark": "accent_hover",
        "accent_text": "accent_text",
        "accent_hover_text": "accent_hover_text",
        "danger_button_text": "danger_button_text",
        "accent_red": "danger",
        "text_primary": "text_primary",
        "text_secondary": "text_secondary",
        "text_muted": "text_disabled",
        "text_disabled": "text_disabled",
        "btn_menu_hover": "surface_alt",
        "btn_menu_text": "text_secondary",
        "border": "border",
        "border_light": "border",
        "scrollbar_handle": "accent",
        "estado_verde_bg": "success",
        "estado_verde_fg": "accent_text",
        "estado_amarillo_bg": "warning",
        "estado_amarillo_fg": "text_primary",
        "estado_rojo_bg": "danger",
        "estado_rojo_fg": "accent_text",
    }
    if key in aliases:
        return tokens[aliases[key]]
    return obtener_color_ui(key, oscuro)


# =========================================================================
# ESTILOS
# =========================================================================

def estilo_input(oscuro: bool) -> str:
    bg = obtener_color("bg_tabla", oscuro)
    fg = obtener_color("text_primary", oscuro)
    border = obtener_color("border", oscuro)
    accent = obtener_color("accent", oscuro)

    return f"""
    QComboBox, QLineEdit, QDateEdit {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 7px;
        padding: 4px 8px;
    }}
    QComboBox:hover, QLineEdit:hover, QDateEdit:hover {{
        border-color: {accent};
    }}
    """


def estilo_tabla(oscuro: bool) -> str:
    bg = obtener_color("bg_tabla", oscuro)
    header = obtener_color("bg_header", oscuro)
    fg = obtener_color("text_primary", oscuro)
    fg2 = obtener_color("text_secondary", oscuro)
    accent = obtener_color("accent", oscuro)

    return f"""
    QTableWidget {{
        background-color: {bg};
        border: none;
        color: {fg};
    }}
    QHeaderView::section {{
        background-color: {header};
        color: {fg2};
        border-bottom: 2px solid {accent};
    }}
    """


def estilo_boton_menu(oscuro: bool, activo: bool = False) -> str:
    bg = obtener_color("accent", oscuro) if activo else "transparent"
    fg = get_theme_manager().tokens()["accent_text"] if activo else obtener_color("btn_menu_text", oscuro)
    hover = obtener_color("btn_menu_hover", oscuro)

    return f"""
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border-radius: 8px;
        padding: 6px;
    }}
    QPushButton:hover {{
        background-color: {hover};
    }}
    """


def estilo_btn_tema(oscuro: bool) -> str:
    bg = obtener_color("btn_menu_hover", oscuro)
    fg = obtener_color("text_secondary", oscuro)
    border = obtener_color("border", oscuro)
    accent = obtener_color("accent", oscuro)

    return f"""
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 7px;
    }}
    QPushButton:hover {{
        background-color: {accent};
        color: {get_theme_manager().tokens()["accent_text"]};
    }}
    """


def estilo_btn_zoom(oscuro: bool) -> str:
    bg = obtener_color("btn_menu_hover", oscuro)
    fg = obtener_color("text_secondary", oscuro)
    border = obtener_color("border", oscuro)
    accent = obtener_color("accent", oscuro)

    return f"""
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background-color: {accent};
        color: {get_theme_manager().tokens()["accent_text"]};
    }}
    """


def estilo_scrollarea_filtros(oscuro: bool) -> str:
    bg = obtener_color("bg_header", oscuro)
    scroll = obtener_color("scrollbar_handle", oscuro)

    return f"""
    QScrollArea {{
        background: {bg};
    }}
    QScrollBar::handle:horizontal {{
        background: {scroll};
    }}
    """


def estilo_separador(oscuro: bool) -> str:
    border = obtener_color("border", oscuro)
    return f"QFrame {{ background: {border}; max-height: 1px; }}"


def estilo_btn_logout(oscuro: bool) -> str:
    rojo = obtener_color("accent_red", oscuro)

    return f"""
    QPushButton {{
        background-color: {rojo};
        color: {get_theme_manager().tokens()["danger_button_text"]};
        border-radius: 6px;
    }}
    """


def estilo_header(oscuro: bool) -> str:
    bg = obtener_color("bg_header", oscuro)
    border = obtener_color("border", oscuro)

    return f"""
    QFrame {{
        background-color: {bg};
        border-bottom: 1px solid {border};
    }}
    """