# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla de visualización de auditoría detallada
# =============================================================================

import json
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDateEdit, QComboBox,
    QPushButton, QMessageBox, QTextEdit, QTabWidget,
    QSplitter, QFileDialog, QHeaderView, QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import QDate, QSignalBlocker, Qt
from services.auditoria import (
    obtener_auditoria_usuario, obtener_auditoria_tabla,
    obtener_cambios_por_fecha, validar_integridad_auditoria,
    exportar_auditoria_csv, TipoOperacion
)
from services.sesion import get_usuario_id
from ui.components import StatusBadge
from ui.components.calendar import configure_calendar_theme
from ui.components.base import wrap_content_in_glass_card
from services.background_task import run_background_task
from services.usuarios import listar_usuarios, obtener_usuario_por_id
from ui.atajos import registrar_atajo
from ui.tabla_lotes import cargar_tabla_en_lotes
from ui.feedback import mostrar_error_usuario

logger = logging.getLogger(__name__)


def _obtener_nombre_usuario(usuario_id: int | None) -> str:
    """Obtiene el nombre de usuario por ID."""
    if not usuario_id:
        return "Sistema"
    usuario = obtener_usuario_por_id(usuario_id)
    return usuario["username"] if usuario else f"Usuario {usuario_id}"


class VistaAuditoria(QWidget):
    """Vista detallada de la auditoría del sistema."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auditoría del Sistema")
        self.resize(1100, 760)
        self.setMinimumSize(560, 360)

        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(12)
        layout_principal.setContentsMargins(12, 12, 12, 12)

        # Título
        titulo = QLabel("Auditoría del Sistema")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout_principal.addWidget(titulo)

        # Controles de filtrado
        controles_widget = QWidget()
        controles = QHBoxLayout(controles_widget)

        # Filtro por tipo de vista
        self.combo_vista = QComboBox()
        self.combo_vista.addItems([
            "Por Fecha",
            "Por Usuario",
            "Por Tabla",
            "Validar Integridad"
        ])
        self.combo_vista.currentTextChanged.connect(self._cambiar_vista)
        controles.addWidget(QLabel("Ver:"))
        controles.addWidget(self.combo_vista)

        # Fecha
        controles.addSpacing(20)
        controles.addWidget(QLabel("Fecha:"))
        self.selector_fecha = QDateEdit()
        self.selector_fecha.setDate(QDate.currentDate())
        self.selector_fecha.setCalendarPopup(True)
        configure_calendar_theme(self.selector_fecha)
        self.selector_fecha.dateChanged.connect(self._cargar_datos)
        controles.addWidget(self.selector_fecha)

        # Usuario (filtro)
        controles.addSpacing(20)
        controles.addWidget(QLabel("Usuario:"))
        self.combo_usuario = QComboBox()
        self._usuarios_cargados = False
        self._cargar_usuarios()
        self.combo_usuario.currentIndexChanged.connect(self._cargar_datos)
        controles.addWidget(self.combo_usuario)

        # Tabla (filtro)
        controles.addSpacing(20)
        controles.addWidget(QLabel("Tabla:"))
        self.combo_tabla = QComboBox()
        self.combo_tabla.addItems(["", "objetivos", "supervisores", "pasadas", "usuarios", "equipos"])
        self.combo_tabla.currentTextChanged.connect(self._cargar_datos)
        controles.addWidget(self.combo_tabla)

        # Botón exportar
        controles.addStretch()
        btn_exportar = QPushButton("📊 Exportar CSV")
        btn_exportar.setToolTip("Exportar el historial de auditoría a CSV")
        btn_exportar.setObjectName("PrimaryButton")
        btn_exportar.clicked.connect(self._exportar_auditoria)
        controles.addWidget(btn_exportar)

        scroll_controles = QScrollArea()
        scroll_controles.setWidgetResizable(True)
        scroll_controles.setFixedHeight(62)
        scroll_controles.setFrameShape(QFrame.Shape.NoFrame)
        scroll_controles.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_controles.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_controles.setWidget(controles_widget)
        layout_principal.addWidget(scroll_controles)

        # Tabs para diferentes vistas
        self.tabs = QTabWidget()

        # Tab 1: Tabla de auditoría
        self.tabla_auditoria = QTableWidget()
        self.tabla_auditoria.setColumnCount(8)
        self.tabla_auditoria.setHorizontalHeaderLabels([
            "Fecha/Hora", "Usuario", "Operación", "Tabla",
            "Reg. ID", "Detalles", "Estado", "Ver Cambios"
        ])
        header = self.tabla_auditoria.horizontalHeader()
        header.setMinimumSectionSize(48)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_auditoria.setWordWrap(True)
        self.tabla_auditoria.setAlternatingRowColors(True)
        self.tabs.addTab(self.tabla_auditoria, "Registros")

        # Tab 2: Detalles de cambios
        layout_detalles = QVBoxLayout()
        self.texto_cambios = QTextEdit()
        self.texto_cambios.setReadOnly(True)
        layout_detalles.addWidget(self.texto_cambios)
        widget_detalles = QWidget()
        widget_detalles.setLayout(layout_detalles)
        self.tabs.addTab(widget_detalles, "Cambios Detallados")

        # Tab 3: Validación de integridad
        layout_integridad = QVBoxLayout()
        self.texto_integridad = QTextEdit()
        self.texto_integridad.setReadOnly(True)
        btn_validar = QPushButton("🔍 Validar Integridad")
        btn_validar.setToolTip("Comprobar la integridad de los registros de auditoría")
        btn_validar.clicked.connect(self._validar_integridad)
        layout_integridad.addWidget(btn_validar)
        layout_integridad.addWidget(self.texto_integridad)
        widget_integridad = QWidget()
        widget_integridad.setLayout(layout_integridad)
        self.tabs.addTab(widget_integridad, "Integridad")

        self.estado_carga = QLabel()
        layout_principal.addWidget(self.estado_carga)
        self.barra_carga = QProgressBar()
        self.barra_carga.setRange(0, 0)
        self.barra_carga.setTextVisible(False)
        self.barra_carga.setMaximumHeight(5)
        self.barra_carga.hide()
        layout_principal.addWidget(self.barra_carga)
        layout_principal.addWidget(self.tabs)
        wrap_content_in_glass_card(self)

        self._carga_id = 0
        self._tareas_carga = {}
        registrar_atajo(self, "F5", self._cargar_datos)
        self._cargar_datos()

    def _cargar_usuarios(self) -> None:
        """Carga la lista de usuarios disponibles."""
        self.combo_usuario.setEnabled(False)
        self.combo_usuario.addItem("Cargando usuarios…", None)
        tarea = run_background_task(listar_usuarios)
        self._tarea_usuarios = tarea
        tarea.signals.finished.connect(self._mostrar_usuarios)
        tarea.signals.error.connect(self._error_cargar_usuarios)

    def _mostrar_usuarios(self, usuarios: list[dict]) -> None:
        self._tarea_usuarios = None
        bloqueador = QSignalBlocker(self.combo_usuario)
        self.combo_usuario.clear()
        self.combo_usuario.addItem("Todos", None)
        for usuario in usuarios:
            self.combo_usuario.addItem(usuario["username"], usuario["id"])
        del bloqueador
        self._usuarios_cargados = True
        self.combo_usuario.setEnabled(
            self.combo_vista.currentText() == "Por Usuario"
        )

    def _error_cargar_usuarios(self, mensaje: str) -> None:
        self._tarea_usuarios = None
        self._usuarios_cargados = False
        self.combo_usuario.setEnabled(False)
        logger.error("No se pudieron cargar los usuarios para auditoría: %s", mensaje)
        QMessageBox.critical(
            self,
            "Error",
            "No se pudieron cargar los usuarios para filtrar la auditoría.",
        )

    def _cambiar_vista(self) -> None:
        """Cambia la vista según la selección del combo."""
        vista = self.combo_vista.currentText()
        
        self.selector_fecha.setEnabled(vista == "Por Fecha")
        self.combo_usuario.setEnabled(
            vista == "Por Usuario" and self._usuarios_cargados
        )
        self.combo_tabla.setEnabled(vista == "Por Tabla")

        self._cargar_datos()

    def _cargar_datos(self) -> None:
        """Carga los datos de auditoría según los filtros."""
        self._cancelar_renderizado()
        vista = self.combo_vista.currentText()
        self._carga_id += 1
        solicitud = self._carga_id
        if vista == "Validar Integridad":
            self.tabla_auditoria.setRowCount(0)
            self.tabla_auditoria.setEnabled(True)
            self.barra_carga.hide()
            self.estado_carga.clear()
            return

        fecha = self.selector_fecha.date().toString("yyyy-MM-dd")
        usuario_id = self.combo_usuario.currentData()
        tabla = self.combo_tabla.currentText()
        self.estado_carga.setText("Cargando auditoría…")
        self.barra_carga.show()
        self.tabla_auditoria.setEnabled(False)
        tarea = run_background_task(
            self._consultar_datos_auditoria,
            vista,
            fecha,
            usuario_id,
            tabla,
        )
        self._tareas_carga[solicitud] = tarea
        tarea.signals.finished.connect(
            lambda resultado, id_solicitud=solicitud:
                self._mostrar_resultado_auditoria(id_solicitud, resultado)
        )
        tarea.signals.error.connect(
            lambda mensaje, id_solicitud=solicitud:
                self._error_carga_auditoria(id_solicitud, mensaje)
        )

    @staticmethod
    def _consultar_datos_auditoria(
        vista: str, fecha: str, usuario_id: int | None, tabla: str
    ) -> tuple[list, dict]:
        if vista == "Por Fecha":
            registros = obtener_cambios_por_fecha(fecha)
        elif vista == "Por Usuario":
            registros = (
                obtener_auditoria_usuario(usuario_id) if usuario_id else []
            )
        elif vista == "Por Tabla":
            registros = obtener_auditoria_tabla(tabla) if tabla else []
        else:
            registros = []

        nombres = {}
        for registro in registros:
            id_usuario = registro[2] if len(registro) > 2 else None
            if id_usuario is not None and id_usuario not in nombres:
                nombres[id_usuario] = _obtener_nombre_usuario(id_usuario)
        return registros, nombres

    def _mostrar_resultado_auditoria(
        self, solicitud: int, resultado: tuple[list, dict]
    ) -> None:
        self._tareas_carga.pop(solicitud, None)
        if solicitud != self._carga_id:
            return
        registros, nombres = resultado
        self._mostrar_registros(registros, nombres, solicitud)

    def _error_carga_auditoria(self, solicitud: int, mensaje: str) -> None:
        self._tareas_carga.pop(solicitud, None)
        if solicitud != self._carga_id:
            return
        self._cancelar_renderizado()
        self.tabla_auditoria.setEnabled(True)
        self.barra_carga.hide()
        self.estado_carga.setText("No se pudo cargar la auditoría.")
        mostrar_error_usuario(
            self,
            "No se cargó la auditoría",
            "No se pudieron cargar los datos de auditoría.",
            mensaje,
        )

    def _mostrar_registros(
        self, registros: list, nombres: dict, solicitud: int
    ) -> None:
        """Muestra los registros en la tabla."""

        def poblar_fila(i: int) -> None:
            registro = registros[i]
            # Los campos varían según el tipo de query, pero usamos índices seguros
            try:
                fecha_hora = f"{registro[0]} {registro[1]}"
                id_usuario = registro[2] if len(registro) > 2 else None
                usuario = nombres.get(
                    id_usuario,
                    "Sistema" if id_usuario is None else f"Usuario {id_usuario}",
                )
                tipo_op = registro[3] if len(registro) > 3 else ""
                tabla = registro[4] if len(registro) > 4 else ""
                reg_id = str(registro[5]) if len(registro) > 5 else ""
                detalles = registro[6] if len(registro) > 6 else ""
                estado = registro[7] if len(registro) > 7 else "EXITOSO"

                self.tabla_auditoria.setItem(i, 0, QTableWidgetItem(fecha_hora))
                self.tabla_auditoria.setItem(i, 1, QTableWidgetItem(usuario))
                self.tabla_auditoria.setItem(i, 2, QTableWidgetItem(tipo_op))
                self.tabla_auditoria.setItem(i, 3, QTableWidgetItem(tabla))
                self.tabla_auditoria.setItem(i, 4, QTableWidgetItem(reg_id))
                self.tabla_auditoria.setItem(i, 5, QTableWidgetItem(str(detalles)))
                
                badge_estado = StatusBadge(
                    estado, "ok" if estado == "EXITOSO" else "danger"
                )
                self.tabla_auditoria.setCellWidget(i, 6, badge_estado)

                # Botón ver cambios
                btn = QPushButton("Ver")
                btn.clicked.connect(lambda checked, r=registro: self._mostrar_cambios(r))
                self.tabla_auditoria.setCellWidget(i, 7, btn)

            except Exception as e:
                logger.error(
                    "No se pudo mostrar el registro de auditoría %s: %s", i, e
                )

        self._timer_render = cargar_tabla_en_lotes(
            self.tabla_auditoria,
            len(registros),
            poblar_fila,
            lambda: self._finalizar_render_auditoria(solicitud, registros),
        )

    def _finalizar_render_auditoria(
        self, solicitud: int, registros: list
    ) -> None:
        if solicitud != self._carga_id:
            return
        self._timer_render = None
        self.tabla_auditoria.setEnabled(True)
        self.barra_carga.hide()
        self.estado_carga.setText(
            "" if registros else "Todavía no hay registros para estos filtros."
        )

    def _cancelar_renderizado(self) -> None:
        timer = getattr(self, "_timer_render", None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            self._timer_render = None

    def _mostrar_cambios(self, registro: tuple) -> None:
        """Muestra los detalles de cambios de un registro."""
        try:
            texto = "=== DETALLES DEL CAMBIO ===\n\n"
            
            # Intentar extraer valores anteriores y nuevos
            if len(registro) > 7:
                valores_ant = registro[6]
                valores_nuev = registro[7]
                
                if valores_ant:
                    texto += "VALORES ANTERIORES:\n"
                    datos_ant = json.loads(valores_ant) if isinstance(valores_ant, str) else valores_ant
                    for clave, valor in datos_ant.items():
                        texto += f"  {clave}: {valor}\n"
                    texto += "\n"
                
                if valores_nuev:
                    texto += "VALORES NUEVOS:\n"
                    datos_nuev = json.loads(valores_nuev) if isinstance(valores_nuev, str) else valores_nuev
                    for clave, valor in datos_nuev.items():
                        texto += f"  {clave}: {valor}\n"
            
            self.texto_cambios.setText(texto)
            self.tabs.setCurrentIndex(1)

        except Exception as e:
            logger.error("No se pudieron procesar los cambios de auditoría: %s", e)
            self.texto_cambios.setText(
                "No se pudieron procesar los detalles de este cambio."
            )

    def _validar_integridad(self) -> None:
        """Valida la integridad de la auditoría."""
        resultado = validar_integridad_auditoria()
        
        texto = "=== VALIDACIÓN DE INTEGRIDAD ===\n\n"
        texto += f"Total de registros: {resultado.get('total_registros', 0)}\n"
        texto += f"Registros validados: {resultado.get('registros_validados', 0)}\n"
        texto += f"Estado: {'✅ VÁLIDO' if resultado.get('es_valido') else '❌ ANOMALÍAS DETECTADAS'}\n"
        
        if resultado.get('anomalias'):
            texto += "\nANOMALÍAS ENCONTRADAS:\n"
            for anomalia in resultado['anomalias']:
                texto += f"  ⚠️ {anomalia}\n"
        else:
            texto += "\nNo se detectaron anomalías.\n"
        
        self.texto_integridad.setText(texto)

    def _exportar_auditoria(self) -> None:
        """Exporta la auditoría a CSV."""
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar auditoría", "auditoria.csv", "CSV Files (*.csv)"
        )
        
        if ruta:
            fecha_inicio = self.selector_fecha.date().toString("yyyy-MM-dd")
            fecha_fin = fecha_inicio  # Por ahora, un día
            
            if exportar_auditoria_csv(fecha_inicio, fecha_fin, ruta):
                QMessageBox.information(self, "Listo", f"Auditoría exportada a:\n{ruta}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo exportar la auditoría")
