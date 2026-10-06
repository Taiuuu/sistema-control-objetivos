"""Generación del stylesheet global de Qt a partir de los tokens de tema."""

from collections.abc import Mapping


def _rgba(color: str, alpha: int) -> str:
    from ui.theme.colors import parse_color

    red, green, blue, _ = parse_color(color).getRgb()
    return f"rgba({red}, {green}, {blue}, {alpha})"


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
        QLabel#SuccessText {{ color: {tokens["success_text"]}; }}
        QLabel#WarningText {{ color: {tokens["warning_text"]}; }}
        QLabel#DangerText {{ color: {tokens["danger_text"]}; }}
        QPushButton {{
            min-height: {tokens["control_height"]};
            padding: 0 {tokens["spacing_lg"]};
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_lg"]};
            font-weight: 600;
        }}
        QPushButton:hover {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border-color: {tokens["accent"]};
        }}
        QPushButton:pressed {{
            background-color: {_rgba(tokens["accent"], 20)};
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
        QPushButton#PrimaryButton {{
            color: #FFFFFF;
            background-color: #0A6506;
            border-color: #0A6506;
        }}
        QPushButton#PrimaryButton:hover {{
            color: #FFFFFF;
            background-color: #075704;
            border-color: #075704;
        }}
        QPushButton#DangerButton {{
            color: {tokens["danger"]};
            background-color: {tokens["surface"]};
            border-color: {tokens["danger"]};
        }}
        QPushButton#DangerButton:hover {{
            color: {tokens["danger_button_text"]};
            background-color: {tokens["danger_button_bg"]};
            border-color: {tokens["danger_button_bg"]};
        }}
        QPushButton#ObjectiveActions {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_md"]};
            min-width: 32px;
            min-height: 30px;
            padding: 0;
            font-size: {tokens["font_size_lg"]};
            font-weight: 700;
        }}
        QPushButton#ObjectiveActions:hover {{
            background-color: {_rgba(tokens["accent"], 12)};
            border-color: {tokens["accent"]};
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QDateTimeEdit,
        QTimeEdit, QSpinBox {{
            min-height: {tokens["control_height"]};
            padding: 0 {tokens["spacing_sm"]};
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_sm"]};
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
        QDateEdit:focus, QDateTimeEdit:focus, QTimeEdit:focus, QSpinBox:focus {{
            border-color: {tokens["accent"]};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled,
        QComboBox:disabled, QDateEdit:disabled, QDateTimeEdit:disabled,
        QTimeEdit:disabled, QSpinBox:disabled {{
            color: {tokens["text_disabled"]};
        }}
        QDateTimeEdit::down-button {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            background-color: {tokens["surface_alt"]};
            border-left: {tokens["border_width"]} solid {tokens["border"]};
            border-top-right-radius: {tokens["radius_sm"]};
            border-bottom-right-radius: {tokens["radius_sm"]};
        }}
        QDateTimeEdit::down-button:hover {{
            background-color: {_rgba(tokens["accent"], 18)};
        }}
        QDateTimeEdit::down-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {tokens["text_secondary"]};
        }}
        QCalendarWidget {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
        }}
        QCalendarWidget QToolButton#qt_calendar_prevmonth,
        QCalendarWidget QToolButton#qt_calendar_nextmonth,
        QCalendarWidget QToolButton#qt_calendar_monthbutton,
        QCalendarWidget QToolButton#qt_calendar_yearbutton {{
            min-width: 28px;
            min-height: 28px;
            padding: 2px 6px;
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border: {tokens["border_width"]} solid transparent;
            border-radius: {tokens["radius_sm"]};
            font-weight: 600;
        }}
        QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
        QCalendarWidget QToolButton#qt_calendar_nextmonth:hover,
        QCalendarWidget QToolButton#qt_calendar_monthbutton:hover,
        QCalendarWidget QToolButton#qt_calendar_yearbutton:hover {{
            background-color: {_rgba(tokens["accent"], 16)};
            border-color: {tokens["border"]};
        }}
        QCalendarWidget QSpinBox#qt_calendar_yearedit {{
            min-height: 28px;
            padding: 0 4px;
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_sm"]};
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QCalendarWidget QAbstractItemView#qt_calendar_calendarview {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: none;
            outline: 0;
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QCalendarWidget QAbstractItemView#qt_calendar_calendarview::item:hover {{
            color: {tokens["text_primary"]};
            background-color: {_rgba(tokens["accent"], 18)};
        }}
        QCalendarWidget QAbstractItemView#qt_calendar_calendarview::item:selected {{
            color: {tokens["accent_text"]};
            background-color: {tokens["accent"]};
        }}
        QCalendarWidget QHeaderView::section {{
            color: {tokens["text_secondary"]};
            background-color: {tokens["surface_alt"]};
            border: none;
            padding: 4px;
            font-weight: 600;
        }}
        QComboBox QAbstractItemView {{
            color: {tokens["text_primary"]};
            background-color: {tokens["surface"]};
            border: {tokens["border_width"]} solid {tokens["border"]};
            selection-background-color: {tokens["accent"]};
            selection-color: {tokens["accent_text"]};
        }}
        QListWidget, QTextEdit, QPlainTextEdit {{
            color: {tokens["text_primary"]};
            background-color: {_rgba(tokens["surface"], 248)};
            border: {tokens["border_width"]} solid {tokens["border"]};
            border-radius: {tokens["radius_sm"]};
            selection-background-color: {_rgba(tokens["accent"], 16)};
            selection-color: {tokens["text_primary"]};
        }}
        QListWidget::item {{
            padding: {tokens["spacing_xs"]} {tokens["spacing_sm"]};
            border-bottom: {tokens["border_width"]} solid {_rgba(tokens["border"], 45)};
        }}
        QListWidget::item:hover, QListWidget::item:selected {{
            background-color: {_rgba(tokens["accent"], 12)};
            color: {tokens["text_primary"]};
        }}
        QGroupBox {{
            color: {tokens["text_secondary"]};
            background-color: {_rgba(tokens["surface"], 210)};
            border: {tokens["border_width"]} solid {_rgba(tokens["border"], 95)};
            border-radius: {tokens["radius_md"]};
            margin-top: {tokens["spacing_md"]};
            padding: {tokens["spacing_md"]};
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {tokens["spacing_md"]};
            padding: 0 {tokens["spacing_xs"]};
        }}
        QTableWidget {{
            color: {tokens["text_primary"]};
            background-color: {_rgba(tokens["surface"], 248)};
            alternate-background-color: {tokens["surface_alt"]};
            border: none;
            border-radius: {tokens["radius_md"]};
            gridline-color: transparent;
            selection-background-color: {_rgba(tokens["accent"], 16)};
            selection-color: {tokens["text_primary"]};
        }}
        QTableWidget::item {{
            border-bottom: {tokens["border_width"]} solid {_rgba(tokens["border"], 45)};
            padding: 5px 8px;
        }}
        QTableWidget::item:hover, QTableWidget::item:selected {{
            color: {tokens["text_primary"]};
            background-color: {_rgba(tokens["accent"], 12)};
        }}
        QTableView {{
            color: {tokens["text_primary"]};
            background-color: {_rgba(tokens["surface"], 248)};
            border: none;
            gridline-color: transparent;
            selection-background-color: {_rgba(tokens["accent"], 16)};
            selection-color: {tokens["text_primary"]};
        }}
        QTableView::item {{
            border-bottom: {tokens["border_width"]} solid {_rgba(tokens["border"], 45)};
            padding: 5px 8px;
        }}
        QTableView::item:hover, QTableView::item:selected {{
            background-color: {_rgba(tokens["accent"], 12)};
        }}
        QHeaderView::section {{
            color: {tokens["text_secondary"]};
            background-color: {_rgba(tokens["surface_alt"], 225)};
            border: none;
            border-bottom: {tokens["border_width"]} solid {_rgba(tokens["border"], 70)};
            padding: {tokens["spacing_sm"]} {tokens["spacing_md"]};
            font-size: {tokens["font_size_xs"]};
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
            color: {tokens["text_primary"]};
            background-color: {tokens["surface_alt"]};
            border-color: {tokens["accent"]};
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
            color: {tokens["text_primary"]};
            background-color: {_rgba(tokens["accent"], 16)};
        }}
        QMenu::item[danger="true"] {{ color: {tokens["danger"]}; }}
        QMenu::item[danger="true"]:selected {{
            color: {tokens["danger"]};
            background-color: {_rgba(tokens["danger"], 18)};
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
