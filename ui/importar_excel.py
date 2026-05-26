# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla para importar datos desde Excel existente
# =============================================================================

from datetime import date

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
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
    QTableWidget,
    QTableWidgetItem,
    QCompleter,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.objetivos import agregar_objetivo, listar_objetivos
from services.importador_universal import get_importador
from services.logger import registrar_accion
from services.sesion import get_usuario_id


class DialogoResolverObjetivos(QDialog):
    """Dialogo para resolver objetivos importados que no existen aún."""

    def __init__(self, objetivos_faltantes, objetivos_existentes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resolver objetivos importados")
        self.setMinimumWidth(700)
        self.objetivos_faltantes = objetivos_faltantes
        self.objetivos_existentes = objetivos_existentes
        self.controles = []

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Ajustá el objetivo correspondiente para cada nombre importado. "
                "Si no existe, seleccioná 'Crear nuevo' y escribí el nombre."
            )
        )

        form_layout = QFormLayout()
        for nombre in objetivos_faltantes:
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            completer = QCompleter([obj.nombre for obj in objetivos_existentes])
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            combo.setCompleter(completer)
            combo.addItems([obj.nombre for obj in objetivos_existentes])
            combo.addItem("-- Crear nuevo --")
            combo.setCurrentIndex(0 if objetivos_existentes else combo.count() - 1)

            line_edit = QLineEdit()
            line_edit.setPlaceholderText("Nombre del nuevo objetivo")
            line_edit.setVisible(False)

            combo.currentIndexChanged.connect(
                lambda _=None, line=line_edit, combo=combo: self._alternar_linea(combo, line)
            )

            contenedor = QHBoxLayout()
            contenedor.addWidget(combo)
            contenedor.addWidget(line_edit)

            form_layout.addRow(nombre, contenedor)
            self.controles.append((nombre, combo, line_edit))

        layout.addLayout(form_layout)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _alternar_linea(self, combo: QComboBox, line_edit: QLineEdit) -> None:
        line_edit.setVisible(combo.currentText() == "-- Crear nuevo --")

    def obtener_mapeo(self):
        mapeo = {}
        for nombre, combo, line_edit in self.controles:
            seleccionado = combo.currentText()
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

            objetivo = next(
                (obj for obj in self.objetivos_existentes if obj.nombre == seleccionado),
                None,
            )
            if objetivo is None:
                raise ValueError(f"No se encontró el objetivo seleccionado: {seleccionado}")
            mapeo[nombre] = objetivo.id

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

    def __init__(self, importador, ruta_archivo, sheet_names=None, objetivo_mapeo=None):
        super().__init__()
        self.importador = importador
        self.ruta_archivo = ruta_archivo
        self.sheet_names = sheet_names
        self.objetivo_mapeo = objetivo_mapeo or {}
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
                sheet_names=self.sheet_names,
                progress_callback=self._on_progress,
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
        self.objetivo_mapeo = {}
        self.unresolved_objectives = []
        self.objetivos_pendientes_label = None
        self.objetivos_pendientes_lista = None

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

    def _limpiar_previsualizacion_thread(self) -> None:
        if self._preview_thread is not None and self._preview_thread.isRunning():
            self._preview_thread.quit()
            self._preview_thread.wait(200)
        self._preview_thread = None
        self._preview_worker = None

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
        self._limpiar_previsualizacion_thread()
        self.sheet_combo.blockSignals(True)
        self.sheet_combo.clear()
        self.sheet_combo.setEnabled(False)
        self.boton_importar.setEnabled(False)
        self.preview_table.setRowCount(0)
        self._hoja_previsualizacion_pedida = None
        self.objetivo_mapeo = {}
        self.unresolved_objectives = []
        self.objetivo_status.setText("No hay objetivos pendientes.")
        self.boton_resolver_objetivos.setEnabled(False)
        self._set_estado_previsualizacion("Previsualizando archivo...", "#ffd166")

        if not self.ruta_archivo:
            self._set_estado_previsualizacion("Esperando archivo...", "#a0a0a0")
            self.sheet_combo.blockSignals(False)
            return

        self._preview_token += 1
        token = self._preview_token
        self._preview_worker = PreviewWorker(get_importador(), self.ruta_archivo, token=token)
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
        self._actualizar_objetivos_no_resueltos()
        self._actualizar_resumen_objetivos([])
        self._actualizar_resumen_detalle(0, 0, 0, 0, "")

    def _solicitar_previsualizacion(self) -> None:
        if not self.ruta_archivo:
            return

        hoja_seleccionada = self.sheet_combo.currentData()
        self._hoja_previsualizacion_pedida = hoja_seleccionada
        self._limpiar_previsualizacion_thread()
        self.boton_importar.setEnabled(False)
        self.preview_table.setRowCount(0)
        self.objetivo_mapeo = {}
        self.unresolved_objectives = []
        self.objetivo_status.setText("No hay objetivos pendientes.")
        self.boton_resolver_objetivos.setEnabled(False)
        self._set_estado_previsualizacion("Actualizando previsualización...", "#ffd166")

        self._preview_token += 1
        token = self._preview_token
        sheet_names = [hoja_seleccionada] if hoja_seleccionada else None
        self._preview_worker = PreviewWorker(get_importador(), self.ruta_archivo, sheet_names=sheet_names, token=token)
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
        self._actualizar_objetivos_no_resueltos()
        self._actualizar_resumen_objetivos([])
        self._actualizar_resumen_detalle(0, 0, 0, 0, "")

    def _on_preview_cargado(self, token: int, preview: dict) -> None:
        if token != self._preview_token:
            return

        self._preview_thread = None
        self._preview_worker = None

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

        self.label_seleccion.setText("Seleccioná el día/turno que querés importar.")

        hoja_seleccionada = self.sheet_combo.currentData()
        registros = preview.get("registros", [])
        if hoja_seleccionada:
            registros = [registro for registro in registros if getattr(registro, "sheet_title", None) == hoja_seleccionada]

        if not registros:
            self.unresolved_objectives = []
            self.objetivo_status.setText("No hay objetivos pendientes.")
            self.boton_resolver_objetivos.setEnabled(False)
            self._set_estado_previsualizacion(
                "La hoja seleccionada no tiene registros detectados para previsualizar.",
                "#ff8a80",
            )
            self.preview_table.setRowCount(0)
            self._actualizar_objetivos_no_resueltos()
            self._actualizar_resumen_objetivos([])
            objetivos_no_resueltos = preview.get("objetivos_no_resueltos", [])
            self.unresolved_objectives = list(objetivos_no_resueltos)
            self._actualizar_resumen_detalle(
                len(registros),
                0,
                len(self.unresolved_objectives),
                len(preview.get('sheet_options', [])),
                hoja_seleccionada or "",
            )
            # validar registros para mostrar errores por fila
            self._validar_registros_preview(registros)
            self.boton_importar.setEnabled(True)
            return

        self._renderizar_tabla_previsualizacion(registros, hoja_seleccionada)
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
        objetivos_no_resueltos = preview.get("objetivos_no_resueltos", [])
        self.unresolved_objectives = list(objetivos_no_resueltos)
        if self.unresolved_objectives:
            self.objetivo_status.setText(
                f"Objetivos pendientes de resolución: {len(self.unresolved_objectives)}"
            )
            self.objetivo_status.setStyleSheet("color: #ffb74d; font-size: 11px;")
            self.boton_resolver_objetivos.setEnabled(True)
            self.boton_importar.setEnabled(False)
        else:
            self.objetivo_status.setText("No hay objetivos pendientes.")
            self.objetivo_status.setStyleSheet("color: #d0d0d0; font-size: 11px;")
            self.boton_resolver_objetivos.setEnabled(False)
            self.boton_importar.setEnabled(True)
        self._actualizar_objetivos_no_resueltos()
        self._set_estado_previsualizacion(
            f"Se encontraron {len(registros)} registros para importar en {hoja_seleccionada}.",
            "#8affc1",
        )

    def _on_preview_error(self, token: int, mensaje: str) -> None:
        if token != self._preview_token:
            return

        self._preview_thread = None
        self._preview_worker = None
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
        if not self.unresolved_objectives:
            self.objetivo_status.setText("No hay objetivos pendientes.")
            self.boton_resolver_objetivos.setEnabled(False)
            return

        objetivos_existentes = listar_objetivos()
        dialogo = DialogoResolverObjetivos(
            self.unresolved_objectives,
            objetivos_existentes,
            parent=self,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        self.objetivo_mapeo = dialogo.obtener_mapeo()
        incompletos = [o for o in self.unresolved_objectives if o not in self.objetivo_mapeo]
        if incompletos:
            self.unresolved_objectives = incompletos
            self.objetivo_status.setText(
                f"Faltan {len(incompletos)} objetivos por resolver."
            )
            self.objetivo_status.setStyleSheet("color: #ff8a80; font-size: 11px;")
        else:
            self.unresolved_objectives = []
            self.objetivo_status.setText("Todos los objetivos pendientes fueron resueltos.")
            self.objetivo_status.setStyleSheet("color: #8affc1; font-size: 11px;")
        self._actualizar_objetivos_no_resueltos()

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

            self.import_worker = ImportWorker(importador, self.ruta_archivo, sheet_names=[hoja_seleccionada] if hoja_seleccionada else None, objetivo_mapeo=self.objetivo_mapeo)
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

    def _on_import_finished(self, resultado) -> None:
        self.progress_bar.setVisible(False)
        self.boton_cancelar_importacion.setVisible(False)
        self.boton_importar.setEnabled(True)
        # mostrar resultado
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

    def _on_import_error(self, mensaje: str) -> None:
        self.progress_bar.setVisible(False)
        self.boton_cancelar_importacion.setVisible(False)
        self.boton_importar.setEnabled(True)
        self.log.append(f"✗ Error: {mensaje}")
        QMessageBox.critical(self, "Error", f"No se pudo completar la importación: {mensaje}")

    def _cancelar_importacion(self) -> None:
        try:
            if hasattr(self, 'import_worker'):
                self.import_worker.cancelled = True
                self.boton_cancelar_importacion.setEnabled(False)
                self.log.append("Solicitud de cancelación enviada...")
        except Exception:
            pass
