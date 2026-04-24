# =============================================================================
# VESP Organizations - Estilos y Paletas Centralizadas
# Módulo único para temas, colores y CSS de toda la UI
# =============================================================================

# =========================================================================
# PALETAS DE COLOR
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
    "scrollbar_handle":  "#3f4556",
    
    # Badges
    "badge_bg":          "#1e2128",
    "estado_verde_bg":   "#14532d",
    "estado_verde_fg":   "#4ade80",
    "estado_rojo_bg":    "#7f1d1d",
    "estado_rojo_fg":    "#fca5a5",
    "estado_amarillo_bg": "#78350f",
    "estado_amarillo_fg": "#fcd34d",
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
    
    # Badges
    "badge_bg":          "#f1f5f9",
    "estado_verde_bg":   "#dcfce7",
    "estado_verde_fg":   "#15803d",
    "estado_rojo_bg":    "#fee2e2",
    "estado_rojo_fg":    "#dc2626",
    "estado_amarillo_bg": "#fef9c3",
    "estado_amarillo_fg": "#b45309",
}


def obtener_color(key: str, oscuro: bool) -> str:
    """Obtiene un color de la paleta según el tema actual."""
    paleta = PALETA_OSCURA if oscuro else PALETA_CLARA
    return paleta.get(key, "#ffffff")


# =========================================================================
# GENERADORES DE ESTILOS CSS
# =========================================================================

def estilo_input(oscuro: bool) -> str:
    """Estilo para inputs (ComboBox, LineEdit, DateEdit)."""
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
            selection-background-color: {accent};
        }}
        QComboBox:hover, QLineEdit:hover, QDateEdit:hover {{
            border-color: {accent};
        }}
        QComboBox:focus, QLineEdit:focus, QDateEdit:focus {{
            border-color: {accent};
            outline: none;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            selection-background-color: {accent};
            selection-color: white;
            outline: none;
        }}
    """


def estilo_tabla(oscuro: bool) -> str:
    """Estilo para la tabla principal."""
    bg_tabla = obtener_color("bg_tabla", oscuro)
    bg_header = obtener_color("bg_header", oscuro)
    fg_primary = obtener_color("text_primary", oscuro)
    fg_secondary = obtener_color("text_secondary", oscuro)
    border = obtener_color("border", oscuro)
    border_light = obtener_color("border_light", oscuro)
    accent = obtener_color("accent", oscuro)
    scrollbar_handle = obtener_color("scrollbar_handle", oscuro)
    btn_menu_hover = obtener_color("btn_menu_hover", oscuro)
    
    return f"""
        QTableWidget {{
            background-color: {bg_tabla};
            gridline-color: transparent;
            border: none;
            outline: none;
            font-size: 12px;
            color: {fg_primary};
            selection-background-color: transparent;
        }}
        QTableWidget::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {border_light};
            color: {fg_primary};
        }}
        QTableWidget::item:selected {{
            background-color: {btn_menu_hover};
            color: {fg_primary};
        }}
        QHeaderView::section {{
            background-color: {bg_header};
            color: {fg_secondary};
            border: none;
            border-bottom: 2px solid {accent};
            padding: 8px 10px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        QScrollBar:vertical {{
            width: 6px;
            background: transparent;
        }}
        QScrollBar::handle:vertical {{
            background: {scrollbar_handle};
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar:horizontal {{
            height: 6px;
            background: transparent;
        }}
        QScrollBar::handle:horizontal {{
            background: {scrollbar_handle};
            border-radius: 3px;
        }}
    """


def estilo_boton_menu(oscuro: bool, activo: bool = False) -> str:
    """Estilo para botones del menú lateral."""
    if activo:
        bg = obtener_color("accent", oscuro)
        fg = "#ffffff"
    else:
        bg = "transparent"
        fg = obtener_color("btn_menu_text", oscuro)
    
    bg_hover = obtener_color("btn_menu_hover", oscuro)
    accent = obtener_color("accent", oscuro)
    fg_primary = obtener_color("text_primary", oscuro)
    
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: none;
            border-radius: 8px;
            padding: 0px 10px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {bg_hover};
            color: {fg_primary};
        }}
    """


def estilo_separador(oscuro: bool) -> str:
    """Estilo para separadores."""
    border = obtener_color("border", oscuro)
    return f"QFrame {{ background: {border}; max-height: 1px; border: none; margin: 4px 0; }}"


def estilo_btn_tema(oscuro: bool) -> str:
    """Estilo para botón de cambio de tema."""
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
            font-size: 11px;
            padding: 0 10px;
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {accent};
            color: white;
            border-color: {accent};
        }}
    """


def estilo_btn_logout(oscuro: bool) -> str:
    """Estilo para botón logout."""
    accent_red = obtener_color("accent_red", oscuro)
    
    return f"""
        QPushButton {{
            background-color: {accent_red};
            color: white;
            border: 1px solid {accent_red};
            border-radius: 7px;
            font-size: 11px;
            padding: 0 10px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: #ff5252;
            border-color: #ff5252;
        }}
    """


def estilo_btn_zoom(oscuro: bool) -> str:
    """Estilo para botones de zoom."""
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
            font-size: 11px;
            min-width: 30px;
            max-width: 36px;
            min-height: 26px;
        }}
        QPushButton:hover {{
            background-color: {accent};
            color: white;
            border-color: {accent};
        }}
    """


def estilo_scrollarea_filtros(oscuro: bool) -> str:
    """Estilo para scroll area de filtros."""
    bg = obtener_color("bg_header", oscuro)
    scrollbar_handle = obtener_color("scrollbar_handle", oscuro)
    
    return f"""
        QScrollArea {{
            border: none;
            background: {bg};
        }}
        QScrollBar:horizontal {{
            height: 3px;
            background: transparent;
        }}
        QScrollBar::handle:horizontal {{
            background: {scrollbar_handle};
            border-radius: 1px;
        }}
    """


def estilo_header(oscuro: bool) -> str:
    """Estilo para el header de la ventana."""
    bg = obtener_color("bg_header", oscuro)
    border = obtener_color("border", oscuro)
    
    return f"""
        QFrame {{
            background-color: {bg};
            border-bottom: 1px solid {border};
        }}
    """
