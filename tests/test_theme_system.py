import json

from PyQt6.QtCore import qInstallMessageHandler
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QFrame

from ui.animaciones import (
    animar_aparecer,
    tiene_animacion_activa,
)
from ui.theme.stylesheet import generate_stylesheet
from ui.theme.colors import parse_color
from ui.theme.theme_manager import get_theme_manager
from ui.theme.tokens import THEMES


_APP = QApplication.instance() or QApplication([])


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
        "accent_hover_text",
        "accent_text",
        "success",
        "success_text",
        "warning",
        "warning_text",
        "danger",
        "danger_text",
        "danger_button_bg",
        "danger_button_hover",
        "danger_button_text",
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


def _composite(foreground: str | QColor, background: str | QColor) -> QColor:
    foreground_color = (
        parse_color(foreground) if isinstance(foreground, str) else foreground
    )
    background_color = (
        parse_color(background) if isinstance(background, str) else background
    )
    alpha = foreground_color.alphaF()
    return QColor(
        round(
            foreground_color.red() * alpha
            + background_color.red() * (1 - alpha)
        ),
        round(
            foreground_color.green() * alpha
            + background_color.green() * (1 - alpha)
        ),
        round(
            foreground_color.blue() * alpha
            + background_color.blue() * (1 - alpha)
        ),
    )


def _contrast_ratio(foreground: str | QColor, background: str | QColor) -> float:
    def luminance(color: str | QColor) -> float:
        parsed = parse_color(color) if isinstance(color, str) else color
        channels = [parsed.redF(), parsed.greenF(), parsed.blueF()]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return sum(
            value * weight
            for value, weight in zip(linear, (0.2126, 0.7152, 0.0722))
        )

    lighter, darker = sorted(
        (luminance(foreground), luminance(background)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_theme_text_and_status_colors_meet_wcag_contrast():
    text_tokens = (
        "text_primary",
        "text_secondary",
        "text_disabled",
        "success_text",
        "warning_text",
        "danger_text",
    )
    for theme_name, tokens in THEMES.items():
        backgrounds = {
            "gradient_start": parse_color(tokens["bg_gradient_start"]),
            "gradient_end": parse_color(tokens["bg_gradient_end"]),
            "surface_alt": parse_color(tokens["surface_alt"]),
        }
        backgrounds["surface_start"] = _composite(
            tokens["surface"], tokens["bg_gradient_start"]
        )
        backgrounds["surface_end"] = _composite(
            tokens["surface"], tokens["bg_gradient_end"]
        )
        backgrounds["contrast_start"] = _composite(
            tokens["card_contrast"], tokens["bg_gradient_start"]
        )
        backgrounds["contrast_end"] = _composite(
            tokens["card_contrast"], tokens["bg_gradient_end"]
        )

        for foreground in text_tokens:
            for background_name, background in backgrounds.items():
                ratio = _contrast_ratio(tokens[foreground], background)
                assert ratio >= 4.5, (
                    f"{theme_name}: {foreground} over {background_name} "
                    f"has contrast {ratio:.2f}:1"
                )

        for background_name in (
            "gradient_start",
            "gradient_end",
            "surface_alt",
            "surface_start",
            "surface_end",
        ):
            ratio = _contrast_ratio(tokens["accent"], backgrounds[background_name])
            assert ratio >= 4.5, (
                f"{theme_name}: accent over {background_name} "
                f"has contrast {ratio:.2f}:1"
            )

        for foreground, background in (
            ("accent_text", "accent"),
            ("accent_hover_text", "accent_hover"),
            ("danger_button_text", "danger_button_bg"),
            ("text_primary", "surface_alt"),
        ):
            ratio = _contrast_ratio(tokens[foreground], tokens[background])
            assert ratio >= 4.5, (
                f"{theme_name}: {foreground} over {background} "
                f"has contrast {ratio:.2f}:1"
            )

        for background in backgrounds.values():
            for state in ("success", "warning", "danger", "accent"):
                color = parse_color(tokens[state])
                color.setAlpha(12)
                badge_background = _composite(color, background)
                ratio = _contrast_ratio(tokens["text_primary"], badge_background)
                assert ratio >= 4.5, (
                    f"{theme_name}: badge {state} has contrast {ratio:.2f}:1"
                )

        for background_name in ("surface_start", "surface_end"):
            accent_tint = parse_color(tokens["accent"])
            accent_tint.setAlpha(35)
            icon_background = _composite(
                accent_tint,
                backgrounds[background_name],
            )
            ratio = _contrast_ratio(tokens["text_primary"], icon_background)
            assert ratio >= 4.5, (
                f"{theme_name}: KPI icon over {background_name} "
                f"has contrast {ratio:.2f}:1"
            )


def test_window_fades_do_not_nest_graphics_paint_effects():
    from ui.login import LoginWindow

    app = _APP
    manager = get_theme_manager()
    manager.apply_current()
    login = LoginWindow(lambda *_args: None)
    card = login.findChild(QFrame, "GlassCard")
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda _kind, _context, message: messages.append(message)
        if "QPainter" in message or "Painter" in message
        else None
    )

    try:
        assert login.graphicsEffect() is None
        assert card is not None
        assert card.graphicsEffect() is not None
        assert tiene_animacion_activa(login)
        login.show()
        QTest.qWait(240)
        assert login.isVisible()
        assert login.windowOpacity() >= 0.99
        assert not messages

        animar_aparecer(login)
        assert login.graphicsEffect() is None
        QTest.qWait(240)
        assert login.windowOpacity() >= 0.99
        assert not messages
    finally:
        qInstallMessageHandler(previous_handler)
        login.close()
        login.deleteLater()
        app.processEvents()
