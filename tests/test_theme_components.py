import pytest
from types import SimpleNamespace
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QToolButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QDateEdit,
    QLineEdit,
    QStyle,
    QStyleOptionSpinBox,
    QWidget,
)

from ui.components import (
    ContrastCard,
    GlassCard,
    KpiCard,
    ModuleCard,
    PillButton,
    ProgressBarThin,
    SearchInput,
    StatusBadge,
    ThemeLogo,
)
from ui.components.calendar import configure_calendar_theme
from ui.theme.theme_manager import get_theme_manager
from ui.theme.stylesheet import generate_stylesheet
from ui.theme.stylesheet import generate_date_edit_dropdown_stylesheet
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
    assert "#0A6506" in button.styleSheet()
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


def test_module_card_emits_click_and_follows_theme(app, tmp_path, monkeypatch):
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    card = ModuleCard("control_diario", "📋", "Control diario", "Revisá la cobertura")
    activations = []
    card.clicked.connect(lambda: activations.append(True))

    card._button.click()
    manager.set_theme("Negro")

    assert activations == [True]
    assert card.property("menu_key") == "control_diario"
    assert THEMES["Negro"]["surface"] in card._button.styleSheet()
    assert THEMES["Negro"]["text_primary"] in card._title.styleSheet()

    manager.set_theme(original_theme)
    card.close()


def test_password_visibility_buttons_have_room_and_toggle_both_fields(app):
    from ui.login import campo_password_con_ojito as login_password_field
    from ui.cambiar_password import campo_password_con_ojito as change_password_field

    for create_field in (login_password_field, change_password_field):
        container, password = create_field("Contraseña")
        button = container.findChild(PillButton, "PasswordVisibilityToggle")

        assert button is not None
        assert button.width() == 48
        assert button.height() == 40
        assert "padding: 0;" in button.styleSheet()
        assert password.echoMode() == QLineEdit.EchoMode.Password

        button.click()
        assert password.echoMode() == QLineEdit.EchoMode.Normal
        assert button.toolTip() == "Ocultar contraseña"

        button.click()
        assert password.echoMode() == QLineEdit.EchoMode.Password
        assert button.toolTip() == "Mostrar contraseña"
        container.close()


def test_date_calendar_tracks_all_theme_tokens(app, tmp_path, monkeypatch):
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    configure_calendar_theme(date_edit)
    calendar = date_edit.calendarWidget()
    calendar_controls = {
        child.objectName() for child in calendar.findChildren(QWidget)
    }
    assert {
        "qt_calendar_navigationbar",
        "qt_calendar_prevmonth",
        "qt_calendar_nextmonth",
        "qt_calendar_monthbutton",
        "qt_calendar_yearbutton",
        "qt_calendar_yearedit",
        "qt_calendar_calendarview",
    } <= calendar_controls
    assert date_edit.calendarPopup()
    calendar.setFirstDayOfWeek(Qt.DayOfWeek.Sunday)
    calendar.setCurrentPage(2025, 9)
    date_edit.resize(180, 36)
    date_edit.show()
    calendar.show()
    app.processEvents()
    field_samples = set()
    arrow_samples = set()
    calendar_samples = set()

    try:
        for theme_name, tokens in THEMES.items():
            manager.set_theme(theme_name)
            manager.apply_current()
            date_edit.setStyleSheet(
                generate_date_edit_dropdown_stylesheet(tokens)
            )
            app.processEvents()
            stylesheet = generate_stylesheet(tokens)
            option = QStyleOptionSpinBox()
            date_edit.initStyleOption(option)
            arrow_rect = date_edit.style().subControlRect(
                QStyle.ComplexControl.CC_SpinBox,
                option,
                QStyle.SubControl.SC_SpinBoxDown,
                date_edit,
            )
            field_image = date_edit.grab().toImage()
            calendar_image = calendar.grab().toImage()
            field_samples.add(field_image.pixelColor(20, 8).name())
            arrow_samples.add(
                field_image.pixelColor(
                    arrow_rect.x() + 2, arrow_rect.y() + 2
                ).name()
            )
            calendar_samples.add(calendar_image.pixelColor(10, 50).name())

            assert tokens["surface"] in stylesheet
            assert tokens["surface_alt"] in stylesheet
            assert tokens["text_primary"] in stylesheet
            assert tokens["text_secondary"] in stylesheet
            assert tokens["accent"] in stylesheet
            assert "QDateTimeEdit::down-button" in (
                generate_date_edit_dropdown_stylesheet(tokens)
            )
            assert "QCalendarWidget QSpinBox#qt_calendar_yearedit" in stylesheet
            assert arrow_rect.width() >= 22
            assert (
                calendar.weekdayTextFormat(Qt.DayOfWeek.Saturday)
                .foreground()
                .color()
                == QColor(tokens["text_secondary"])
            )
            assert (
                calendar.headerTextFormat().foreground().color()
                == QColor(tokens["text_secondary"])
            )
            assert (
                calendar.dateTextFormat(QDate(2025, 8, 31))
                .foreground()
                .color()
                == QColor(tokens["text_secondary"])
            )
            assert (
                calendar.dateTextFormat(QDate(2025, 10, 1))
                .foreground()
                .color()
                == QColor(tokens["text_secondary"])
            )
            today_format = calendar.dateTextFormat(QDate.currentDate())
            assert today_format.background().color() == QColor(tokens["accent"])
            assert today_format.foreground().color() == QColor(tokens["accent_text"])
    finally:
        manager.set_theme(original_theme)
        manager.apply_current()
        calendar.close()
        date_edit.close()

    assert len(field_samples) == 4
    assert len(arrow_samples) == 4
    assert len(calendar_samples) == 4


