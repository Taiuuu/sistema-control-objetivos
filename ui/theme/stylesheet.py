"""Generación del stylesheet global de Qt a partir de los tokens de tema."""

from collections.abc import Mapping


def generate_stylesheet(tokens: Mapping[str, str]) -> str:
    """Genera QSS global evitando colores específicos de widgets."""
    return f"""
        QWidget {{
            color: {tokens["text_primary"]};
            font-family: "Aptos", "Segoe UI", sans-serif;
            font-size: {tokens["font_size_md"]};
            background-color: transparent;
        }}
        QWidget:window, QMainWindow, QDialog {{
            color: {tokens["text_primary"]};
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 {tokens["bg_gradient_start"]},
                stop: 1 {tokens["bg_gradient_end"]}
            );
        }}
        QLabel {{
            color: {tokens["text_primary"]};
            background-color: transparent;
        }}
        QLabel:disabled {{
            color: {tokens["text_disabled"]};
        }}
        QLabel#SuccessText {{ color: {tokens["success"]}; }}
        QLabel#WarningText {{ color: {tokens["warning"]}; }}
        QLabel#DangerText {{ color: {tokens["danger"]}; }}
        QPushButton {{
            min-height: {tokens["control_height"]};
            padding: 0 {tokens["spacing_lg"]};
            color: {tokens["accent_text"]};
            background-color: {tokens["accent"]};
            border: {tokens["border_width"]} solid {tokens["accent"]};
            border-radius: {tokens["radius_lg"]};
            font-weight: 600;
        }}
        QPushButton:hover {{
            color: {tokens["accent_hover_text"]};
            background-color: {tokens["accent_hover"]};
            border-color: {tokens["accent_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {tokens["accent"]};
        }}
        QPushButton:disabled {{
            color: {tokens["text_disabled"]};
            background-color: {tokens["surface_alt"]};
            border-color: {tokens["border"]};
        }}
        QPushButton#SidebarActive {{
            color: {tokens["accent_text"]};
            background-color: {tokens["sidebar_active_bg"]};
            border-color: {tokens["sidebar_active_bg"]};
        }}
        QLineEdit, QComboBox, QDateEdit {{
            min-height: {tokens["control_height"]};
            padding: 0 {tokens["spacing_sm"]};
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_sm"]};
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
            border-color: {tokens["accent"]};
        }}
        QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled {{
            color: {tokens["text_disabled"]};
        }}
        QComboBox QAbstractItemView {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QTableWidget {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            alternate-background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_md"]};
            gridline-color: {tokens["border"]};
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QTableWidget::item:hover, QTableWidget::item:selected {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
        }}
        QHeaderView::section {{
            color: {tokens["text_secondary"]};
            background-color: {tokens["surface_alt"]};
            border: none;
            border-bottom: {tokens["border_width"]} solid {tokens["border"]};
            padding: {tokens["spacing_sm"]} {tokens["spacing_md"]};
            font-weight: 600;
        }}
        QTabWidget::pane {{
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_md"]};
            padding: {tokens["spacing_sm"]};
        }}
        QTabBar::tab {{
            color: {tokens["text_secondary"]};
            background-color: transparent;
            border: {tokens["border_width"]} solid transparent;
            border-radius: {tokens["radius_md"]};
            padding: {tokens["spacing_sm"]} {tokens["spacing_md"]};
            margin: {tokens["spacing_xs"]};
        }}
        QTabBar::tab:selected {{
            color: {tokens["accent_text"]};
            background-color: {tokens["accent"]};
        }}
        QTabBar::tab:hover:!selected {{
            color: {tokens["text_primary"]};
            border-color: {tokens["border"]};
        }}
        QScrollBar:vertical {{
            width: {tokens["scrollbar_width"]};
            background-color: transparent;
            margin: {tokens["spacing_xs"]};
        }}
        QScrollBar:horizontal {{
            height: {tokens["scrollbar_width"]};
            background-color: transparent;
            margin: {tokens["spacing_xs"]};
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            min-width: 24px;
            min-height: 24px;
            background-color: {tokens["accent"]};
            border-radius: 4px;
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0;
            height: 0;
            border: none;
        }}
        QMenu {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_sm"]};
            padding: {tokens["spacing_xs"]};
        }}
        QMenu::item {{
            padding: {tokens["spacing_sm"]} {tokens["spacing_lg"]};
            border-radius: {tokens["radius_sm"]};
        }}
        QMenu::item:selected {{
            color: {tokens["accent_text"]};
            background-color: {tokens["accent"]};
        }}
        QCheckBox {{
            color: {tokens["text_primary"]};
            spacing: {tokens["spacing_sm"]};
            background-color: transparent;
        }}
        QCheckBox:disabled {{
            color: {tokens["text_disabled"]};
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: 4px;
        }}
        QCheckBox::indicator:checked {{
            background-color: {tokens["accent"]};
            border-color: {tokens["accent"]};
        }}
        QDialog {{
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_card"]};
        }}
        QToolTip {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            padding: {tokens["spacing_xs"]} {tokens["spacing_sm"]};
        }}
        QFrame#Card, QFrame#CardContenedor, QFrame#MetricCard, QFrame#PanelGlass {{
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_card"]};
        }}
        QFrame#CardContrast {{
            background-color: {tokens["card_contrast"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_card"]};
        }}
    """
