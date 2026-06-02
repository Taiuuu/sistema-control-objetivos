# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla para importar datos desde Excel existente
# =============================================================================

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QListWidget,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QCompleter,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.objetivos import agregar_objetivo, listar_objetivos
from models.supervisores import agregar_supervisor, listar_supervisores
from services.importador_universal import get_importador
from services.logger import registrar_accion
from services.sesion import get_usuario_id


class DialogoResolverObjetivos(QDialog):
    """Dialogo para resolver objetivos importados."""

    def __init__(self, objetivos_faltantes, objetivos_existentes, initial_mapping=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resolver objetivos importados")
        self.setMinimumWidth(700)
        self.objetivos_faltantes = objetivos_faltantes
        self.objetivos_existentes = objetivos_existentes
        self.initial_mapping = initial_mapping or {}
        self.controles = []

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Ajustá el objetivo correspondiente para cada nombre importado. "
                "Si no existe, seleccioná 'Crear nuevo' y escribí el nombre."
            )
        )

        # Contenedor scrolleable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(350)

        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        existing_names = [obj.nombre for obj in objetivos_existentes]

        for nombre in objetivos_faltantes:
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

            completer = QCompleter(existing_names)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            combo.setCompleter(completer)

            combo.addItems(existing_names)
            combo.addItem("-- Crear nuevo --")

            mejor_coincidencia = self.initial_mapping.get(nombre)

            if not mejor_coincidencia:
                mejor_coincidencia = next(
                    (
                        obj.nombre
                        for obj in objetivos_existentes
                        if obj.nombre.strip().lower() == nombre.strip().lower()
                    ),
                    None,
                )

            if mejor_coincidencia:
                combo.setCurrentText(mejor_coincidencia)
            else:
                combo.setCurrentIndex(combo.count() - 1)

            line_edit = QLineEdit()
            line_edit.setPlaceholderText("Nombre del nuevo objetivo")

            line_edit.setVisible(
                combo.currentText() == "-- Crear nuevo --"
            )

            if combo.currentText() == "-- Crear nuevo --":
                line_edit.setText(nombre)

            combo.currentIndexChanged.connect(
                lambda _=None, line=line_edit, combo=combo:
                self._alternar_linea(combo, line)
            )

            contenedor = QHBoxLayout()
            contenedor.addWidget(combo)
            contenedor.addWidget(line_edit)

            form_layout.addRow(nombre, contenedor)

            self.controles.append((nombre, combo, line_edit))

        scroll_widget.setLayout(form_layout)

        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _alternar_linea(self, combo: QComboBox, line_edit: QLineEdit) -> None:
        line_edit.setVisible(combo.currentText() == "-- Crear nuevo --")

    def _buscar_objetivo_por_nombre(self, nombre: str):
        nombre_normalizado = str(nombre).strip().lower()
        return next(
            (
                obj
                for obj in self.objetivos_existentes
                if obj.nombre.strip().lower() == nombre_normalizado
            ),
            None,
        )

    def obtener_mapeo(self):
        mapeo = {}
        for nombre, combo, line_edit in self.controles:
            seleccionado = combo.currentText().strip()
            if seleccionado == "-- Crear nuevo --":
                nuevo_nombre = line_edit.text().strip()
                if not nuevo_nombre:
                    raise ValueError(f"Completá el nombre del objetivo para: {nombre}")

                objetivo = agregar_objetivo(
                    nuevo_nombre,
                    date.today().isoformat(),
                    "Lunes,Martes,Miércoles,Jueves,Viernes,Sábado,Domingo",
                )
                mapeo[nombre] = objetivo.id
                continue

            objetivo = self._buscar_objetivo_por_nombre(seleccionado)
            if objetivo is None:
                raise ValueError(f"No se encontró el objetivo seleccionado: {seleccionado}")
            mapeo[nombre] = objetivo.id

        return mapeo


class DialogoResolverSupervisores(QDialog):
    """Dialogo para resolver supervisores importados."""

    def __init__(self, supervisores_faltantes, supervisores_existentes, initial_mapping=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resolver supervisores importados")
        self.setMinimumWidth(700)
        self.supervisores_faltantes = supervisores_faltantes
        self.supervisores_existentes = supervisores_existentes
        self.initial_mapping = initial_mapping or {}
        self.controles = []

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Ajustá el supervisor correspondiente para cada nombre importado. "
                "Si no existe, seleccioná 'Crear nuevo' y escribí el nombre."
            )
        )

        # Contenedor scrolleable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(350)

        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        existing_names = [sup.nombre for sup in supervisores_existentes]

        for nombre in supervisores_faltantes:
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

            completer = QCompleter(existing_names)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            combo.setCompleter(completer)

            combo.addItems(existing_names)
            combo.addItem("-- Crear nuevo --")

            mejor_coincidencia = self.initial_mapping.get(nombre)

            if not mejor_coincidencia:
                mejor_coincidencia = next(
                    (
                        sup.nombre
                        for sup in supervisores_existentes
                        if sup.nombre.strip().lower() == nombre.strip().lower()
                    ),
                    None,
                )

            if mejor_coincidencia:
                combo.setCurrentText(mejor_coincidencia)
            else:
                combo.setCurrentIndex(combo.count() - 1)

            line_edit = QLineEdit()
            line_edit.setPlaceholderText("Nombre del nuevo supervisor")

            line_edit.setVisible(
                combo.currentText() == "-- Crear nuevo --"
            )

            if combo.currentText() == "-- Crear nuevo --":
                line_edit.setText(nombre)

            combo.currentIndexChanged.connect(
                lambda _=None, line=line_edit, combo=combo:
                self._alternar_linea(combo, line)
            )

            contenedor = QHBoxLayout()
            contenedor.addWidget(combo)
            contenedor.addWidget(line_edit)

            form_layout.addRow(nombre, contenedor)

            self.controles.append((nombre, combo, line_edit))

        scroll_widget.setLayout(form_layout)

        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _alternar_linea(self, combo: QComboBox, line_edit: QLineEdit) -> None:
        line_edit.setVisible(combo.currentText() == "-- Crear nuevo --")

    def _buscar_supervisor_por_nombre(self, nombre: str):
        nombre_normalizado = str(nombre).strip().lower()
        return next(
            (
                sup
                for sup in self.supervisores_existentes
                if sup.nombre.strip().lower() == nombre_normalizado
            ),
            None,
        )

    def obtener_mapeo(self):
        mapeo = {}
        for nombre, combo, line_edit in self.controles:
            seleccionado = combo.currentText().strip()
            if seleccionado == "-- Crear nuevo --":
                nuevo_nombre = line_edit.text().strip()
                if not nuevo_nombre:
                    raise ValueError(f"Completá el nombre del supervisor para: {nombre}")

                supervisor = agregar_supervisor(nuevo_nombre)
                mapeo[nombre] = supervisor.id
                continue

            supervisor = self._buscar_supervisor_por_nombre(seleccionado)
            if supervisor is None:
                raise ValueError(f"No se encontró el supervisor seleccionado: {seleccionado}")
            mapeo[nombre] = supervisor.id

        return mapeo


