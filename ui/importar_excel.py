# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Pantalla para importar datos desde Excel (pipeline services/importador/)
# =============================================================================

import os
from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.gestor_db import gestor_db
from models.objetivos import listar_objetivos
from models.supervisores import listar_supervisores
from services.logger import registrar_accion
from services.sesion import get_usuario_id

from services.importador import analizar_excel, confirmar_importacion
from services.importador import reporte as importador_reporte
from services.importador.modelos import (
    ResultadoAnalisis,
    ResultadoMatchObjetivo,
    ResultadoMatchSupervisor,
)
from services.importador.resolucion import EstadoResolucion


# =============================================================================
# Diálogo genérico de resolución (objetivos o supervisores)
# =============================================================================

class DialogoResolverCoincidencias(QDialog):
    """Resuelve un conjunto de nombres no reconocidos (objetivos o
    supervisores), eligiendo un registro existente o creando uno nuevo.

    `grupos` es una lista de dicts:
        {
            "resultado": ResultadoMatchObjetivo | ResultadoMatchSupervisor,
            "nombre_excel": str,
            "ids_problema": list[int],
        }
    """

    def __init__(self, titulo, grupos, nombres_existentes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(700)
        self.controles = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Elegí a qué registro existente corresponde cada nombre importado, "
            "o seleccioná 'Crear nuevo'."
        ))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(350)
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        for grupo in grupos:
            resultado = grupo["resultado"]
            nombre_excel = grupo["nombre_excel"]

            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            completer = QCompleter(nombres_existentes)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            combo.setCompleter(completer)
            combo.addItems(nombres_existentes)
            combo.addItem("-- Crear nuevo --")

            mejor_nombre = None
            if resultado.tipo == "sugerencias" and resultado.sugerencias:
                candidato = resultado.sugerencias[0]
                entidad = getattr(candidato, "objetivo", None) or getattr(candidato, "supervisor", None)
                mejor_nombre = entidad.nombre if entidad else None

            line_edit = QLineEdit()
            line_edit.setPlaceholderText("Nombre del nuevo registro")

            if mejor_nombre:
                combo.setCurrentText(mejor_nombre)
            else:
                combo.setCurrentIndex(combo.count() - 1)
                line_edit.setText(resultado.nombre_sugerido_nuevo or nombre_excel)

            line_edit.setVisible(combo.currentText() == "-- Crear nuevo --")

            combo.currentIndexChanged.connect(
                lambda _=None, line=line_edit, combo=combo: line.setVisible(
                    combo.currentText() == "-- Crear nuevo --"
                )
            )

            fila = QHBoxLayout()
            fila.addWidget(combo)
            fila.addWidget(line_edit)
            form_layout.addRow(nombre_excel, fila)

            self.controles.append((grupo, combo, line_edit))

        scroll_widget.setLayout(form_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def obtener_resoluciones(self):
        """Devuelve lista de (grupo, tipo, nombre_elegido)."""
        salida = []
        for grupo, combo, line_edit in self.controles:
            seleccionado = combo.currentText().strip()
            if seleccionado == "-- Crear nuevo --":
                nuevo = line_edit.text().strip()
                if not nuevo:
                    raise ValueError(
                        f"Completá el nombre nuevo para: {grupo['nombre_excel']}"
                    )
                salida.append((grupo, "nuevo", nuevo))
            else:
                salida.append((grupo, "existente", seleccionado))
        return salida


# =============================================================================
# Workers (segundo plano)
# =============================================================================

class AnalisisWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, ruta_archivo, anio, conexion_bd, forzar_sobrescritura):
        super().__init__()
        self.ruta_archivo = ruta_archivo
        self.anio = anio
        self.conexion_bd = conexion_bd
        self.forzar_sobrescritura = forzar_sobrescritura

    def run(self) -> None:
        try:
            resultado = analizar_excel(
                self.ruta_archivo,
                self.anio,
                self.conexion_bd,
                forzar_sobrescritura=self.forzar_sobrescritura,
            )
            self.finished.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


class ImportWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, analisis, resoluciones, usuario, conexion_bd):
        super().__init__()
        self.analisis = analisis
        self.resoluciones = resoluciones
        self.usuario = usuario
        self.conexion_bd = conexion_bd

    def run(self) -> None:
        try:
            resultado = confirmar_importacion(
                self.analisis, self.resoluciones, self.usuario, self.conexion_bd
            )
            self.finished.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


# =============================================================================
# Widget principal
# =============================================================================

