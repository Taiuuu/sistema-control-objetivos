# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado y gestión de objetivos
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QDialog,
    QLabel, QLineEdit, QDateEdit, QCheckBox,
    QInputDialog, QComboBox, QListWidget, QTabWidget, QMenu, QHeaderView,
    QHBoxLayout
)
from PyQt6.QtCore import QDate, Qt
from models.objetivos import (
    actualizar_objetivo,
    dar_de_baja_objetivo,
    listar_periodos, pausar_objetivo, reactivar_objetivo,
    eliminar_objetivo,
    listar_objetivos,
    marcar_objetivo_revisado,
)
from models.types import Objetivo
from services.sincronizacion import obtener_sincronizador
from services.sesion import get_rol
from services.permisos import tiene_permiso
from ui.components import GlassCard, PillButton, StatusBadge
from ui.components.calendar import configure_calendar_theme
from ui.components.base import rgba
from ui.theme.theme_manager import get_theme_manager


DIAS_MAP = {
    "1": "Lun", "2": "Mar", "3": "Mié",
    "4": "Jue", "5": "Vie", "6": "Sáb", "7": "Dom", "8": "Feriados"
}

DIAS_NOMBRES = {
    "Lunes": "1", "Martes": "2", "Miércoles": "3",
    "Jueves": "4", "Viernes": "5", "Sábado": "6", "Domingo": "7",
    "Feriados": "8"
}


def _cargar_objetivos() -> list[Objetivo]:
    return listar_objetivos()


def _actualizar_objetivo(objetivo_id: int, nombre: str, fecha_inicio: str,
                          fecha_fin: str | None, dias_semana: str, tipo_objetivo: str) -> None:
    actualizar_objetivo(objetivo_id, nombre, fecha_inicio, dias_semana, fecha_fin, tipo_objetivo)