class DialogoAsignarTurnos(QDialog):
    """Dialogo para asignar 'diurno'/'nocturno' a hojas con turno indeterminado."""

    def __init__(self, sheet_options, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asignar turnos a hojas")
        self.setMinimumWidth(400)
        self.sheet_options = sheet_options
        self.controles = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Asigná el turno para cada hoja detectada sin turno:"))

        form_layout = QFormLayout()
        for opt in sheet_options:
            if opt.get('turno') in (None, ''):
                combo = QComboBox()
                combo.addItem("diurno")
                combo.addItem("nocturno")
                combo.setCurrentIndex(0)
                form_layout.addRow(opt.get('title', ''), combo)
                self.controles.append((opt.get('title'), combo))

        layout.addLayout(form_layout)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def obtener_mapeo(self):
        mapeo = {}
        for title, combo in self.controles:
            mapeo[title] = combo.currentText()
        return mapeo


class PreviewWorker(QObject):
    finished = pyqtSignal(int, dict)
    error = pyqtSignal(int, str)

    def __init__(self, importador, ruta_archivo, sheet_names=None, token=0):
        super().__init__()
        self.importador = importador
        self.ruta_archivo = ruta_archivo
        self.sheet_names = sheet_names
        self.token = token

    def run(self) -> None:
        try:
            preview = self.importador.previsualizar_archivo(
                self.ruta_archivo,
                sheet_names=self.sheet_names,
            )
            self.finished.emit(self.token, preview)
        except Exception as exc:
            self.error.emit(self.token, str(exc))


class ImportWorker(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, importador, ruta_archivo, sheet_names=None, objetivo_mapeo=None, supervisor_mapeo=None, sheet_turno_map=None, preview_precalculado=None, rango_desde=None, rango_hasta=None):
        super().__init__()
        self.importador = importador
        self.ruta_archivo = ruta_archivo
        self.sheet_names = sheet_names
        self.objetivo_mapeo = objetivo_mapeo or {}
        self.supervisor_mapeo = supervisor_mapeo or {}
        self.sheet_turno_map = sheet_turno_map or {}
        self.preview_precalculado = preview_precalculado  # NUEVO: para evitar doble parseo
        self.rango_desde = rango_desde
        self.rango_hasta = rango_hasta
        self.cancelled = False

    def _on_progress(self, processed: int, total: int) -> None:
        if self.cancelled:
            raise Exception("cancelled")
        self.progress.emit(processed, total)

    def run(self) -> None:
        try:
            resultado = self.importador.importar_control_recorridos(
                self.ruta_archivo,
                objetivo_mapeo=self.objetivo_mapeo,
                supervisor_mapeo=self.supervisor_mapeo,
                sheet_names=self.sheet_names,
                sheet_turno_map=self.sheet_turno_map,
                progress_callback=self._on_progress,
                preview_precalculado=self.preview_precalculado,  # NUEVO: pasar preview precalculado
            )
            self.finished.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


class ImportarExcel(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Importar desde Excel")
        self.setGeometry(200, 200, 900, 700)
        self.ruta_archivo = None
        self._preview_token = 0
        self._preview_thread = None
        self._preview_worker = None
        self._hoja_previsualizacion_pedida = None
        self._last_preview = None
        self._detected_objectives = []
        self.objetivo_mapeo = {}
        self.unresolved_objectives = []
        self._detected_supervisores = []
        self.supervisor_mapeo = {}
        self.unresolved_supervisores = []
        self.sheet_turno_map = {}
        self.objetivos_pendientes_label = None
        self.objetivos_pendientes_lista = None
        self.supervisores_pendientes_label = None
        self.supervisores_pendientes_lista = None
        # Rango de importación
        self.todas_las_hojas = []  # Lista ordenada de hojas (fecha, turno)
        self.rango_desde = None  # (fecha, turno) o None
        self.rango_hasta = None  # (fecha, turno) o None
        self.combo_rango_desde = None
        self.combo_rango_hasta = None
        # import worker/thread handles
        self.import_thread = None
        self.import_worker = None

        layout = QVBoxLayout()

        titulo = QLabel("Importar datos desde Excel")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(titulo)

        desc = QLabel(
            "Seleccioná el archivo y luego el día/turno que querés importar. "
            "Si el archivo tiene hojas tipo 27-5 (D) o 27-5 (N), podés ver y cargar una sola hoja."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(desc)

        fila_archivo = QHBoxLayout()
        self.label_archivo = QLabel("Ningún archivo seleccionado")
        self.label_archivo.setStyleSheet("color: #888;")
        boton_archivo = QPushButton("Seleccionar Excel")
        boton_archivo.clicked.connect(self._seleccionar_archivo)
        fila_archivo.addWidget(self.label_archivo)
        fila_archivo.addWidget(boton_archivo)
        layout.addLayout(fila_archivo)

        self.label_seleccion = QLabel("Seleccioná el día/turno que querés importar.")
        self.label_seleccion.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.label_seleccion)

        self.sheet_combo = QComboBox()
        self.sheet_combo.setEnabled(False)
        self.sheet_combo.currentIndexChanged.connect(self._solicitar_previsualizacion)
        layout.addWidget(self.sheet_combo)

        self.boton_asignar_turnos = QPushButton("Asignar turnos")
        self.boton_asignar_turnos.setEnabled(False)
        self.boton_asignar_turnos.clicked.connect(self._abrir_dialogo_asignar_turnos)
        layout.addWidget(self.boton_asignar_turnos)

        # Rango de fechas/turnos (opcional)
        rango_layout = QHBoxLayout()
        rango_layout.addWidget(QLabel("Filtrar por rango (opcional):"))
        
        rango_layout.addWidget(QLabel("Desde:"))
        self.combo_rango_desde = QComboBox()
        self.combo_rango_desde.setEnabled(False)
        self.combo_rango_desde.currentIndexChanged.connect(self._validar_rango)
        rango_layout.addWidget(self.combo_rango_desde)
        
        rango_layout.addWidget(QLabel("Hasta:"))
        self.combo_rango_hasta = QComboBox()
        self.combo_rango_hasta.setEnabled(False)
        self.combo_rango_hasta.currentIndexChanged.connect(self._validar_rango)
        rango_layout.addWidget(self.combo_rango_hasta)
        
        layout.addLayout(rango_layout)

        self.estado_banner = QLabel("Esperando archivo...")
        self.estado_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado_banner.setStyleSheet(
            "background-color: #263238; color: #ffffff; padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(self.estado_banner)

        self.preview_status = QLabel("Esperando archivo...")
        self.preview_status.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        layout.addWidget(self.preview_status)

        self.resumen_detalle_label = QLabel("")
        self.resumen_detalle_label.setStyleSheet("color: #b0bec5; font-size: 11px;")
        self.resumen_detalle_label.setWordWrap(True)
        self.resumen_detalle_label.setVisible(False)
        layout.addWidget(self.resumen_detalle_label)

        self.resumen_objetivos_label = QLabel("")
        self.resumen_objetivos_label.setStyleSheet("color: #c0c0c0; font-size: 11px;")
        self.resumen_objetivos_label.setWordWrap(True)
        self.resumen_objetivos_label.setVisible(False)
        layout.addWidget(self.resumen_objetivos_label)

        self.errors_list = QListWidget()
        self.errors_list.setVisible(False)
        self.errors_list.setStyleSheet("color: #ffccbc; background-color: #1e1e1e; border: 1px solid #442200;")
        self.errors_list.setMinimumHeight(100)
        layout.addWidget(self.errors_list)

        self.preview_table = QTableWidget(0, 7)
        self.preview_table.setHorizontalHeaderLabels(
            ["Hoja", "Fecha", "Hora", "Turno", "Supervisor", "Objetivo", "Notas"]
        )
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setMinimumHeight(260)
        self.preview_table.setStyleSheet(
            "QTableWidget { background-color: #1f1f1f; color: #f0f0f0; gridline-color: #444; }"
            "QHeaderView::section { background-color: #2a2a2a; color: #ffffff; padding: 4px; }"
        )
        layout.addWidget(self.preview_table)

        controles_objetivos = QHBoxLayout()
        self.objetivo_status = QLabel("No hay objetivos pendientes.")
        self.objetivo_status.setStyleSheet("color: #d0d0d0; font-size: 11px;")
        self.boton_resolver_objetivos = QPushButton("Resolver objetivos")
        self.boton_resolver_objetivos.setEnabled(False)
        self.boton_resolver_objetivos.clicked.connect(self._resolver_objetivos)
        controles_objetivos.addWidget(self.objetivo_status)
        controles_objetivos.addWidget(self.boton_resolver_objetivos)
        layout.addLayout(controles_objetivos)

        controles_supervisores = QHBoxLayout()
        self.supervisor_status = QLabel("No hay supervisores pendientes.")
        self.supervisor_status.setStyleSheet("color: #d0d0d0; font-size: 11px;")
        self.boton_resolver_supervisores = QPushButton("Resolver supervisores")
        self.boton_resolver_supervisores.setEnabled(False)
        self.boton_resolver_supervisores.clicked.connect(self._resolver_supervisores)
        controles_supervisores.addWidget(self.supervisor_status)
        controles_supervisores.addWidget(self.boton_resolver_supervisores)
        layout.addLayout(controles_supervisores)

        self.objetivos_pendientes_label = QLabel("Objetivos no encontrados en la base:")
        self.objetivos_pendientes_label.setStyleSheet("font-size: 12px; color: #f57f17; font-weight: bold;")
        self.objetivos_pendientes_label.setVisible(False)
        layout.addWidget(self.objetivos_pendientes_label)

        self.objetivos_pendientes_lista = QListWidget()
        self.objetivos_pendientes_lista.setVisible(False)
        self.objetivos_pendientes_lista.setMinimumHeight(100)
        self.objetivos_pendientes_lista.setStyleSheet(
            "QListWidget { background-color: #121212; color: #ffffff; border: 1px solid #444; }"
        )
        layout.addWidget(self.objetivos_pendientes_lista)

        self.supervisores_pendientes_label = QLabel("Supervisores no encontrados en la base:")
        self.supervisores_pendientes_label.setStyleSheet("font-size: 12px; color: #f57f17; font-weight: bold;")
        self.supervisores_pendientes_label.setVisible(False)
        layout.addWidget(self.supervisores_pendientes_label)

        self.supervisores_pendientes_lista = QListWidget()
        self.supervisores_pendientes_lista.setVisible(False)
        self.supervisores_pendientes_lista.setMinimumHeight(100)
        self.supervisores_pendientes_lista.setStyleSheet(
            "QListWidget { background-color: #121212; color: #ffffff; border: 1px solid #444; }"
        )
        layout.addWidget(self.supervisores_pendientes_lista)

        self.boton_importar = QPushButton("Importar datos")
        self.boton_importar.setFixedHeight(40)
        self.boton_importar.clicked.connect(self._importar)
        self.boton_importar.setEnabled(False)
        layout.addWidget(self.boton_importar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        self.boton_cancelar_importacion = QPushButton("Cancelar importación")
        self.boton_cancelar_importacion.setVisible(False)
        self.boton_cancelar_importacion.clicked.connect(self._cancelar_importacion)
        layout.addWidget(self.boton_cancelar_importacion)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.log)

        self.setLayout(layout)

        # Busy overlay (covers the widget to indicate background activity)
        self._overlay = QWidget(self)
        self._overlay.setVisible(False)
        self._overlay.setStyleSheet(
            "background-color: rgba(0,0,0,0.55); border-radius: 6px;"
        )
        ov_layout = QVBoxLayout(self._overlay)
        ov_layout.setContentsMargins(20, 20, 20, 20)
        ov_layout.setSpacing(10)
        self._overlay_label = QLabel("")
        self._overlay_label.setStyleSheet("color: #ffffff; font-size: 13px;")
        ov_layout.addWidget(self._overlay_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self._overlay_progress = QProgressBar()
        self._overlay_progress.setMinimum(0)
        self._overlay_progress.setMaximum(0)  # indeterminate by default
        self._overlay_progress.setFixedWidth(300)
        ov_layout.addWidget(self._overlay_progress, alignment=Qt.AlignmentFlag.AlignCenter)
        self._overlay.resize(self.size())

        # Timer to allow subtle UI animations if needed in future
        self._overlay_timer = QTimer(self)
        self._overlay_timer.setInterval(500)

    def _limpiar_previsualizacion_thread(self) -> None:
        if self._preview_thread is not None and self._preview_thread.isRunning():
            self._preview_thread.quit()
            self._preview_thread.wait(200)
        self._preview_thread = None
        self._preview_worker = None

    def _limpiar_import_thread(self) -> None:
        """Intentar limpiar el hilo/worker de importación si existe."""
        try:
            if getattr(self, 'import_thread', None) is not None and self.import_thread.isRunning():
                # solicitar cancelación al worker si está disponible
                if getattr(self, 'import_worker', None) is not None:
                    try:
                        self.import_worker.cancelled = True
                    except Exception:
                        pass
                self.import_thread.quit()
                self.import_thread.wait(200)
        except Exception:
            pass
        finally:
            self.import_thread = None
            self.import_worker = None

    def _show_busy_overlay(self, mensaje: str, determinate: bool = False) -> None:
        """Mostrar overlay que cubre la vista para indicar operación en segundo plano."""
        self._overlay_label.setText(mensaje)
        if determinate:
            # determinate: mostrar barra con rango 0-100
            self._overlay_progress.setRange(0, 100)
            self._overlay_progress.setValue(0)
        else:
            # indeterminate
            self._overlay_progress.setRange(0, 0)
        self._overlay.setGeometry(self.rect())
        self._overlay.setVisible(True)
        self._overlay.raise_()

    def _hide_busy_overlay(self) -> None:
        try:
            self._overlay.setVisible(False)
        except Exception:
            pass

    def resizeEvent(self, event):
        # mantener overlay cubriendo toda la vista
        try:
            if getattr(self, '_overlay', None) is not None:
                self._overlay.setGeometry(self.rect())
        except Exception:
            pass
        return super().resizeEvent(event)

    def _reset_previsualizacion(self) -> None:
        self.sheet_combo.blockSignals(True)
        self.sheet_combo.clear()
        self.sheet_combo.setEnabled(False)
        self.boton_importar.setEnabled(False)
        self.preview_table.setRowCount(0)
        self._hoja_previsualizacion_pedida = None
        self._detected_objectives = []
        self.objetivo_mapeo = {}
        self.unresolved_objectives = []
        self._detected_supervisores = []
        self.supervisor_mapeo = {}
        self.unresolved_supervisores = []
        self._last_preview = None
        self.objetivo_status.setText("No hay objetivos pendientes.")
        self.boton_resolver_objetivos.setEnabled(False)
        self.supervisor_status.setText("No hay supervisores pendientes.")
        self.boton_resolver_supervisores.setEnabled(False)
        self._actualizar_objetivos_no_resueltos()
        self._actualizar_supervisores_no_resueltos()
        self._actualizar_resumen_objetivos([])
        self._actualizar_resumen_detalle(0, 0, 0, 0, "")
        self.errors_list.clear()
        self.errors_list.setVisible(False)
        # Reset rango
        self._limpiar_combobox_rango()

    def _cargar_combobox_rango(self, sheet_options: List[Dict[str, Any]]) -> None:
        """Carga los combobox de rango con las hojas disponibles."""
        self.combo_rango_desde.blockSignals(True)
        self.combo_rango_hasta.blockSignals(True)
        
        self.combo_rango_desde.clear()
        self.combo_rango_hasta.clear()
        
        # Guardar lista ordenada de hojas
        self.todas_las_hojas = [
            (opt['fecha'], opt['turno'], opt['title'])
            for opt in sheet_options
            if opt.get('fecha') and opt.get('turno')
        ]
        
        # Agregar opción "Todas"
        self.combo_rango_desde.addItem("Todas", None)
        self.combo_rango_hasta.addItem("Todas", None)
        
        # Agregar opciones de hojas
        for fecha, turno, title in self.todas_las_hojas:
            label = f"{fecha} ({turno.upper()[0]})"
            self.combo_rango_desde.addItem(label, (fecha, turno))
            self.combo_rango_hasta.addItem(label, (fecha, turno))
        
        self.combo_rango_desde.setEnabled(len(self.todas_las_hojas) > 0)
        self.combo_rango_hasta.setEnabled(len(self.todas_las_hojas) > 0)
        
        self.combo_rango_desde.blockSignals(False)
        self.combo_rango_hasta.blockSignals(False)
    
    def _limpiar_combobox_rango(self) -> None:
        """Limpia los combobox de rango."""
        self.combo_rango_desde.blockSignals(True)
        self.combo_rango_hasta.blockSignals(True)
        
        self.combo_rango_desde.clear()
        self.combo_rango_hasta.clear()
        self.combo_rango_desde.setEnabled(False)
        self.combo_rango_hasta.setEnabled(False)
        
        self.todas_las_hojas = []
        self.rango_desde = None
        self.rango_hasta = None
        
        self.combo_rango_desde.blockSignals(False)
        self.combo_rango_hasta.blockSignals(False)
    
    def _validar_rango(self) -> None:
        """Valida y aplica el rango de fechas seleccionado."""
        rango_desde = self.combo_rango_desde.currentData()
        rango_hasta = self.combo_rango_hasta.currentData()
        
        # Si ambos son None, mostrar todos
        if rango_desde is None and rango_hasta is None:
            self.rango_desde = None
            self.rango_hasta = None
            self._actualizar_previsualizacion_actual()
            return
        
        # Validar que "desde" <= "hasta"
        if rango_desde is not None and rango_hasta is not None:
            desde_idx = next(
                (i for i, (f, t, _) in enumerate(self.todas_las_hojas) if (f, t) == rango_desde),
                -1
            )
            hasta_idx = next(
                (i for i, (f, t, _) in enumerate(self.todas_las_hojas) if (f, t) == rango_hasta),
                -1
            )
            
            if desde_idx > hasta_idx:
                # Intercambiar si es necesario
                self.combo_rango_desde.blockSignals(True)
                self.combo_rango_hasta.blockSignals(True)
                self.combo_rango_desde.setCurrentData(rango_hasta)
                self.combo_rango_hasta.setCurrentData(rango_desde)
                self.combo_rango_desde.blockSignals(False)
                self.combo_rango_hasta.blockSignals(False)
                rango_desde, rango_hasta = rango_hasta, rango_desde
        
        self.rango_desde = rango_desde
        self.rango_hasta = rango_hasta
        self._actualizar_previsualizacion_actual()
    
    def _actualizar_previsualizacion_actual(self) -> None:
        """Actualiza la previsualización actual con el rango aplicado."""
        if not self._last_preview:
            return
        
        registros = self._filtrar_registros_por_rango(
            self._last_preview.get("registros", [])
        )
        
        hoja_seleccionada = self.sheet_combo.currentData()
        if hoja_seleccionada:
            registros = [r for r in registros if getattr(r, "sheet_title", None) == hoja_seleccionada]
        
        self._renderizar_tabla_previsualizacion(registros, hoja_seleccionada)
    
    def _filtrar_registros_por_rango(self, registros: List[Any]) -> List[Any]:
        """Filtra registros por el rango de fechas/turnos seleccionado."""
        if self.rango_desde is None and self.rango_hasta is None:
            return registros
        
        from datetime import date
        
        def comparar_fecha_turno(registro_fecha: str, registro_turno: str, limite_fecha: date, limite_turno: str) -> int:
            """
            Compara fecha y turno de un registro con un límite.
            Retorna: -1 si registro < límite, 0 si =, 1 si > límite
            """
            try:
                reg_date = datetime.strptime(registro_fecha, "%Y-%m-%d").date()
                
                if reg_date < limite_fecha:
                    return -1
                elif reg_date > limite_fecha:
                    return 1
                else:
                    # Misma fecha, comparar turno
                    reg_turno_norm = str(registro_turno).strip().lower()
                    limite_turno_norm = str(limite_turno).strip().lower()
                    
                    if reg_turno_norm == limite_turno_norm:
                        return 0
                    elif reg_turno_norm in ('d', 'dia', 'diurno') and limite_turno_norm in ('n', 'noche', 'nocturno'):
                        return -1
                    elif reg_turno_norm in ('n', 'noche', 'nocturno') and limite_turno_norm in ('d', 'dia', 'diurno'):
                        return 1
                    else:
                        return 0
            except Exception:
                return 0
        
        filtrados = []
        for registro in registros:
            fecha_reg = registro.fecha
            turno_reg = registro.turno
            
            incluir = True
            
            # Validar desde
            if self.rango_desde is not None:
                cmp = comparar_fecha_turno(fecha_reg, turno_reg, self.rango_desde[0], self.rango_desde[1])
                if cmp < 0:
                    incluir = False
            
            # Validar hasta
            if self.rango_hasta is not None and incluir:
                cmp = comparar_fecha_turno(fecha_reg, turno_reg, self.rango_hasta[0], self.rango_hasta[1])
                if cmp > 0:
                    incluir = False
            
            if incluir:
                filtrados.append(registro)
        
        return filtrados

    def _set_estado_previsualizacion(self, mensaje: str, color: str = "#a0a0a0") -> None:
        self.preview_status.setText(mensaje)
        self.preview_status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.estado_banner.setText(mensaje)
        self.estado_banner.setStyleSheet(
            f"background-color: {color}; color: #263238; padding: 8px; border-radius: 4px;"
        )

    def _seleccionar_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)")
        if ruta:
            self.ruta_archivo = ruta
            self.label_archivo.setText(ruta.split("/")[-1].split("\\")[-1])
            self.label_archivo.setStyleSheet("color: #4CAF50;")
            self._cargar_previsualizacion()

    def _cargar_previsualizacion(self) -> None:
        self._reset_previsualizacion()
        self.sheet_turno_map = {}
        self._set_estado_previsualizacion("Previsualizando archivo...", "#ffd166")

        if not self.ruta_archivo:
            self._set_estado_previsualizacion("Esperando archivo...", "#a0a0a0")
            self.sheet_combo.blockSignals(False)
            return

        self._iniciar_previsualizacion_thread()

    def _iniciar_previsualizacion_thread(self, sheet_names=None) -> None:
        self._limpiar_previsualizacion_thread()
        self._preview_token += 1
        try:
            self._show_busy_overlay("Previsualizando archivo...", determinate=False)
        except Exception:
            pass
        token = self._preview_token
        self._preview_worker = PreviewWorker(
            get_importador(),
            self.ruta_archivo,
            sheet_names=sheet_names,
            token=token,
        )
        self._preview_thread = QThread(self)
        self._preview_worker.moveToThread(self._preview_thread)
        self._preview_thread.started.connect(self._preview_worker.run)
        self._preview_worker.finished.connect(self._on_preview_cargado)
        self._preview_worker.error.connect(self._on_preview_error)
        self._preview_worker.finished.connect(self._preview_thread.quit)
        self._preview_worker.error.connect(self._preview_thread.quit)
        self._preview_worker.finished.connect(self._preview_worker.deleteLater)
        self._preview_worker.error.connect(self._preview_worker.deleteLater)
        self._preview_thread.finished.connect(self._preview_thread.deleteLater)
        self._preview_thread.start()
        self.sheet_combo.blockSignals(False)

    def _solicitar_previsualizacion(self) -> None:
        if not self.ruta_archivo:
            return

        hoja_seleccionada = self.sheet_combo.currentData()
        self._hoja_previsualizacion_pedida = hoja_seleccionada
        self.boton_importar.setEnabled(False)
        self.preview_table.setRowCount(0)
        self.objetivo_status.setText("No hay objetivos pendientes.")
        self.boton_resolver_objetivos.setEnabled(False)
        self._set_estado_previsualizacion("Actualizando previsualización...", "#ffd166")

        sheet_names = [hoja_seleccionada] if hoja_seleccionada else None
        self._iniciar_previsualizacion_thread(sheet_names=sheet_names)

    def _on_preview_cargado(self, token: int, preview: dict) -> None:
        if token != self._preview_token:
            return

        # limpiar referencias al hilo/worker de previsualización (evita referencias colgantes)
        self._limpiar_previsualizacion_thread()
        try:
            self._hide_busy_overlay()
        except Exception:
            pass

        if preview.get("tipo") != "control_recorridos":
            self.sheet_combo.blockSignals(True)
            self.sheet_combo.clear()
            self.sheet_combo.setEnabled(False)
            self.sheet_combo.blockSignals(False)
            self.label_seleccion.setText("No se detectó CONTROL_RECORRIDOS. Se importará con el flujo legacy.")
            self._set_estado_previsualizacion(
                "El archivo no parece tener hojas con formato CONTROL_RECORRIDOS. Se usará la importación legacy.",
                "#ff8a80",
            )
            self.preview_table.setRowCount(0)
            self.boton_importar.setEnabled(True)
            return

        opciones = preview.get("sheet_options", [])
        self._last_preview = preview
        self._detected_objectives = preview.get("objetivos_detectados", [])
        if not opciones:
            self.label_seleccion.setText("No se encontraron hojas válidas en el archivo.")
            self._set_estado_previsualizacion("No se pudieron detectar hojas con el formato esperado.", "#ff8a80")
            self.preview_table.setRowCount(0)
            self.boton_importar.setEnabled(False)
            self.sheet_combo.setEnabled(False)
            return

        self.sheet_combo.blockSignals(True)
        self.sheet_combo.clear()
        for opcion in opciones:
            self.sheet_combo.addItem(
                f"{opcion['title']} | {opcion['fecha']} | {opcion['turno']}",
                opcion['title'],
            )

        # Habilitar asignar turnos si hay hojas sin turno
        tiene_indeterminadas = any(opt.get('turno') in (None, '') for opt in opciones)
        self.boton_asignar_turnos.setEnabled(tiene_indeterminadas)

        hoja_seleccionada = self._hoja_previsualizacion_pedida
        if hoja_seleccionada is None:
            hoja_seleccionada = self.sheet_combo.currentData()

        indice = 0
        if hoja_seleccionada is not None:
            indices = self.sheet_combo.findData(hoja_seleccionada)
            if indices >= 0:
                indice = indices

        self.sheet_combo.setCurrentIndex(indice)
        self.sheet_combo.setEnabled(True)
        self.sheet_combo.blockSignals(False)

        # Llenar combobox de rango de fechas
        self._cargar_combobox_rango(opciones)

        self.label_seleccion.setText("Seleccioná el día/turno que querés importar.")

        hoja_seleccionada = self.sheet_combo.currentData()
        registros = preview.get("registros", [])
        
        # Aplicar filtro de rango
        registros = self._filtrar_registros_por_rango(registros)
        
        if hoja_seleccionada:
            registros = [registro for registro in registros if getattr(registro, "sheet_title", None) == hoja_seleccionada]

        if not registros:
            self.unresolved_objectives = list(preview.get("objetivos_no_resueltos", []))
            self.objetivo_status.setText("No hay registros para previsualizar.")
            self.boton_resolver_objetivos.setEnabled(bool(self._detected_objectives))
            self._set_estado_previsualizacion(
                "La hoja seleccionada no tiene registros detectados para previsualizar.",
                "#ff8a80",
            )
            self.preview_table.setRowCount(0)
            self._actualizar_objetivos_no_resueltos()
            self._actualizar_resumen_objetivos([])
            self._actualizar_resumen_detalle(
                len(registros),
                0,
                len(self.unresolved_objectives),
                len(preview.get('sheet_options', [])),
                hoja_seleccionada or "",
            )
            self._validar_registros_preview(registros)
            self.boton_importar.setEnabled(True)
            return

        self._renderizar_tabla_previsualizacion(registros, hoja_seleccionada)
        
        # Procesar objetivos
        self._detected_objectives = preview.get("objetivos_detectados", [])
        objetivos_no_resueltos = preview.get("objetivos_no_resueltos", [])
        self.unresolved_objectives = list(objetivos_no_resueltos)
        
        # Procesar supervisores
        self._detected_supervisores = preview.get("supervisores_detectados", [])
        supervisores_no_resueltos = preview.get("supervisores_no_resueltos", [])
        self.unresolved_supervisores = list(supervisores_no_resueltos)
        
        self._actualizar_resumen_detalle(
            len(registros),
            len(set(registro.objetivo for registro in registros)),
            len(self.unresolved_objectives),
            len(preview.get('sheet_options', [])),
            hoja_seleccionada or "",
        )
        self._actualizar_resumen_objetivos(registros)
        # validar registros para mostrar errores por fila
        self._validar_registros_preview(registros)
        
        # Actualizar estado objetivos
        if self.unresolved_objectives:
            self.objetivo_status.setText(
                f"Objetivos pendientes de resolución: {len(self.unresolved_objectives)}"
            )
            self.objetivo_status.setStyleSheet("color: #ffb74d; font-size: 11px;")
            self.boton_resolver_objetivos.setEnabled(True)
            self.boton_importar.setEnabled(False)
        else:
            self.objetivo_status.setText(
                f"Objetivos detectados: {len(self._detected_objectives)}"
            )
            self.objetivo_status.setStyleSheet("color: #d0d0d0; font-size: 11px;")
            self.boton_resolver_objetivos.setEnabled(bool(self._detected_objectives))
        
        # Actualizar estado supervisores
        if self.unresolved_supervisores:
            self.supervisor_status.setText(
                f"Supervisores pendientes de resolución: {len(self.unresolved_supervisores)}"
            )
            self.supervisor_status.setStyleSheet("color: #ffb74d; font-size: 11px;")
            self.boton_resolver_supervisores.setEnabled(True)
            if not self.unresolved_objectives:
                self.boton_importar.setEnabled(False)
        else:
            self.supervisor_status.setText(
                f"Supervisores detectados: {len(self._detected_supervisores)}"
            )
            self.supervisor_status.setStyleSheet("color: #d0d0d0; font-size: 11px;")
            self.boton_resolver_supervisores.setEnabled(bool(self._detected_supervisores))
            if not self.unresolved_objectives:
                self.boton_importar.setEnabled(True)
        
        self._actualizar_objetivos_no_resueltos()
        self._actualizar_supervisores_no_resueltos()
        self._set_estado_previsualizacion(
            f"Se encontraron {len(registros)} registros para importar en {hoja_seleccionada}.",
            "#8affc1",
        )

    def _on_preview_error(self, token: int, mensaje: str) -> None:
        if token != self._preview_token:
            return
        # asegurarse de limpiar hilos previos
        self._limpiar_previsualizacion_thread()
        try:
            self._hide_busy_overlay()
        except Exception:
            pass
        self._set_estado_previsualizacion(f"No se pudo previsualizar el archivo: {mensaje}", "#ff8a80")
        self.preview_table.setRowCount(0)
        self.boton_importar.setEnabled(False)
        self._actualizar_resumen_objetivos([])
        self._actualizar_resumen_detalle(0, 0, 0, 0, "")

    def _renderizar_tabla_previsualizacion(self, registros, hoja_seleccionada: str) -> None:
        self.preview_table.setRowCount(0)
        headers = self.preview_table.horizontalHeader()
        headers.setStretchLastSection(True)

        for fila, registro in enumerate(registros[:100]):
            self.preview_table.insertRow(fila)
            valores = [
                hoja_seleccionada or getattr(registro, "sheet_title", ""),
                getattr(registro, "fecha", ""),
                getattr(registro, "hora", ""),
                getattr(registro, "turno", ""),
                getattr(registro, "supervisor", "") or "Sin supervisor",
                getattr(registro, "objetivo", ""),
                getattr(registro, "notas", "") or "",
            ]
            for columna, valor in enumerate(valores):
                self.preview_table.setItem(fila, columna, QTableWidgetItem(str(valor)))

        if len(registros) > 100:
            self.preview_table.setRowCount(100)
            self.preview_table.insertRow(100)
            self.preview_table.setItem(100, 0, QTableWidgetItem("..."))
            self.preview_table.setItem(100, 1, QTableWidgetItem(f"{len(registros) - 100} registros más"))
            for columna in range(2, 7):
                self.preview_table.setItem(100, columna, QTableWidgetItem(""))

    def _resolver_objetivos(self) -> None:
        if not self._detected_objectives:
            self.objetivo_status.setText("No hay objetivos detectados.")
            self.boton_resolver_objetivos.setEnabled(False)
            return

        objetivos_existentes = listar_objetivos()
        initial_mapping = {
            nombre: next(
                (
                    obj.nombre
                    for obj in objetivos_existentes
                    if obj.nombre.strip().lower() == nombre.strip().lower()
                ),
                None,
            )
            for nombre in self._detected_objectives
        }

        dialogo = DialogoResolverObjetivos(
            self._detected_objectives,
            objetivos_existentes,
            initial_mapping=initial_mapping,
            parent=self,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        self.objetivo_mapeo = dialogo.obtener_mapeo()
        incompletos = [o for o in self._detected_objectives if o not in self.objetivo_mapeo]
        if incompletos:
            self.unresolved_objectives = incompletos
            self.objetivo_status.setText(
                f"Faltan {len(incompletos)} objetivos por resolver."
            )
            self.objetivo_status.setStyleSheet("color: #ff8a80; font-size: 11px;")
            self.boton_importar.setEnabled(False)
        else:
            self.unresolved_objectives = []
            self.objetivo_status.setText(
                "Todos los objetivos pendientes fueron resueltos."
            )
            self.objetivo_status.setStyleSheet(
                "color: #8affc1; font-size: 11px;"
            )
            self.boton_resolver_objetivos.setEnabled(False)
            self.boton_importar.setEnabled(True)
        self._actualizar_objetivos_no_resueltos()

    def _resolver_supervisores(self) -> None:
        if not self._detected_supervisores:
            self.supervisor_status.setText("No hay supervisores detectados.")
            self.boton_resolver_supervisores.setEnabled(False)
            return

        supervisores_existentes = listar_supervisores()
        initial_mapping = {
            nombre: next(
                (
                    sup.nombre
                    for sup in supervisores_existentes
                    if sup.nombre.strip().lower() == nombre.strip().lower()
                ),
                None,
            )
            for nombre in self._detected_supervisores
        }

        dialogo = DialogoResolverSupervisores(
            self._detected_supervisores,
            supervisores_existentes,
            initial_mapping=initial_mapping,
            parent=self,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        self.supervisor_mapeo = dialogo.obtener_mapeo()
        incompletos = [s for s in self._detected_supervisores if s not in self.supervisor_mapeo]
        if incompletos:
            self.unresolved_supervisores = incompletos
            self.supervisor_status.setText(
                f"Faltan {len(incompletos)} supervisores por resolver."
            )
            self.supervisor_status.setStyleSheet("color: #ff8a80; font-size: 11px;")
            self.boton_importar.setEnabled(False)
        else:
            self.unresolved_supervisores = []
            self.supervisor_status.setText(
                "Todos los supervisores pendientes fueron resueltos."
            )
            self.supervisor_status.setStyleSheet(
                "color: #8affc1; font-size: 11px;"
            )
            self.boton_resolver_supervisores.setEnabled(False)
            if not self.unresolved_objectives:
                self.boton_importar.setEnabled(True)
        self._actualizar_supervisores_no_resueltos()

    def _importar(self) -> None:
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "Seleccioná un archivo Excel primero.")
            return

        importador = get_importador()
        self.log.clear()

        try:
            preview = importador.previsualizar_archivo(self.ruta_archivo)
            if preview.get("tipo") != "control_recorridos":
                self.log.append("No se detectó CONTROL_RECORRIDOS; usando importación legacy.")
                resultado = importador.importar_excel(self.ruta_archivo)
                # legacy import is synchronous
                self._handle_import_result(resultado)
                return

            hoja_seleccionada = self.sheet_combo.currentData()
            self.log.append(
                f"Detectado CONTROL_RECORRIDOS. Hoja seleccionada: {hoja_seleccionada or 'todas las hojas'}"
            )

            objetivos_no_resueltos = list(preview.get("objetivos_no_resueltos", []))
            if objetivos_no_resueltos and set(self.objetivo_mapeo.keys()) != set(objetivos_no_resueltos):
                self.log.append(
                    "Se requieren objetivos para continuar: " + ", ".join(objetivos_no_resueltos)
                )
                objetivos_existentes = listar_objetivos()
                dialogo = DialogoResolverObjetivos(
                    objetivos_no_resueltos,
                    objetivos_existentes,
                    parent=self,
                )
                if dialogo.exec() != QDialog.DialogCode.Accepted:
                    self.log.append("Importación cancelada por el usuario.")
                    return
                self.objetivo_mapeo = dialogo.obtener_mapeo()

            # Preparar worker de import
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.boton_cancelar_importacion.setVisible(True)
            self.boton_importar.setEnabled(False)

            # mostrar overlay durante importación (determinate)
            try:
                self._show_busy_overlay("Importando...", determinate=True)
            except Exception:
                pass

            # Preparar mapeo de turnos desde la UI (si existe)
            sheet_turno_map = self.sheet_turno_map
            # limpiar hilos de importación previos si existen
            self._limpiar_import_thread()

            # crear nuevo worker / thread con preview precalculado (evita doble parseo)
            self.import_worker = ImportWorker(
                importador,
                self.ruta_archivo,
                sheet_names=[hoja_seleccionada] if hoja_seleccionada else None,
                objetivo_mapeo=self.objetivo_mapeo,
                supervisor_mapeo=self.supervisor_mapeo,
                sheet_turno_map=sheet_turno_map,
                preview_precalculado=preview,  # NUEVO: pasar preview para evitar doble llamada
            )
            self.import_thread = QThread(self)
            self.import_worker.moveToThread(self.import_thread)
            self.import_thread.started.connect(self.import_worker.run)
            self.import_worker.progress.connect(self._on_import_progress)
            self.import_worker.finished.connect(self._on_import_finished)
            self.import_worker.error.connect(self._on_import_error)
            self.import_worker.finished.connect(self.import_thread.quit)
            self.import_worker.error.connect(self.import_thread.quit)
            self.import_worker.finished.connect(self.import_worker.deleteLater)
            self.import_worker.error.connect(self.import_worker.deleteLater)
            self.import_thread.finished.connect(self.import_thread.deleteLater)
            self.import_thread.start()

        except Exception as e:
            self.log.append(f"✗ Error: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo importar: {e}")

    def _handle_import_result(self, resultado) -> None:
        self.progress_bar.setVisible(False)
        self.boton_cancelar_importacion.setVisible(False)
        self.boton_importar.setEnabled(True)

        self.log.append(f"✓ Importados: {resultado.registros_validos}")
        self.log.append(f"✓ Duplicados omitidos: {resultado.registros_duplicados}")
        if resultado.errores:
            self.log.append("⚠ Errores:")
            for error in resultado.errores[:8]:
                self.log.append(f"  • {error}")

        if resultado.registros_validos > 0:
            registrar_accion(
                get_usuario_id(),
                f"Importó Excel: {resultado.registros_validos} pasadas desde "
                f"{self.ruta_archivo.split('/')[-1].split('\\')[-1]}",
            )

        if resultado.exitoso:
            QMessageBox.information(
                self,
                "Listo",
                f"Importación completada. {resultado.registros_validos} pasadas importadas.",
            )
        else:
            QMessageBox.warning(
                self,
                "Importación parcial",
                f"Se importaron {resultado.registros_validos} pasadas. Revisá el log para ver los errores.",
            )

    def _actualizar_objetivos_no_resueltos(self) -> None:
        if self.unresolved_objectives:
            self.objetivos_pendientes_label.setVisible(True)
            self.objetivos_pendientes_lista.setVisible(True)
            self.objetivos_pendientes_lista.clear()
            for nombre in self.unresolved_objectives:
                self.objetivos_pendientes_lista.addItem(nombre)
        else:
            self.objetivos_pendientes_label.setVisible(False)
            self.objetivos_pendientes_lista.setVisible(False)
            self.objetivos_pendientes_lista.clear()

    def _actualizar_supervisores_no_resueltos(self) -> None:
        if self.unresolved_supervisores:
            self.supervisores_pendientes_label.setVisible(True)
            self.supervisores_pendientes_lista.setVisible(True)
            self.supervisores_pendientes_lista.clear()
            for nombre in self.unresolved_supervisores:
                self.supervisores_pendientes_lista.addItem(nombre)
        else:
            self.supervisores_pendientes_label.setVisible(False)
            self.supervisores_pendientes_lista.setVisible(False)
            self.supervisores_pendientes_lista.clear()

    def _actualizar_resumen_objetivos(self, registros) -> None:
        if not registros:
            self.resumen_objetivos_label.setText("")
            self.resumen_objetivos_label.setVisible(False)
            return

        contador = {}
        for registro in registros:
            objetivo = getattr(registro, "objetivo", "") or "Sin objetivo"
            contador[objetivo] = contador.get(objetivo, 0) + 1

        lineas = [f"{nombre}: {cantidad} pasadas" for nombre, cantidad in sorted(contador.items())]
        if len(lineas) > 8:
            lineas = lineas[:8] + [f"... y {len(contador) - 8} objetivos más"]

        self.resumen_objetivos_label.setText(" | ".join(lineas))
        self.resumen_objetivos_label.setVisible(True)

    def _actualizar_resumen_detalle(
        self,
        total: int,
        objetivos: int,
        pendientes: int,
        hojas: int,
        hoja_seleccionada: str,
    ) -> None:
        if total == 0:
            self.resumen_detalle_label.setText("")
            self.resumen_detalle_label.setVisible(False)
            return

        partes = [f"Total registros: {total}", f"Objetivos detectados: {objetivos}", f"Pendientes: {pendientes}"]
        if hojas:
            partes.insert(0, f"Hojas detectadas: {hojas}")
        if hoja_seleccionada:
            partes.insert(1, f"Hoja: {hoja_seleccionada}")
        texto = " | ".join(partes)
        self.resumen_detalle_label.setText(texto)
        self.resumen_detalle_label.setVisible(True)

    def _validar_registros_preview(self, registros) -> None:
        """Valida registros y llena el panel de errores por fila."""
        self.errors_list.clear()
        if not registros:
            self.errors_list.setVisible(False)
            return

        importador = get_importador()
        errores = []
        for idx, registro in enumerate(registros, start=1):
            # validar turno
            if registro.turno not in ("diurno", "nocturno"):
                errores.append(f"Fila {idx}: Turno inválido: '{registro.turno}'")

            # validar fecha/hora
            try:
                datetime.strptime(registro.fecha, "%Y-%m-%d")
            except Exception:
                errores.append(f"Fila {idx}: Fecha inválida: '{registro.fecha}'")

            try:
                datetime.strptime(registro.hora, "%H:%M")
            except Exception:
                try:
                    # probar normalización
                    base = datetime.strptime(registro.fecha, "%Y-%m-%d").date()
                    importador._normalizar_hora_y_fecha(registro.hora, base)
                except Exception:
                    errores.append(f"Fila {idx}: Hora inválida: '{registro.hora}'")

        if errores:
            for e in errores:
                self.errors_list.addItem(e)
            self.errors_list.setVisible(True)
        else:
            self.errors_list.setVisible(False)

    def _on_import_progress(self, processed: int, total: int) -> None:
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(processed)
        self.estado_banner.setText(f"Importando... {processed}/{total}")
        try:
            # actualizar overlay si está visible y es determinate
            if getattr(self, '_overlay', None) is not None and self._overlay.isVisible():
                if self._overlay_progress.maximum() > 0 and total:
                    val = int(processed * 100 / total)
                    self._overlay_progress.setValue(val)
        except Exception:
            pass

    def _on_import_finished(self, resultado) -> None:
        try:
            self._handle_import_result(resultado)
        finally:
            # asegurar limpieza de recursos del hilo
            try:
                self._hide_busy_overlay()
            except Exception:
                pass
            self._limpiar_import_thread()

    def _on_import_error(self, mensaje: str) -> None:
        # limpiar recursos antes de actualizar UI
        try:
            self._hide_busy_overlay()
        except Exception:
            pass
        self._limpiar_import_thread()
        self.progress_bar.setVisible(False)
        self.boton_cancelar_importacion.setVisible(False)
        self.boton_importar.setEnabled(True)
        self.log.append(f"✗ Error: {mensaje}")
        QMessageBox.critical(self, "Error", f"No se pudo completar la importación: {mensaje}")

    def _cancelar_importacion(self) -> None:
        try:
            if getattr(self, 'import_worker', None) is not None:
                try:
                    self.import_worker.cancelled = True
                except Exception:
                    pass
                self.boton_cancelar_importacion.setEnabled(False)
                self.log.append("Solicitud de cancelación enviada...")

            # intentar detener el hilo si está corriendo
            if getattr(self, 'import_thread', None) is not None and self.import_thread.isRunning():
                try:
                    self.import_thread.quit()
                    self.import_thread.wait(200)
                except Exception:
                    pass
            # limpiar referencias
            self._limpiar_import_thread()
        except Exception:
            pass

    def _abrir_dialogo_asignar_turnos(self) -> None:
        if not self._last_preview:
            return

        opciones = self._last_preview.get('sheet_options', [])
        dialogo = DialogoAsignarTurnos(opciones, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        mapeo = dialogo.obtener_mapeo()
        # Guardar mapeo local
        self.sheet_turno_map = mapeo

        # Aplicar mapeo a la previsualización en memoria y refrescar vista
        registros = self._last_preview.get('registros', [])
        for r in registros:
            if getattr(r, 'sheet_title', None) in mapeo and (getattr(r, 'turno', None) in (None, '')):
                r.turno = mapeo.get(r.sheet_title)

        # Actualizar sheet_options turnos para display
        for opt in opciones:
            if opt.get('title') in mapeo:
                opt['turno'] = mapeo[opt.get('title')]

        # Re-renderizar la misma previsualización (simular carga)
        self._on_preview_cargado(self._preview_token, self._last_preview)
