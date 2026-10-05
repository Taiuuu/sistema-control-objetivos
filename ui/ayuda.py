# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de ayuda con atajos de teclado y FAQ
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QScrollArea,
    QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.theme.theme_manager import get_theme_manager
from ui.components import GlassCard, ThemeLogo


SHORTCUTS = [
    ("Ctrl + P", "Registrar pasada"),
    ("Ctrl + O", "Agregar objetivo"),
    ("Ctrl + S", "Agregar supervisor"),
    ("Ctrl + T", "Registrar turno"),
    ("Ctrl + N", "Notas del día"),
    ("Ctrl + R", "Reporte mensual"),
    ("Ctrl + B", "Actualizar tabla principal"),
    ("Ctrl + H", "Abrir esta ayuda"),
    ("Ctrl + =", "Aumentar zoom"),
    ("Ctrl + -", "Reducir zoom"),
    ("Ctrl + ←", "Día anterior"),
    ("Ctrl + →", "Día siguiente"),
]


class Ayuda(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ayuda - VESP Control")
        self.setGeometry(300, 300, 700, 600)
        self._theme_manager = get_theme_manager()

        layout = QVBoxLayout(self)
        card = GlassCard()
        contenido = card.content_layout

        # Logo y título principal
        logo = ThemeLogo(size=60)
        contenido.addWidget(logo)

        self.titulo = QLabel("Centro de Ayuda")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contenido.addWidget(self.titulo)

        # Pestañas
        self.tabs = QTabWidget()
        contenido.addWidget(self.tabs)

        # Pestaña de atajos
        self._crear_pestana_atajos()

        # Pestaña de FAQ
        self._crear_pestana_faq()

        layout.addWidget(card)
        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.titulo.setStyleSheet(
            f"font-size: {tokens['font_size_title']}; font-weight: 700; "
            f"color: {tokens['accent']};"
        )
        self._subtitulo_atajos.setStyleSheet(
            f"font-size: {tokens['font_size_sm']}; color: {tokens['text_secondary']};"
        )
        self._nota_atajos.setStyleSheet(
            f"font-size: {tokens['font_size_xs']}; color: {tokens['text_secondary']}; "
            f"padding: {tokens['spacing_sm']};"
        )
        for tabla in self.findChildren(QTableWidget):
            for fila in range(tabla.rowCount()):
                item = tabla.item(fila, 0)
                if item:
                    item.setForeground(QColor(tokens["accent"]))
        if hasattr(self, "_texto_estados"):
            self._texto_estados.setText(
                f"""
                <span style='color: {tokens["success_text"]};'><b>✔ Pasaron los dos:</b></span> Ambos turnos registraron pasada<br>
                <span style='color: {tokens["warning_text"]};'><b>⚠ No pasó [día|noches]:</b></span> Solo un turno registró pasada<br>
                <span style='color: {tokens["danger_text"]};'><b>❌ No pasó nadie:</b></span> Ningún turno registró pasada<br><br>
                Los colores te ayudan a identificar rápidamente qué objetivos necesitan atención.
                """
            )

    def _crear_pestana_atajos(self):
        """Crea la pestaña de atajos de teclado."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        subtitulo = QLabel("Usá estos atajos para trabajar más rápido")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitulo_atajos = subtitulo
        layout.addWidget(subtitulo)

        tabla = QTableWidget()
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["Atajo", "Acción"])
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla.setColumnWidth(0, 120)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.setRowCount(len(SHORTCUTS))

        for i, (atajo, accion) in enumerate(SHORTCUTS):
            item_atajo = QTableWidgetItem(atajo)
            item_atajo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla.setItem(i, 0, item_atajo)
            tabla.setItem(i, 1, QTableWidgetItem(accion))

        layout.addWidget(tabla)

        nota = QLabel("Tip: los atajos funcionan desde la ventana principal.")
        nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._nota_atajos = nota
        layout.addWidget(nota)

        self.tabs.addTab(widget, "⌨️ Atajos")

    def _crear_pestana_faq(self):
        """Crea la pestaña de preguntas frecuentes."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Pregunta 1: ¿Qué son los turnos?
        group1 = QGroupBox("¿Qué son los turnos diurno y nocturno?")
        layout1 = QVBoxLayout(group1)
        texto1 = QLabel("""
        <b>Turno diurno:</b> Trabaja desde las 6:00 hasta las 18:00 horas.<br>
        <b>Turno nocturno:</b> Trabaja desde las 18:00 hasta las 6:00 horas del día siguiente.<br><br>
        Los turnos nocturnos que cruzan la medianoche (00:00) se registran con la fecha del día que comienza el turno.
        """)
        texto1.setWordWrap(True)
        texto1.setTextFormat(Qt.TextFormat.RichText)
        layout1.addWidget(texto1)
        layout.addWidget(group1)

        # Pregunta 2: ¿Cómo registrar pasadas?
        group2 = QGroupBox("¿Cómo registrar las pasadas de supervisión?")
        layout2 = QVBoxLayout(group2)
        texto2 = QLabel("""
        Las pasadas se registran cuando un supervisor verifica físicamente un objetivo.<br><br>
        <b>Proceso:</b><br>
        1. Presiona Ctrl+P o haz clic en "Registrar pasada"<br>
        2. Selecciona el objetivo que verificaste<br>
        3. Elige el turno correspondiente (diurno/nocturno)<br>
        4. Confirma el registro<br><br>
        Cada objetivo debe ser supervisado al menos una vez por turno.
        """)
        texto2.setWordWrap(True)
        texto2.setTextFormat(Qt.TextFormat.RichText)
        layout2.addWidget(texto2)
        layout.addWidget(group2)

        # Pregunta 3: ¿Qué significa el estado de cobertura?
        group3 = QGroupBox("¿Qué significan los colores en la tabla principal?")
        layout3 = QVBoxLayout(group3)
        texto3 = QLabel()
        self._texto_estados = texto3
        texto3.setWordWrap(True)
        texto3.setTextFormat(Qt.TextFormat.RichText)
        layout3.addWidget(texto3)
        layout.addWidget(group3)

        # Pregunta 4: ¿Cómo funcionan las fechas?
        group4 = QGroupBox("¿Cómo se manejan las fechas en el sistema?")
        layout4 = QVBoxLayout(group4)
        texto4 = QLabel("""
        <b>Fechas de objetivos:</b> Cada objetivo tiene una fecha de inicio y fin opcional.<br>
        <b>Fechas de pasadas:</b> Se registran con la fecha en que ocurren.<br>
        <b>Reportes mensuales:</b> Muestran todos los objetivos activos en el mes seleccionado.<br><br>
        El formato de fecha es dd/mm/yyyy (día/mes/año).
        """)
        texto4.setWordWrap(True)
        texto4.setTextFormat(Qt.TextFormat.RichText)
        layout4.addWidget(texto4)
        layout.addWidget(group4)

        # Pregunta 5: ¿Qué hacer si hay errores?
        group5 = QGroupBox("¿Qué hacer si encuentro errores o problemas?")
        layout5 = QVBoxLayout(group5)
        texto5 = QLabel("""
        <b>Errores comunes:</b><br>
        • Verificar que las fechas estén correctas<br>
        • Asegurarse de seleccionar el turno correcto<br>
        • Comprobar que el supervisor esté registrado<br><br>
        <b>Si persiste el problema:</b><br>
        • Revisa los logs del sistema (Vista → Logs)<br>
        • Verifica la validación de datos (Vista → Validaciones)<br>
        • Contacta al administrador si es necesario
        """)
        texto5.setWordWrap(True)
        texto5.setTextFormat(Qt.TextFormat.RichText)
        layout5.addWidget(texto5)
        layout.addWidget(group5)

        layout.addStretch()
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "❓ FAQ")