def test_objectives_screen_uses_glass_card_and_single_branded_primary(
    app, tmp_path, monkeypatch
):
    from types import SimpleNamespace
    import ui.lista_objetivos as objectives_screen

    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    monkeypatch.setattr(objectives_screen, "_cargar_objetivos", lambda: [])
    monkeypatch.setattr(objectives_screen, "get_rol", lambda: "supervisor")
    monkeypatch.setattr(
        objectives_screen,
        "tiene_permiso",
        lambda permission: permission == "objetivos.crear",
    )
    monkeypatch.setattr(
        objectives_screen,
        "obtener_sincronizador",
        lambda: SimpleNamespace(
            datos_cambiados=SimpleNamespace(connect=lambda _callback: None)
        ),
    )

    window = objectives_screen.ListaObjetivos()
    manager.set_theme("Negro")

    assert window.findChild(GlassCard) is not None
    assert window.boton_agregar is not None
    assert "#0A6506" in window.boton_agregar.styleSheet()
    assert "QTableWidget::item:hover" in window.styleSheet()
    assert len(window.tablas) == 3

    manager.set_theme(original_theme)
    window.close()


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


def test_sidebar_menu_buttons_initialize_and_refresh_theme(app, tmp_path, monkeypatch):
    from ui.ventana_principal import BotonMenu as MainMenuButton
    from ui.widgets.sidebar import BotonMenu as SidebarMenuButton

    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    buttons = [
        MainMenuButton("📋", "Control diario", False),
        SidebarMenuButton("📋", "Control diario", False),
    ]

    try:
        for theme_name in manager.available_themes():
            manager.set_theme(theme_name)
            for button in buttons:
                button.actualizar_tema(theme_name != "Claro")
                button.set_activo(True)
                if isinstance(button, MainMenuButton):
                    assert THEMES[theme_name]["surface_alt"] in button.styleSheet()
                    assert THEMES[theme_name]["text_primary"] in button.styleSheet()
                    assert "border: 1px solid rgba(" in button.styleSheet()
                else:
                    assert THEMES[theme_name]["accent"] in button.styleSheet()
                    assert THEMES[theme_name]["accent_text"] in button.styleSheet()
                button.set_activo(False)
                button.colapsar()
                if isinstance(button, MainMenuButton):
                    assert "text-align: center" in button.styleSheet()
                button.expandir()
                if isinstance(button, MainMenuButton):
                    assert "text-align: left" in button.styleSheet()
                assert "Control diario" in button.text()
    finally:
        manager.set_theme(original_theme)
        for button in buttons:
            button.deleteLater()
        app.processEvents()


