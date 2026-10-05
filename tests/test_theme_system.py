import json

from PyQt6.QtWidgets import QApplication

from ui.theme.stylesheet import generate_stylesheet
from ui.theme.theme_manager import get_theme_manager
from ui.theme.tokens import THEMES


def test_all_themes_define_same_complete_token_surface():
    token_keys = {frozenset(tokens) for tokens in THEMES.values()}

    assert len(token_keys) == 1
    assert {
        "bg_gradient_start",
        "bg_gradient_end",
        "surface",
        "surface_alt",
        "border",
        "text_primary",
        "text_secondary",
        "text_disabled",
        "accent",
        "accent_hover",
        "accent_text",
        "success",
        "warning",
        "danger",
        "card_contrast",
        "sidebar_active_bg",
        "shadow",
        "logo_path",
        "radius_card",
        "spacing_md",
        "font_size_md",
    }.issubset(next(iter(token_keys)))


def test_stylesheet_covers_global_controls_for_each_theme():
    for tokens in THEMES.values():
        stylesheet = generate_stylesheet(tokens)

        for selector in (
            "QWidget",
            "QLabel",
            "QPushButton",
            "QLineEdit",
            "QComboBox",
            "QDateEdit",
            "QTableWidget",
            "QHeaderView::section",
            "QTabWidget",
            "QTabBar::tab",
            "QScrollBar",
            "QMenu",
            "QDialog",
            "QToolTip",
            "QCheckBox",
        ):
            assert selector in stylesheet
        assert tokens["bg_gradient_start"] in stylesheet
        assert tokens["accent"] in stylesheet


def test_theme_manager_persists_visual_and_legacy_preference(tmp_path, monkeypatch):
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")

    manager.set_theme("vErDe")

    config = json.loads((tmp_path / "tema.json").read_text(encoding="utf-8"))
    assert manager.current() == "Verde"
    assert config["tema_visual"] == "Verde"
    assert config["tema"] == "oscuro"
    assert manager.available_themes() == ["Claro", "Verde", "Negro", "Grafito"]

    manager.set_theme(original_theme)


def test_theme_manager_applies_stylesheet_to_application(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")

    manager.set_theme("Negro")

    assert "QDialog" in app.styleSheet()
    assert THEMES["Negro"]["bg_gradient_start"] in app.styleSheet()
    assert app.palette().color(app.palette().ColorRole.Window).name().upper() == "#000000"

    manager.set_theme(original_theme)
