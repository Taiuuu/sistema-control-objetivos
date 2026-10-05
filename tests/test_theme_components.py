import pytest
from PyQt6.QtWidgets import QApplication

from ui.components import (
    ContrastCard,
    GlassCard,
    KpiCard,
    PillButton,
    ProgressBarThin,
    SearchInput,
    StatusBadge,
    ThemeLogo,
)
from ui.theme.theme_manager import get_theme_manager
from ui.theme.tokens import THEMES


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def test_components_follow_theme_changes(app, tmp_path, monkeypatch):
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")

    card = GlassCard()
    contrast_card = ContrastCard()
    button = PillButton("Primary", "primary")
    search = SearchInput()
    badge = StatusBadge("Ready", "ok")
    progress = ProgressBarThin(42)
    logo = ThemeLogo()
    kpi = KpiCard("Active", 12, "✓")

    manager.set_theme("Negro")

    assert THEMES["Negro"]["surface"] in card.styleSheet()
    assert THEMES["Negro"]["card_contrast"] in contrast_card.styleSheet()
    assert THEMES["Negro"]["accent"] in button.styleSheet()
    assert THEMES["Negro"]["text_primary"] in search.styleSheet()
    assert THEMES["Negro"]["success"] in badge.styleSheet()
    assert THEMES["Negro"]["accent"] in progress.styleSheet()
    assert logo.toolTip() == "Logo del tema Negro"
    assert not logo.pixmap().isNull()
    assert THEMES["Negro"]["text_primary"] in kpi.value_label.styleSheet()

    manager.set_theme(original_theme)


@pytest.mark.parametrize("variant", ["primary", "secondary", "ghost", "danger"])
def test_pill_button_accepts_each_variant(app, variant):
    assert PillButton("Action", variant).variant == variant


@pytest.mark.parametrize("status", ["ok", "warning", "danger", "info"])
def test_status_badge_accepts_each_status(app, status):
    assert StatusBadge("Status", status).status == status


def test_invalid_component_variants_are_rejected(app):
    with pytest.raises(ValueError, match="Variante no válida"):
        PillButton("Action", "unknown")
    with pytest.raises(ValueError, match="Estado no válido"):
        StatusBadge("Status", "unknown")


def test_component_preview_switches_all_components_live(app, tmp_path, monkeypatch):
    from scripts.preview_components import ComponentsPreview

    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    preview = ComponentsPreview()
    preview.theme_selector.setCurrentText("Verde")

    assert manager.current() == "Verde"
    assert preview.centralWidget().findChild(ThemeLogo).toolTip() == "Logo del tema Verde"
    assert preview.centralWidget().findChild(PillButton).styleSheet()

    manager.set_theme(original_theme)
    preview.close()
