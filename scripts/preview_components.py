"""Vista previa interactiva de los componentes visuales reutilizables."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

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


class ComponentsPreview(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VESP · Vista previa de componentes")
        self.resize(980, 760)
        manager = get_theme_manager()
        manager.apply_current()

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        header.addWidget(ThemeLogo(48))
        title = QLabel("Componentes base")
        title.setStyleSheet("font-size: 22px; font-weight: 700; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(manager.available_themes())
        self.theme_selector.setCurrentText(manager.current())
        self.theme_selector.currentTextChanged.connect(manager.set_theme)
        header.addWidget(QLabel("Tema"))
        header.addWidget(self.theme_selector)
        layout.addLayout(header)

        kpis = QGridLayout()
        kpis.setSpacing(14)
        kpis.addWidget(KpiCard("Objetivos activos", 128, "◎", shadow=True), 0, 0)
        kpis.addWidget(KpiCard("Cumplimiento", "94%", "✓"), 0, 1)
        kpis.addWidget(KpiCard("Pendientes", 7, "!"), 0, 2)
        layout.addLayout(kpis)

        actions_card = GlassCard(shadow=True)
        actions_card.add_widget(_section_label("PillButton"))
        buttons = QHBoxLayout()
        for text, variant in (
            ("Primario", "primary"),
            ("Secundario", "secondary"),
            ("Ghost", "ghost"),
            ("Peligro", "danger"),
        ):
            buttons.addWidget(PillButton(text, variant))
        actions_card.add_layout(buttons)
        actions_card.add_widget(_section_label("SearchInput"))
        actions_card.add_widget(SearchInput("Buscar objetivos o supervisores"))
        layout.addWidget(actions_card)

        status_card = GlassCard()
        status_card.add_widget(_section_label("StatusBadge"))
        badges = QHBoxLayout()
        for text, status in (
            ("Operativo", "ok"),
            ("Revisar", "warning"),
            ("Crítico", "danger"),
            ("Información", "info"),
        ):
            badges.addWidget(StatusBadge(text, status))
        badges.addStretch()
        status_card.add_layout(badges)
        status_card.add_widget(_section_label("ProgressBarThin"))
        status_card.add_widget(ProgressBarThin(68))
        layout.addWidget(status_card)

        alert = ContrastCard(shadow=True)
        alert.add_widget(_section_label("ContrastCard"))
        alert.add_widget(QLabel("Hay 3 alertas que requieren atención."))
        alert.add_widget(StatusBadge("Atención requerida", "warning"))
        layout.addWidget(alert)

        layout.addStretch()
        self.setCentralWidget(root)

    @staticmethod
    def run() -> int:
        app = QApplication.instance() or QApplication(sys.argv)
        manager = get_theme_manager()
        original_theme = manager.current()
        window = ComponentsPreview()
        window.show()
        exit_code = app.exec()
        manager.set_theme(original_theme)
        return exit_code


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-weight: 700; background: transparent;")
    return label


if __name__ == "__main__":
    raise SystemExit(ComponentsPreview.run())
