# =============================================================================
# VESP Organizations - Estilos y Paletas Centralizadas
# =============================================================================


from services.tema import PALETAS_UI, obtener_color_ui

PALETA_OSCURA = PALETAS_UI["oscuro"]
PALETA_CLARA = PALETAS_UI["claro"]


# =========================================================================
# UTILIDAD
# =========================================================================

def obtener_color(key: str, oscuro: bool) -> str:
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
    fg = "#ffffff" if activo else obtener_color("btn_menu_text", oscuro)
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
        color: white;
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
        color: white;
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
        color: white;
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