class DialogoEditarObjetivo(QDialog):

    def __init__(self, objetivo: Objetivo, parent=None):
        super().__init__(parent)
        self.objetivo_id = objetivo.id
        self.setWindowTitle("Editar objetivo")
        self.setFixedSize(440, 620)
        self._theme_manager = get_theme_manager()

        card = GlassCard(parent=self)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.add_layout(layout)

        layout.addWidget(QLabel("Nombre:"))
        self.input_nombre = QLineEdit(objetivo.nombre)
        layout.addWidget(self.input_nombre)

        layout.addWidget(QLabel("Fecha inicio:"))
        self.input_inicio = QDateEdit()
        self.input_inicio.setCalendarPopup(True)
        configure_calendar_theme(self.input_inicio)
        self.input_inicio.setDate(QDate.fromString(objetivo.fecha_inicio, "yyyy-MM-dd"))
        layout.addWidget(self.input_inicio)

        layout.addWidget(QLabel("Tipo de objetivo:"))
        self.selector_tipo = QComboBox()
        self.selector_tipo.addItem("Puntual", "puntual")
        self.selector_tipo.addItem("Intermitente", "intermitente")
        self.selector_tipo.setCurrentIndex(1 if objetivo.tipo_objetivo == "intermitente" else 0)
        layout.addWidget(self.selector_tipo)

        self.check_fin = QCheckBox("Tiene fecha de finalización:")
        self.check_fin.setChecked(objetivo.fecha_fin is not None)
        self.check_fin.toggled.connect(self._toggle_fecha_fin)
        layout.addWidget(self.check_fin)

        self.input_fin = QDateEdit()
        self.input_fin.setCalendarPopup(True)
        configure_calendar_theme(self.input_fin)
        if objetivo.fecha_fin:
            self.input_fin.setDate(QDate.fromString(objetivo.fecha_fin, "yyyy-MM-dd"))
        else:
            self.input_fin.setDate(QDate.currentDate())
        self.input_fin.setEnabled(objetivo.fecha_fin is not None)
        layout.addWidget(self.input_fin)

        layout.addWidget(QLabel("Días de cobertura:"))
        dias_actuales = objetivo.dias_semana.split(",") if objetivo.dias_semana else []
        self.dias = {}
        for nombre_dia, numero in DIAS_NOMBRES.items():
            cb = QCheckBox(nombre_dia)
            cb.setChecked(numero in dias_actuales)
            layout.addWidget(cb)
            self.dias[nombre_dia] = cb

        self.historial = QListWidget()
        layout.addWidget(QLabel("Historial de períodos:"))
        layout.addWidget(self.historial)
        self._cargar_historial()

        self.boton_periodo = QPushButton()
        self.boton_periodo.setObjectName("ObjectivePeriodAction")
        self.boton_periodo.clicked.connect(self._cambiar_periodo)
        layout.addWidget(self.boton_periodo)
        self._actualizar_boton_periodo()

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        self.boton_cancelar = PillButton("Cancelar", "secondary")
        self.boton_cancelar.clicked.connect(self.reject)
        self.boton_guardar = PillButton("Guardar cambios", "primary")
        self.boton_guardar.setObjectName("EditObjectivePrimary")
        self.boton_guardar.clicked.connect(self._guardar)
        fila_botones.addWidget(self.boton_cancelar)
        fila_botones.addWidget(self.boton_guardar)
        layout.addLayout(fila_botones)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(16, 16, 16, 16)
        layout_principal.addWidget(card)
        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.setStyleSheet(
            f"""
            QLineEdit, QDateEdit, QComboBox, QListWidget {{
                color: {tokens["text_primary"]};
                background-color: {tokens["surface_alt"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_sm"]};
                padding: 5px 8px;
                selection-background-color: {tokens["accent"]};
                selection-color: {tokens["accent_text"]};
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{
                border-color: {tokens["accent"]};
            }}
            QListWidget::item {{
                padding: 7px 8px;
                border-bottom: 1px solid {rgba(tokens["border"], 45)};
            }}
            QListWidget::item:selected {{
                color: {tokens["text_primary"]};
                background-color: {tokens["surface_alt"]};
            }}
            QPushButton#ObjectivePeriodAction {{
                color: {tokens["text_primary"]};
                background-color: {tokens["surface_alt"]};
                border: 1px solid {tokens["border"]};
                border-radius: {tokens["radius_lg"]};
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton#ObjectivePeriodAction:hover {{
                background-color: {rgba(tokens["accent"], 12)};
                border-color: {tokens["accent"]};
            }}
            QPushButton#EditObjectivePrimary {{
                color: #FFFFFF;
                background-color: #0A6506;
                border: 1px solid #0A6506;
            }}
            QPushButton#EditObjectivePrimary:hover {{
                color: #FFFFFF;
                background-color: #075704;
                border-color: #075704;
            }}
            """
        )

    def _toggle_fecha_fin(self, checked: bool) -> None:
        self.input_fin.setEnabled(checked)

    def _cargar_historial(self) -> None:
        self.historial.clear()
        for periodo in listar_periodos(self.objetivo_id):
            self.historial.addItem(f"{periodo['fecha_inicio']} - {periodo['fecha_fin'] or 'Activo'}")

    def _actualizar_boton_periodo(self) -> None:
        periodos = listar_periodos(self.objetivo_id)
        activo = bool(periodos and periodos[-1]['fecha_fin'] is None)
        self.boton_periodo.setText("Pausar" if activo else "Reactivar")

    def _cambiar_periodo(self) -> None:
        try:
            fecha = QDate.currentDate().toString("yyyy-MM-dd")
            if self.boton_periodo.text() == "Pausar":
                pausar_objetivo(self.objetivo_id, fecha)
            else:
                reactivar_objetivo(self.objetivo_id, fecha)
            self._cargar_historial()
            self._actualizar_boton_periodo()
        except Exception as error:
            QMessageBox.warning(self, "Período", str(error))

    def _guardar(self) -> None:
        nombre = self.input_nombre.text().strip()
        inicio = self.input_inicio.date().toString("yyyy-MM-dd")
        fin = self.input_fin.date().toString("yyyy-MM-dd") if self.check_fin.isChecked() else None
        dias_seleccionados = [
            DIAS_NOMBRES[dia] for dia, cb in self.dias.items() if cb.isChecked()
        ]

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        if not dias_seleccionados:
            QMessageBox.warning(self, "Error", "Seleccioná al menos un día.")
            return

        if fin and fin < inicio:
            QMessageBox.warning(self, "Error", "La fecha fin no puede ser anterior al inicio.")
            return

        dias_str = ",".join(dias_seleccionados)
        _actualizar_objetivo(self.objetivo_id, nombre, inicio, fin, dias_str, self.selector_tipo.currentData())

        from services.logger import registrar_accion
        from services.sesion import get_usuario_id
        registrar_accion(
            get_usuario_id(),
            f"Editó objetivo id={self.objetivo_id} - Nombre: {nombre} | "
            f"Inicio: {inicio} | Fin: {fin or 'Sin fecha'} | Días: {dias_str}"
        )

        QMessageBox.information(self, "Listo", "Objetivo actualizado correctamente.")
        self.accept()


