import json

import pytest
from PyQt6.QtWidgets import QApplication

from ui.configuracion import ConfiguracionDialog, ThemeSelectionCard
from ui.theme.theme_manager import get_theme_manager


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def test_theme_cards_apply_selected_theme_and_show_active_state(
    app, tmp_path, monkeypatch
):
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    dialog = ConfiguracionDialog()
    cards = {
        card.theme_name: card
        for card in dialog.findChildren(ThemeSelectionCard)
    }

    assert list(cards) == ["Claro", "Verde", "Negro", "Grafito"]
    assert cards[original_theme].preview.isChecked()
    assert not cards[original_theme].check.isHidden()

    cards["Verde"].preview.click()

    assert manager.current() == "Verde"
    assert cards["Verde"].preview.isChecked()
    assert not cards["Verde"].check.isHidden()
    assert not cards[original_theme].preview.isChecked()
    assert json.loads((tmp_path / "tema.json").read_text(encoding="utf-8"))[
        "tema_visual"
    ] == "Verde"

    manager.set_theme(original_theme)
    dialog.close()


def test_font_controls_share_theme_manager_and_persist_size(
    app, tmp_path, monkeypatch
):
    manager = get_theme_manager()
    original_size = manager.font_size()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    dialog = ConfiguracionDialog()

    dialog.increase_font_button.click()

    assert manager.font_size() == original_size + 1
    assert dialog.font_size_label.text() == f"{original_size + 1} px"
    assert f'font-size: {original_size + 1}px;' in app.styleSheet()
    assert json.loads((tmp_path / "tema.json").read_text(encoding="utf-8"))[
        "font_size"
    ] == original_size + 1

    dialog.decrease_font_button.click()
    assert manager.font_size() == original_size
    dialog.close()


def test_font_controls_respect_manager_limits(app, tmp_path, monkeypatch):
    manager = get_theme_manager()
    original_size = manager.font_size()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    dialog = ConfiguracionDialog()

    manager.set_font_size(manager.MIN_FONT_SIZE)
    assert not dialog.decrease_font_button.isEnabled()
    manager.set_font_size(manager.MAX_FONT_SIZE)
    assert not dialog.increase_font_button.isEnabled()

    manager.set_font_size(original_size)
    dialog.close()