class ImportarExcel(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Importar desde Excel")
        self.setGeometry(200, 200, 900, 700)

        self.ruta_archivo: Optional[str] = None
        self.analisis: Optional[ResultadoAnalisis] = None
        self.resoluciones: Optional[EstadoResolucion] = None

        self._analisis_thread = None
        self._analisis_worker = None
        self._import_thread = None
        self._import_worker = None

        layout = QVBoxLayout(self)

        titulo = QLabel("Importar datos desde Excel")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(titulo)

        fila_archivo = QHBoxLayout()
        self.label_archivo = QLabel("Ningún archivo seleccionado")
        self.label_archivo.setStyleSheet("color: #888;")
        boton_archivo = QPushButton("Seleccionar Excel")
        boton_archivo.clicked.connect(self._seleccionar_archivo)
        fila_archivo.addWidget(self.label_archivo)
        fila_archivo.addWidget(boton_archivo)
        layout.addLayout(fila_archivo)

        fila_opciones = QHBoxLayout()
        fila_opciones.addWidget(QLabel("Año:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2000, 2100)
        self.spin_anio.setValue(date.today().year)
        fila_opciones.addWidget(self.spin_anio)

        self.check_forzar = QCheckBox("Forzar sobrescritura de pasadas existentes")
        fila_opciones.addWidget(self.check_forzar)
        fila_opciones.addStretch()
        layout.addLayout(fila_opciones)

        self.boton_analizar = QPushButton("Analizar archivo")
        self.boton_analizar.setEnabled(False)
        self.boton_analizar.clicked.connect(self._analizar)
        layout.addWidget(self.boton_analizar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.resumen_label = QLabel("")
        self.resumen_label.setStyleSheet(
            "background-color: #263238; color: #ffffff; padding: 8px; border-radius: 4px;"
        )
        self.resumen_label.setWordWrap(True)
        self.resumen_label.setVisible(False)
        layout.addWidget(self.resumen_label)

        fila_matching = QHBoxLayout()
        self.boton_resolver_objetivos = QPushButton("Resolver objetivos")
        self.boton_resolver_objetivos.setEnabled(False)
        self.boton_resolver_objetivos.clicked.connect(self._resolver_objetivos)
        self.boton_resolver_supervisores = QPushButton("Resolver supervisores")
        self.boton_resolver_supervisores.setEnabled(False)
        self.boton_resolver_supervisores.clicked.connect(self._resolver_supervisores)
        fila_matching.addWidget(self.boton_resolver_objetivos)
        fila_matching.addWidget(self.boton_resolver_supervisores)
        layout.addLayout(fila_matching)

        self.lista_errores = QListWidget()
        self.lista_errores.setVisible(False)
        self.lista_errores.setStyleSheet(
            "color: #ffccbc; background-color: #1e1e1e; border: 1px solid #442200;"
        )
        self.lista_errores.setMinimumHeight(120)
        layout.addWidget(self.lista_errores)

        self.boton_descargar_informe = QPushButton("Descargar informe detallado")
        self.boton_descargar_informe.setEnabled(False)
        self.boton_descargar_informe.clicked.connect(self._descargar_informe)
        layout.addWidget(self.boton_descargar_informe)

        self.boton_importar = QPushButton("Importar datos")
        self.boton_importar.setFixedHeight(40)
        self.boton_importar.setEnabled(False)
        self.boton_importar.clicked.connect(self._importar)
        layout.addWidget(self.boton_importar)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        layout.addWidget(self.log)

    # ------------------------------------------------------------------
    # Selección de archivo
    # ------------------------------------------------------------------

    def _seleccionar_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)"
        )
        if ruta:
            self.ruta_archivo = ruta
            self.label_archivo.setText(os.path.basename(ruta))
            self.label_archivo.setStyleSheet("color: #4CAF50;")
            self.boton_analizar.setEnabled(True)
            self._resetear_resultado()

    def _resetear_resultado(self) -> None:
        self.analisis = None
        self.resoluciones = None
        self.resumen_label.setVisible(False)
        self.boton_resolver_objetivos.setEnabled(False)
        self.boton_resolver_objetivos.setText("Resolver objetivos")
        self.boton_resolver_supervisores.setEnabled(False)
        self.boton_resolver_supervisores.setText("Resolver supervisores")
        self.boton_descargar_informe.setEnabled(False)
        self.boton_importar.setEnabled(False)
        self.lista_errores.clear()
        self.lista_errores.setVisible(False)
        self.log.clear()

    # ------------------------------------------------------------------
    # Análisis (Fase 10) en segundo plano
    # ------------------------------------------------------------------

    def _analizar(self) -> None:
        if not self.ruta_archivo:
            return

        self._resetear_resultado()
        self.progress_bar.setVisible(True)
        self.boton_analizar.setEnabled(False)

        conexion = gestor_db.obtener_conexion()
        self._analisis_worker = AnalisisWorker(
            self.ruta_archivo,
            self.spin_anio.value(),
            conexion,
            self.check_forzar.isChecked(),
        )
        self._analisis_thread = QThread(self)
        self._analisis_worker.moveToThread(self._analisis_thread)
        self._analisis_thread.started.connect(self._analisis_worker.run)
        self._analisis_worker.finished.connect(self._on_analisis_listo)
        self._analisis_worker.error.connect(self._on_analisis_error)
        self._analisis_worker.finished.connect(self._analisis_thread.quit)
        self._analisis_worker.error.connect(self._analisis_thread.quit)
        self._analisis_worker.finished.connect(self._analisis_worker.deleteLater)
        self._analisis_worker.error.connect(self._analisis_worker.deleteLater)
        self._analisis_thread.finished.connect(self._analisis_thread.deleteLater)
        self._analisis_thread.start()

    def _on_analisis_listo(self, resultado: ResultadoAnalisis) -> None:
        self.progress_bar.setVisible(False)
        self.boton_analizar.setEnabled(True)

        self.analisis = resultado
        # usuario en EstadoResolucion es solo para el rastro de auditoría
        # de correcciones; importacion._usuario_id() sabe resolver un id
        # entero directamente.
        self.resoluciones = EstadoResolucion(usuario=get_usuario_id())

        self.resumen_label.setText(importador_reporte.generar_resumen_texto(resultado))
        self.resumen_label.setVisible(True)

        # Errores críticos: la pasada nunca se construyó (ej. hora
        # inválida), así que no hay nada que "resolver" acá. Hay que
        # corregir el Excel original y volver a analizarlo.
        criticos = [p for p in resultado.problemas if p.tipo == "error_critico"]
        self.lista_errores.clear()
        for p in criticos:
            self.lista_errores.addItem(
                f"[{p.hoja or '?'} fila {p.fila_excel or '?'}] {p.descripcion}"
            )
        self.lista_errores.setVisible(bool(criticos))
        self.boton_descargar_informe.setEnabled(bool(resultado.problemas))

        self.boton_resolver_objetivos.setEnabled(resultado.objetivos_para_revisar > 0)
        self.boton_resolver_supervisores.setEnabled(resultado.supervisores_para_revisar > 0)

        self._actualizar_boton_importar()

        if criticos:
            self.log.append(
                f"⚠ Hay {len(criticos)} errores críticos. Corregí el Excel "
                "original y volvé a analizarlo; no se resuelven desde acá."
            )

    def _on_analisis_error(self, mensaje: str) -> None:
        self.progress_bar.setVisible(False)
        self.boton_analizar.setEnabled(True)
        QMessageBox.critical(self, "Error", f"No se pudo analizar el archivo: {mensaje}")

    # ------------------------------------------------------------------
    # Resolución de matching (Fase 11-12)
    # ------------------------------------------------------------------

    def _ids_para_revisar(self, tipo_resultado) -> dict:
        """Agrupa los Problema 'para_revisar' de un tipo por identidad del
        ResultadoMatch, para no pedir resolver el mismo nombre más de una
        vez si aparece en varias pasadas."""
        grupos: dict[int, dict] = {}
        for idx, p in enumerate(self.analisis.problemas):
            if p.tipo != "para_revisar" or not isinstance(p.valor_problema, tipo_resultado):
                continue
            clave = id(p.valor_problema)
            grupos.setdefault(clave, {
                "resultado": p.valor_problema,
                "nombre_excel": p.valor_problema.nombre_excel,
                "ids_problema": [],
            })["ids_problema"].append(idx)
        return grupos

    def _resolver_grupo(self, tipo_resultado, nombres_existentes, titulo, boton) -> None:
        grupos = list(self._ids_para_revisar(tipo_resultado).values())
        if not grupos:
            return

        dialogo = DialogoResolverCoincidencias(titulo, grupos, nombres_existentes, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            resoluciones_dialogo = dialogo.obtener_resoluciones()
        except ValueError as exc:
            QMessageBox.warning(self, "Faltan datos", str(exc))
            return

        for grupo, tipo, nombre in resoluciones_dialogo:
            for id_problema in grupo["ids_problema"]:
                p = self.analisis.problemas[id_problema]
                if tipo == "existente":
                    self.resoluciones.registrar_match(id_problema, p.hoja, p.objetivo, nombre)
                else:
                    self.resoluciones.registrar_creacion(id_problema, p.hoja, p.objetivo, nombre)

        boton.setText(f"{titulo.split()[1].capitalize()} resueltos ({len(grupos)})")
        self._actualizar_boton_importar()

    def _resolver_objetivos(self) -> None:
        nombres = [o.nombre for o in listar_objetivos()]
        self._resolver_grupo(
            ResultadoMatchObjetivo, nombres, "Resolver objetivos", self.boton_resolver_objetivos
        )

    def _resolver_supervisores(self) -> None:
        nombres = [s.nombre for s in listar_supervisores()]
        self._resolver_grupo(
            ResultadoMatchSupervisor, nombres, "Resolver supervisores", self.boton_resolver_supervisores
        )

    def _actualizar_boton_importar(self) -> None:
        if not self.analisis:
            self.boton_importar.setEnabled(False)
            return

        hay_criticos = any(p.tipo == "error_critico" for p in self.analisis.problemas)
        ids_bloqueantes = [i for i, p in enumerate(self.analisis.problemas) if p.tipo == "para_revisar"]
        pendientes = (
            self.resoluciones.pendientes_bloqueantes(ids_bloqueantes)
            if self.resoluciones else ids_bloqueantes
        )

        self.boton_importar.setEnabled(not hay_criticos and not pendientes)

    # ------------------------------------------------------------------
    # Informe detallado descargable
    # ------------------------------------------------------------------

    def _descargar_informe(self) -> None:
        if not self.analisis:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", "informe_importacion.xlsx", "Excel (*.xlsx)"
        )
        if not ruta:
            return
        try:
            contenido = importador_reporte.generar_reporte_detallado(self.analisis)
            with open(ruta, "wb") as f:
                f.write(contenido)
            QMessageBox.information(self, "Listo", "Informe descargado correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo generar el informe: {exc}")

    # ------------------------------------------------------------------
    # Confirmación e importación (Fase 13-14) en segundo plano
    # ------------------------------------------------------------------

    def _importar(self) -> None:
        if not self.analisis or not self.resoluciones:
            return

        respuesta = QMessageBox.question(
            self, "Confirmar importación",
            "¿Confirmás la importación de los datos analizados?",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        self.boton_importar.setEnabled(False)
        self.progress_bar.setVisible(True)

        conexion = gestor_db.obtener_conexion()
        self._import_worker = ImportWorker(
            self.analisis, self.resoluciones, get_usuario_id(), conexion
        )
        self._import_thread = QThread(self)
        self._import_worker.moveToThread(self._import_thread)
        self._import_thread.started.connect(self._import_worker.run)
        self._import_worker.finished.connect(self._on_importacion_lista)
        self._import_worker.error.connect(self._on_importacion_error)
        self._import_worker.finished.connect(self._import_thread.quit)
        self._import_worker.error.connect(self._import_thread.quit)
        self._import_worker.finished.connect(self._import_worker.deleteLater)
        self._import_worker.error.connect(self._import_worker.deleteLater)
        self._import_thread.finished.connect(self._import_thread.deleteLater)
        self._import_thread.start()

    def _on_importacion_lista(self, resultado: dict) -> None:
        self.progress_bar.setVisible(False)

        self.log.append(f"✓ Pasadas nuevas: {resultado.get('pasadas_nuevas', 0)}")
        self.log.append(f"✓ Pasadas actualizadas: {resultado.get('pasadas_actualizadas', 0)}")
        self.log.append(f"✓ Pasadas omitidas: {resultado.get('pasadas_omitidas', 0)}")
        self.log.append(f"✓ Objetivos creados: {resultado.get('objetivos_creados', 0)}")
        self.log.append(f"✓ Supervisores creados: {resultado.get('supervisores_creados', 0)}")

        registrar_accion(
            get_usuario_id(),
            f"Importó Excel: {resultado.get('pasadas_nuevas', 0)} pasadas nuevas, "
            f"{resultado.get('pasadas_actualizadas', 0)} actualizadas desde "
            f"{os.path.basename(self.ruta_archivo)}",
        )

        QMessageBox.information(self, "Listo", resultado.get("mensaje", "Importación completada."))

        self._resetear_resultado()
        self.ruta_archivo = None
        self.label_archivo.setText("Ningún archivo seleccionado")
        self.label_archivo.setStyleSheet("color: #888;")
        self.boton_analizar.setEnabled(False)

    def _on_importacion_error(self, mensaje: str) -> None:
        self.progress_bar.setVisible(False)
        self.boton_importar.setEnabled(True)
        self.log.append(f"✗ Error: {mensaje}")
        QMessageBox.critical(self, "Error", f"No se pudo completar la importación: {mensaje}")