class ListaObjetivos(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Listado de objetivos")
        self.setGeometry(200, 200, 950, 400)
        self._theme_manager = get_theme_manager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        card = GlassCard(content_margins=18, parent=self)
        card_layout = card.content_layout
        card_layout.setSpacing(14)

        header = QHBoxLayout()
        titulo = QLabel("Ver objetivos")
        titulo.setObjectName("ObjectivesTitle")
        subtitulo = QLabel("Consultá y gestioná los objetivos y sus períodos.")
        subtitulo.setObjectName("ObjectivesSubtitle")
        encabezados = QVBoxLayout()
        encabezados.setSpacing(3)
        encabezados.addWidget(titulo)
        encabezados.addWidget(subtitulo)
        header.addLayout(encabezados, 1)
        self.boton_agregar = None
        if tiene_permiso("objetivos.crear"):
            self.boton_agregar = PillButton("＋  Agregar objetivo", "primary")
            self.boton_agregar.setObjectName("ObjectivesPrimaryAction")
            self.boton_agregar.clicked.connect(self._abrir_form_objetivo)
            header.addWidget(self.boton_agregar, 0, Qt.AlignmentFlag.AlignVCenter)
        card_layout.addLayout(header)

        # Info de permisos
        rol_actual = get_rol()
        self.es_admin = rol_actual in ("administrador", "admin")
        
        if self.es_admin:
            info_label = QLabel("Modo administrador · permisos de gestión habilitados")
            info_label.setObjectName("AdminModeBanner")
            card_layout.addWidget(info_label)

        self.tabs = QTabWidget()
        self.tablas = {}
        for clave, titulo in (("actuales", "Objetivos actuales"), ("finalizados", "Objetivos finalizados"), ("todos", "Todos")):
            tabla = QTableWidget()
            self._configurar_tabla(tabla)
            self.tablas[clave] = tabla
            self.tabs.addTab(tabla, titulo)
        self.tabla = self.tablas["actuales"]
        self._aplicar_tema(self._theme_manager.current())
        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self.tabs.currentChanged.connect(self._cargar_tabla)
        card_layout.addWidget(self.tabs, 1)

        layout.addWidget(card)
        self._cargar_tabla()

        # Conectar señales de sincronización
        self.sincronizador = obtener_sincronizador()
        self.sincronizador.datos_cambiados.connect(self._on_datos_cambiados)

    def _configurar_tabla(self, tabla: QTableWidget) -> None:
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels(["Nombre", "Inicio", "Fin", "Días", "Estado", "Acciones"])
        for columna, ancho in enumerate((220, 100, 100, 180, 170, 85)):
            tabla.setColumnWidth(columna, ancho)
        tabla.setShowGrid(False)
        tabla.setAlternatingRowColors(False)
        tabla.setMouseTracking(True)
        tabla.viewport().setMouseTracking(True)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.verticalHeader().setDefaultSectionSize(48)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        tabla.horizontalHeader().setStretchLastSection(True)

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                border-radius: {tokens['radius_md']};
                background: transparent;
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {tokens['text_secondary']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_lg']};
                padding: 7px 14px;
                margin: 0 4px 8px 0;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {tokens['surface_alt']};
                color: {tokens['text_primary']};
                border-color: {tokens['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {rgba(tokens['accent'], 10)};
                color: {tokens['text_primary']};
            }}
            QTableWidget {{
                background: {rgba(tokens['surface'], 248)};
                color: {tokens['text_primary']};
                border: none;
                gridline-color: transparent;
                outline: none;
                selection-background-color: {rgba(tokens['accent'], 14)};
                selection-color: {tokens['text_primary']};
                font-size: {tokens['font_size_sm']};
            }}
            QTableWidget::item {{
                border-bottom: 1px solid {rgba(tokens['border'], 45)};
                padding: 8px 10px;
            }}
            QTableWidget::item:hover {{
                background: {rgba(tokens['accent'], 10)};
                color: {tokens['text_primary']};
            }}
            QTableWidget::item:selected {{
                background: {rgba(tokens['accent'], 14)};
                color: {tokens['text_primary']};
            }}
            QHeaderView::section {{
                background: {rgba(tokens['surface_alt'], 220)};
                color: {tokens['text_secondary']};
                border: none;
                border-bottom: 1px solid {rgba(tokens['border'], 70)};
                padding: 8px 10px;
                font-size: {tokens['font_size_xs']};
                font-weight: 600;
            }}
            QLabel#ObjectivesTitle {{
                color: {tokens['text_primary']};
                font-size: {tokens['font_size_title']};
                font-weight: 600;
                background: transparent;
            }}
            QLabel#ObjectivesSubtitle {{
                color: {tokens['text_secondary']};
                font-size: {tokens['font_size_sm']};
                background: transparent;
            }}
            QLabel#AdminModeBanner {{
                color: {tokens['text_secondary']};
                background: {tokens['surface_alt']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']};
                padding: 7px 10px;
            }}
            QPushButton#ObjectiveActions {{
                background: {tokens['surface_alt']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']};
                font-size: {tokens['font_size_lg']};
                font-weight: 700;
                min-width: 32px;
                min-height: 30px;
            }}
            QPushButton#ObjectiveActions:hover {{
                background: {rgba(tokens['accent'], 12)};
                border-color: {tokens['accent']};
            }}
            QMenu {{
                background: {tokens['surface']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border']};
                padding: 4px;
            }}
            QMenu::item {{ padding: 7px 22px; border-radius: {tokens['radius_sm']}; }}
            QMenu::item:selected {{
                background: {tokens['surface_alt']};
                color: {tokens['text_primary']};
            }}
            QMenu::item[danger="true"] {{ color: {tokens['danger']}; }}
            QMenu::item[danger="true"]:selected {{
                background: {tokens['danger']};
                color: {tokens['accent_text']};
            }}
        """)
        if self.boton_agregar is not None:
            self.boton_agregar.setStyleSheet(
                f"""
                QPushButton {{
                    color: #FFFFFF;
                    background-color: #0A6506;
                    border: 1px solid #0A6506;
                    border-radius: {tokens['radius_lg']};
                    padding: 0 16px;
                    min-height: 38px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    color: #FFFFFF;
                    background-color: #075704;
                    border-color: #075704;
                }}
                QPushButton:pressed {{
                    color: #FFFFFF;
                    background-color: #064A03;
                }}
                """
            )
    def _cargar_tabla(self, _indice: int = 0) -> None:
        objetivos = _cargar_objetivos()
        filtros = {
            "actuales": lambda obj: obj.es_activo(),
            "finalizados": lambda obj: not obj.es_activo(),
            "todos": lambda obj: True,
        }
        for clave, tabla in self.tablas.items():
            tabla.setRowCount(0)
            seleccionados = [obj for obj in objetivos if filtros[clave](obj)]
            tabla.setRowCount(len(seleccionados))
            self._llenar_tabla(tabla, seleccionados)

    def _llenar_tabla(self, tabla: QTableWidget, objetivos: list[Objetivo]) -> None:
        for i, o in enumerate(objetivos):
            dias_texto = ", ".join([DIAS_MAP.get(d, d) for d in (o.dias_semana or "").split(",")])
            fin_texto = o.fecha_fin if o.fecha_fin else "Sin fecha fin"

            tabla.setItem(i, 0, QTableWidgetItem(o.nombre))
            tabla.setItem(i, 1, QTableWidgetItem(o.fecha_inicio))
            tabla.setItem(i, 2, QTableWidgetItem(fin_texto))
            tabla.setItem(i, 3, QTableWidgetItem(dias_texto))
            estado = "Pendiente de revisión" if o.pendiente_revision else ("Vigente" if o.es_activo() else "Finalizado")
            estado_tipo = "warning" if o.pendiente_revision else ("ok" if o.es_activo() else "info")
            estado_badge = StatusBadge(estado, estado_tipo)
            tabla.setCellWidget(i, 4, self._centrar_widget(estado_badge))

            menu = QMenu(self)
            accion_editar = menu.addAction("Editar")
            accion_editar.triggered.connect(lambda checked=False, obj=o: self._editar(obj))
            if o.pendiente_revision:
                accion_revision = menu.addAction("Marcar revisado")
                accion_revision.triggered.connect(
                    lambda checked=False, obj_id=o.id: self._marcar_revisado(obj_id)
                )
            elif not o.fecha_fin or self.es_admin:
                accion_baja = menu.addAction("Dar de baja")
                accion_baja.setProperty("danger", True)
                accion_baja.triggered.connect(
                    lambda checked=False, obj_id=o.id, nombre=o.nombre: self._dar_de_baja(obj_id, nombre)
                )
            boton_acciones = QPushButton("⋯")
            boton_acciones.setObjectName("ObjectiveActions")
            boton_acciones.setToolTip("Acciones del objetivo")
            boton_acciones.setMenu(menu)
            tabla.setCellWidget(i, 5, self._centrar_widget(boton_acciones))

    def _abrir_form_objetivo(self) -> None:
        from ui.form_objetivo import FormObjetivo

        self._form_objetivo = FormObjetivo()
        self._form_objetivo.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._form_objetivo.destroyed.connect(self._cargar_tabla)
        self._form_objetivo.show()

    @staticmethod
    def _centrar_widget(widget: QWidget) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addStretch()
        layout.addWidget(widget)
        layout.addStretch()
        return contenedor

    def _marcar_revisado(self, objetivo_id: int) -> None:
        try:
            marcar_objetivo_revisado(objetivo_id)
            self._cargar_tabla()
        except Exception as error:
            QMessageBox.warning(self, "Revisión", str(error))

    
    def _editar(self, objetivo: Objetivo) -> None:
        self.dialogo_edicion = DialogoEditarObjetivo(objetivo, self)
        if self.dialogo_edicion.exec():
            self._cargar_tabla()

    def _dar_de_baja(self, objetivo_id: int, nombre: str) -> None:
        confirmar = QMessageBox.question(
            self, "Confirmar",
            f"¿Seguro que querés dar de baja '{nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            fecha_hoy = QDate.currentDate().toString("yyyy-MM-dd")
            dar_de_baja_objetivo(objetivo_id, fecha_hoy)

            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            registrar_accion(
                get_usuario_id(),
                f"Dio de baja objetivo: {nombre} | Fecha: {fecha_hoy}"
            )

            QMessageBox.information(self, "Listo", "Objetivo dado de baja correctamente.")
            self._cargar_tabla()

    def _eliminar_permanentemente(self, objetivo_id: int, nombre: str) -> None:
        """Elimina un objetivo de forma permanente de la base de datos.
        Solo disponible para administradores.
        """
        if get_rol() not in ("administrador", "admin"):
            QMessageBox.critical(
                self, "Acceso denegado",
                "Solo los administradores pueden eliminar objetivos permanentemente."
            )
            return

        confirmacion, ok = QInputDialog.getText(
            self,
            "Confirmación de eliminación",
            f"Escribí 'ELIMINAR' para confirmar la eliminación permanente de '{nombre}':"
        )

        if not ok or confirmacion != "ELIMINAR":
            QMessageBox.warning(
                self, "Cancelado",
                "La eliminación ha sido cancelada. Confirmación incorrecta."
            )
            return

        try:
            eliminar_objetivo(objetivo_id)

            from services.logger import registrar_accion
            from services.sesion import get_usuario_id
            registrar_accion(
                get_usuario_id(),
                f"⚠️ ELIMINÓ PERMANENTEMENTE objetivo: {nombre} (ID: {objetivo_id})"
            )

            QMessageBox.information(
                self, "✓ Eliminado",
                f"Objetivo '{nombre}' ha sido eliminado permanentemente de la base de datos."
            )
            self._cargar_tabla()

        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"No se pudo eliminar el objetivo: {str(e)}"
            )

    def _on_datos_cambiados(self, tabla, operacion, datos):
        """Maneja cambios de datos para refrescar la tabla."""
        if tabla == "objetivos":
            self._cargar_tabla()