def test_translucent_sidebar_card_keeps_theme_surface_and_shadow(app, tmp_path, monkeypatch):
    manager = get_theme_manager()
    original_theme = manager.current()
    monkeypatch.setattr(manager, "_config_file", tmp_path / "tema.json")
    card = GlassCard(shadow=True, background_alpha=220, content_margins=0)

    try:
        for theme_name in manager.available_themes():
            manager.set_theme(theme_name)
            assert "background-color: rgba(" in card.styleSheet()
            assert card.graphicsEffect() is not None
            assert card._shadow_effect is not None
            assert card._shadow_effect.blurRadius() == 22
    finally:
        manager.set_theme(original_theme)
        card.deleteLater()
        app.processEvents()


def test_main_sidebar_navigation_is_grouped_and_admin_links_keep_permission_gate(
    app, monkeypatch
):
    import ui.ventana_principal as main_window

    section_container = QWidget()
    owner = SimpleNamespace(
        _oscuro=True,
        _menu_visible={},
        _botones_menu=[],
        _secciones_sidebar=[],
        layout_scroll=QVBoxLayout(section_container),
        _activar_boton=lambda *_args: None,
    )
    action_names = (
        "_mostrar_dashboard",
        "abrir_form_pasada",
        "abrir_form_turno",
        "abrir_form_objetivo",
        "abrir_lista_objetivos",
        "abrir_form_supervisor",
        "abrir_lista_supervisores",
        "abrir_lista_pasadas",
        "abrir_feriados",
        "abrir_notas",
        "abrir_reporte_mensual",
        "abrir_reporte_mensual_objetivo",
        "abrir_transferir_datos",
        "abrir_importar_excel",
        "abrir_ayuda",
        "abrir_gestionar_usuarios",
        "abrir_logs",
        "abrir_indexacion",
        "abrir_validaciones",
        "abrir_auditoria",
        "abrir_sincronizacion",
    )
    for name in action_names:
        setattr(owner, name, lambda: None)

    try:
        monkeypatch.setattr(main_window, "tiene_permiso", lambda _permission: False)
        main_window.VentanaPrincipal._construir_botones_menu(owner)
        assert [label.text() for label in owner._secciones_sidebar] == [
            "OPERACIÓN",
            "GESTIÓN",
            "CONSULTAS",
        ]
        button_names = [button._texto_completo.strip().split(maxsplit=1)[-1]
                        for button in owner._botones_menu]
        assert "Control diario" in button_names
        assert "Registrar turno" in button_names
        assert "Agregar objetivo" in button_names
        assert "Ver supervisores" in button_names
        assert "Feriados" in button_names
        assert "Gestionar usuarios" not in button_names

        owner._botones_menu.clear()
        owner._secciones_sidebar.clear()
        while owner.layout_scroll.count():
            item = owner.layout_scroll.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        monkeypatch.setattr(main_window, "tiene_permiso", lambda _permission: True)
        main_window.VentanaPrincipal._construir_botones_menu(owner)
        assert owner._secciones_sidebar[-1].text() == "ADMINISTRACIÓN"
        assert any(
            "Gestionar usuarios" in button._texto_completo
            for button in owner._botones_menu
        )
    finally:
        section_container.deleteLater()
        app.processEvents()


def test_collapsed_sidebar_keeps_icon_tooltips_and_expands_back(app):
    from ui.ventana_principal import BotonMenu, VentanaPrincipal

    manager = get_theme_manager()
    logo = ThemeLogo(size=44)
    menu_button = BotonMenu("📋", "Control diario", False)
    section_label = QLabel("OPERACIÓN")
    collapse_button = QToolButton()
    settings_button = QPushButton("⚙  Configuración")
    logout_button = QPushButton("🚪  Cerrar sesión")
    user_chip = QWidget()
    widths = []
    owner = SimpleNamespace(
        _sidebar_expandido=True,
        _theme_manager=manager,
        SIDEBAR_COLAPSADO=68,
        SIDEBAR_EXPANDIDO=248,
        btn_colapsar=collapse_button,
        logo_label=logo,
        usuario_chip=user_chip,
        btn_configuracion=settings_button,
        btn_logout=logout_button,
        _botones_menu=[menu_button],
        _secciones_sidebar=[section_label],
        _ajustar_sidebar=lambda width: widths.append(width),
    )

    VentanaPrincipal._toggle_sidebar(owner)
    assert not owner._sidebar_expandido
    assert widths[-1] == 68
    assert menu_button.text().strip() == "📋"
    assert menu_button.toolTip().startswith("Control diario")
    assert "text-align: center" in menu_button.styleSheet()
    assert section_label.isHidden()
    assert user_chip.isHidden()
    assert settings_button.text() == "⚙"
    assert settings_button.toolTip() == "Configuración"
    assert logout_button.text() == "🚪"
    assert logout_button.toolTip() == "Cerrar sesión"
    assert logo._size == 28

    VentanaPrincipal._toggle_sidebar(owner)
    assert owner._sidebar_expandido
    assert widths[-1] == 248
    assert menu_button.text().endswith("Control diario")
    assert not section_label.isHidden()
    assert not user_chip.isHidden()
    assert settings_button.text() == "⚙  Configuración"
    assert logout_button.text() == "🚪  Cerrar sesión"
    assert logo._size == 44

    for widget in (
        logo,
        menu_button,
        section_label,
        collapse_button,
        settings_button,
        logout_button,
        user_chip,
    ):
        widget.deleteLater()
    app.processEvents()


