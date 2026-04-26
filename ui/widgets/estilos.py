# =============================================================================
# VESP Organizations - Estilos y Paletas Centralizadas
# =============================================================================


# =========================================================================
# PALETAS BASE
# =========================================================================

PALETA_OSCURA = {
    # Fondos
    "bg_sidebar":        "#111318",
    "bg_sidebar_hover":  "#1e2128",
    "bg_main":           "#16181e",
    "bg_header":         "#1a1d24",
    "bg_tabla":          "#1e2128",
    "bg_tabla_alt":      "#1a1d24",

    # Acentos
    "accent":            "#4ade80",
    "accent_dark":       "#22c55e",
    "accent_red":        "#f87171",
    "accent_yellow":     "#fbbf24",

    # Texto
    "text_primary":      "#f1f5f9",
    "text_secondary":    "#94a3b8",
    "text_muted":        "#475569",

    # Bordes
    "border":            "#2a2d36",
    "border_light":      "#1e2128",

    # Botones
    "btn_menu_text":     "#cbd5e1",
    "btn_menu_hover":    "#2a2d36",

    # Scrollbars
    "scrollbar":         "#2a2d36",
    "scrollbar_handle":  "#4ade80",
}


PALETA_CLARA = {
    # Fondos
    "bg_sidebar":        "#f8fafc",
    "bg_sidebar_hover":  "#f1f5f9",
    "bg_main":           "#ffffff",
    "bg_header":         "#f8fafc",
    "bg_tabla":          "#ffffff",
    "bg_tabla_alt":      "#f8fafc",

    # Acentos
    "accent":            "#16a34a",
    "accent_dark":       "#15803d",
    "accent_red":        "#dc2626",
    "accent_yellow":     "#d97706",

    # Texto
    "text_primary":      "#0f172a",
    "text_secondary":    "#475569",
    "text_muted":        "#94a3b8",

    # Bordes
    "border":            "#e2e8f0",
    "border_light":      "#f1f5f9",

    # Botones
    "btn_menu_text":     "#334155",
    "btn_menu_hover":    "#e2e8f0",

    # Scrollbars
    "scrollbar":         "#e2e8f0",
    "scrollbar_handle":  "#94a3b8",

    # Badges (solo clara)
    "badge_bg":          "#f1f5f9",
    "estado_verde_bg":   "#dcfce7",
    "estado_verde_fg":   "#15803d",
    "estado_rojo_bg":    "#fee2e2",
    "estado_rojo_fg":    "#dc2626",
    "estado_amarillo_bg": "#fef9c3",
    "estado_amarillo_fg": "#b45309",
}


# Alias por compatibilidad
PALETA_EMPRESA = PALETA_OSCURA


# =========================================================================
# UTILIDAD PRINCIPAL
# =========================================================================

def obtener_color(key: str, oscuro: bool) -> str:
    paleta = PALETA_OSCURA if oscuro else PALETA_CLARA
    return paleta.get(key, "#ffffff")


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
        font-size: 12px;
        min-height: 28px;
    }}
    QComboBox:hover, QLineEdit:hover, QDateEdit:hover {{
        border-color: {accent};
    }}
    QComboBox:focus, QLineEdit:focus, QDateEdit:focus {{
        border-color: {accent};
    }}
    """


def estilo_tabla(oscuro: bool) -> str:
    bg = obtener_color("bg_tabla", oscuro)
    header = obtener_color("bg_header", oscuro)
    fg = obtener_color("text_primary", oscuro)
    fg2 = obtener_color("text_secondary", oscuro)
    border = obtener_color("border_light", oscuro)
    accent = obtener_color("accent", oscuro)
    scroll = obtener_color("scrollbar_handle", oscuro)

    return f"""
    QTableWidget {{
        background-color: {bg};
        border: none;
        color: {fg};
    }}
    QTableWidget::item {{
        border-bottom: 1px solid {border};
        padding: 6px;
    }}
    QHeaderView::section {{
        background-color: {header};
        color: {fg2};
        border-bottom: 2px solid {accent};
        padding: 6px;
        font-weight: bold;
    }}
    QScrollBar::handle:vertical {{
        background: {scroll};
        border-radius: 3px;
    }}
    """


def estilo_boton_menu(oscuro: bool, activo: bool = False) -> str:
    if activo:
        bg = obtener_color("accent", oscuro)
        fg = "#ffffff"
    else:
        bg = "transparent"
        fg = obtener_color("btn_menu_text", oscuro)

    hover = obtener_color("btn_menu_hover", oscuro)

    return f"""
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: none;
        border-radius: 8px;
        padding: 6px 10px;
        text-align: left;
    }}
    QPushButton:hover {{
        background-color: {hover};
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
        padding: 5px;
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