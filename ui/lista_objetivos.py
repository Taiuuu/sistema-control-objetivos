# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de listado y gestión de objetivos
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QDialog,
    QLabel, QLineEdit, QDateEdit, QCheckBox, QDialogButtonBox,
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
from ui.components import StatusBadge
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

        layout = QVBoxLayout()

        # Nombre
        layout.addWidget(QLabel("Nombre:"))
        self.input_nombre = QLineEdit(objetivo.nombre)
        layout.addWidget(self.input_nombre)

        # Fecha inicio
        layout.addWidget(QLabel("Fecha inicio:"))
        self.input_inicio = QDateEdit()
        self.input_inicio.setCalendarPopup(True)
        self.input_inicio.setDate(QDate.fromString(objetivo.fecha_inicio, "yyyy-MM-dd"))
        layout.addWidget(self.input_inicio)

        layout.addWidget(QLabel("Tipo de objetivo:"))
        self.selector_tipo = QComboBox()
        self.selector_tipo.addItem("Puntual", "puntual")
        self.selector_tipo.addItem("Intermitente", "intermitente")
        self.selector_tipo.setCurrentIndex(1 if objetivo.tipo_objetivo == "intermitente" else 0)
        layout.addWidget(self.selector_tipo)

        # Fecha fin opcional
        self.check_fin = QCheckBox("Tiene fecha de finalización:")
        self.check_fin.setChecked(objetivo.fecha_fin is not None)
        self.check_fin.toggled.connect(self._toggle_fecha_fin)
        layout.addWidget(self.check_fin)

        self.input_fin = QDateEdit()
        self.input_fin.setCalendarPopup(True)
        if objetivo.fecha_fin:
            self.input_fin.setDate(QDate.fromString(objetivo.fecha_fin, "yyyy-MM-dd"))
        else:
            self.input_fin.setDate(QDate.currentDate())
        self.input_fin.setEnabled(objetivo.fecha_fin is not None)
        layout.addWidget(self.input_fin)

        # Días de cobertura
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
        self.boton_periodo.clicked.connect(self._cambiar_periodo)
        layout.addWidget(self.boton_periodo)
        self._actualizar_boton_periodo()

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self.setLayout(layout)

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

        layout = QVBoxLayout()

        # Info de permisos
        rol_actual = get_rol()
        self.es_admin = rol_actual in ("administrador", "admin")
        
        if self.es_admin:
            info_label = QLabel("Modo administrador · permisos de gestión habilitados")
            info_label.setObjectName("AdminModeBanner")
            layout.addWidget(info_label)

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
        layout.addWidget(self.tabs)

        self.setLayout(layout)
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
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']};
                background: {tokens['surface']};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {tokens['surface_alt']};
                color: {tokens['text_secondary']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_lg']};
                padding: 7px 14px;
                margin: 0 4px 8px 0;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {tokens['accent']};
                color: {tokens['accent_text']};
                border-color: {tokens['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {tokens['sidebar_active_bg']};
                color: {tokens['text_primary']};
            }}
            QTableWidget {{
                background: {tokens['surface']};
                color: {tokens['text_primary']};
                border: none;
                gridline-color: transparent;
                outline: none;
                selection-background-color: {tokens['surface_alt']};
                selection-color: {tokens['text_primary']};
                font-size: {tokens['font_size_sm']};
            }}
            QTableWidget::item {{
                border-bottom: 1px solid {tokens['border']};
                padding: 6px 10px;
            }}
            QHeaderView::section {{
                background: {tokens['surface_alt']};
                color: {tokens['text_secondary']};
                border: none;
                border-bottom: 1px solid {tokens['border']};
                padding: 9px 10px;
                font-weight: 600;
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
                background: {tokens['sidebar_active_bg']};
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
        if hasattr(self, "tablas"):
            self._cargar_tabla()

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