def test_dashboard_metrics_are_compact_and_can_be_collapsed(app):
    from ui.ventana_principal import VentanaPrincipal

    owner = SimpleNamespace(_metricas_valores={})
    metrics = VentanaPrincipal._construir_metricas(owner)
    assert all(card.height() == 72 for card in owner._metricas_valores.values())

    toggle = QToolButton()
    dashboard = SimpleNamespace(
        _metricas=metrics,
        _btn_toggle_metricas=toggle,
        _metricas_colapsadas=False,
    )
    VentanaPrincipal._alternar_metricas(dashboard)
    assert metrics.isHidden()
    assert dashboard._metricas_colapsadas
    assert toggle.text() == "⌄"

    VentanaPrincipal._alternar_metricas(dashboard)
    assert not metrics.isHidden()
    assert not dashboard._metricas_colapsadas
    assert toggle.text() == "⌃"
    metrics.deleteLater()
    toggle.deleteLater()
    app.processEvents()


def test_dashboard_metrics_and_table_card_only_show_on_control_view(app):
    from ui.ventana_principal import VentanaPrincipal

    metrics = QWidget()
    toggle = QWidget()
    filters = QWidget()
    separator = QWidget()
    table_card = QWidget()
    table = QWidget()
    landing = QWidget()
    panel = QWidget()
    dashboard = SimpleNamespace(
        _landing=landing,
        _metricas=metrics,
        _metricas_colapsadas=False,
        _btn_toggle_metricas=toggle,
        _barra_filtros_widget=filters,
        _sep_header=separator,
        _tabla_card=table_card,
        tabla=SimpleNamespace(
            show=table.show,
            hide=table.hide,
            viewport=lambda: QWidget(),
        ),
        cargar_tabla=lambda: None,
        _panel_derecho=panel,
    )

    VentanaPrincipal._mostrar_landing_inicial(dashboard)
    assert metrics.isHidden()
    assert table_card.isHidden()
    assert landing.isVisible()

    VentanaPrincipal._mostrar_dashboard(dashboard)
    assert not metrics.isHidden()
    assert not table_card.isHidden()
    assert not table.isHidden()
    assert landing.isHidden()

    for widget in (metrics, toggle, filters, separator, table_card, table, landing, panel):
        widget.deleteLater()
    app.processEvents()


def test_dashboard_table_recolors_existing_rows_without_reloading(app):
    from ui.ventana_principal import VentanaPrincipal

    manager = get_theme_manager()
    table = QTableWidget(1, 6)
    table.setItem(0, 0, QTableWidgetItem("Objetivo"))
    table.setItem(0, 1, QTableWidgetItem("Equipo"))
    wrapper = QWidget()
    table.setCellWidget(0, 2, wrapper)
    target = SimpleNamespace(_theme_manager=manager, tabla=table)

    original_theme = manager.current()
    try:
        manager._current = "Grafito"
        VentanaPrincipal._actualizar_colores_tabla(target)
        tokens = THEMES["Grafito"]
        assert table.item(0, 0).foreground().color() == QColor(tokens["text_primary"])
        assert table.item(0, 1).foreground().color() == QColor(tokens["text_secondary"])
        assert table.item(0, 0).background().color().alpha() == 255
        assert "#FF312C2D" in wrapper.styleSheet().upper()
    finally:
        manager._current = original_theme
        table.deleteLater()
        app.processEvents()
