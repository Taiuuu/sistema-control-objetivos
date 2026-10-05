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
from ui.widgets.dialogos import confirmar_mensaje, mostrar_mensaje
from ui.widgets.overlay_progreso import OverlayProgreso
from ui.widgets.toggle_switch import ToggleSwitch
from ui.theme.theme_manager import get_theme_manager


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

    OPCION_CREAR = "-- Crear nuevo --"
    OPCION_VINCULAR = "-- Vincular a otro nombre de este archivo --"

    def __init__(self, titulo, grupos, nombres_existentes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(700)
        self.controles = []
        es_resolucion_objetivos = "objetivos" in titulo.lower()

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
            combo.addItem(self.OPCION_CREAR)
            grupos_para_vincular = [otro for otro in grupos if otro is not grupo]
            if es_resolucion_objetivos and grupos_para_vincular:
                combo.addItem(self.OPCION_VINCULAR)

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
                combo.setCurrentText(self.OPCION_CREAR)
                line_edit.setText(resultado.nombre_sugerido_nuevo or nombre_excel)

            link_combo = QComboBox()
            link_combo.addItems([g["nombre_excel"] for g in grupos_para_vincular])
            link_combo.setVisible(False)
            link_combo.setMinimumWidth(220)
            link_label = QLabel("Vincular con:")
            link_label.setVisible(False)

            alias = QCheckBox("Guardar alias")
            alias.setVisible(False)

            def actualizar_controles(
                seleccion,
                line=line_edit,
                link=link_combo,
                label=link_label,
                alias_check=alias,
                es_objetivo=es_resolucion_objetivos,
            ):
                line.setVisible(seleccion == self.OPCION_CREAR)
                link.setVisible(seleccion == self.OPCION_VINCULAR)
                label.setVisible(seleccion == self.OPCION_VINCULAR)
                alias_check.setVisible(
                    es_objetivo
                    and seleccion not in (self.OPCION_CREAR, self.OPCION_VINCULAR)
                )

            combo.currentTextChanged.connect(actualizar_controles)
            actualizar_controles(combo.currentText())

            fila = QHBoxLayout()
            fila.addWidget(combo)
            fila.addWidget(line_edit)
            fila.addWidget(link_label)
            fila.addWidget(link_combo)
            fila.addWidget(alias)
            form_layout.addRow(nombre_excel, fila)

            self.controles.append(
                (grupo, combo, line_edit, alias, link_combo, grupos_para_vincular)
            )

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
        controles_por_grupo = {
            id(grupo): (combo, line_edit)
            for grupo, combo, line_edit, _, _, _ in self.controles
        }

        for grupo, combo, line_edit, alias, link_combo, grupos_para_vincular in self.controles:
            seleccionado = combo.currentText().strip()
            if seleccionado == self.OPCION_VINCULAR:
                grupo_objetivo = grupos_para_vincular[link_combo.currentIndex()]
                combo_objetivo, entrada_objetivo = controles_por_grupo[id(grupo_objetivo)]
                seleccion_objetivo = combo_objetivo.currentText().strip()
                if seleccion_objetivo == self.OPCION_VINCULAR:
                    raise ValueError(
                        f"Primero elegí un objetivo existente o nuevo para: "
                        f"{grupo_objetivo['nombre_excel']}"
                    )
                if seleccion_objetivo == self.OPCION_CREAR:
                    nombre_objetivo = entrada_objetivo.text().strip()
                else:
                    nombre_objetivo = seleccion_objetivo
                if not nombre_objetivo:
                    raise ValueError(
                        f"Completá o resolvé primero el objetivo: "
                        f"{grupo_objetivo['nombre_excel']}"
                    )
                salida.append((grupo, "alias", nombre_objetivo))
            elif seleccionado == self.OPCION_CREAR:
                nuevo = line_edit.text().strip()
                if not nuevo:
                    raise ValueError(
                        f"Completá el nombre nuevo para: {grupo['nombre_excel']}"
                    )
                salida.append((grupo, "nuevo", nuevo))
            else:
                tipo = "alias" if alias.isVisible() and alias.isChecked() else "existente"
                salida.append((grupo, tipo, seleccionado))
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

    def __init__(self, analisis, resoluciones, usuario, conexion_bd, forzar_sobrescritura=False):
        super().__init__()
        self.analisis = analisis
        self.resoluciones = resoluciones
        self.usuario = usuario
        self.conexion_bd = conexion_bd
        self.forzar_sobrescritura = forzar_sobrescritura

    def run(self) -> None:
        try:
            resultado = confirmar_importacion(
                self.analisis, self.resoluciones, self.usuario, self.conexion_bd,
                forzar_sobrescritura=self.forzar_sobrescritura,
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
        self.setObjectName("ImportarExcel")
        self.setWindowTitle("Importar desde Excel")
        self.setGeometry(200, 200, 900, 700)
        self._theme_manager = get_theme_manager()

        self.ruta_archivo: Optional[str] = None
        self.analisis: Optional[ResultadoAnalisis] = None
        self.resoluciones: Optional[EstadoResolucion] = None

        self._analisis_thread = None
        self._analisis_worker = None
        self._import_thread = None
        self._import_worker = None

        layout = QVBoxLayout(self)

        titulo = QLabel("Importar datos desde Excel")
        titulo.setObjectName("ImportTitle")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        fila_archivo = QHBoxLayout()
        self.label_archivo = QLabel("Ningún archivo seleccionado")
        self.label_archivo.setObjectName("ImportFileLabel")
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

        self.check_forzar = ToggleSwitch("Forzar sobrescritura")
        fila_opciones.addWidget(QLabel("Forzar sobrescritura"))
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
        self.resumen_label.setObjectName("ImportSummary")
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
        self.lista_errores.setObjectName("ImportErrors")
        self.lista_errores.setMinimumHeight(120)
        layout.addWidget(self.lista_errores)

        self.boton_descargar_informe = QPushButton("Descargar informe detallado")
        self.boton_descargar_informe.setEnabled(False)
        self.boton_descargar_informe.clicked.connect(self._descargar_informe)
        layout.addWidget(self.boton_descargar_informe)

        self.boton_importar = QPushButton("Importar datos")
        self.boton_importar.setObjectName("PrimaryButton")
        self.boton_importar.setFixedHeight(40)
        self.boton_importar.setEnabled(False)
        self.boton_importar.clicked.connect(self._importar)
        layout.addWidget(self.boton_importar)

        self.log = QTextEdit()
        self.log.setObjectName("ImportLog")
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        layout.addWidget(self.log)

        self.overlay_progreso = OverlayProgreso(self)
        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())

    def _aplicar_tema(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        self.setStyleSheet(f"""
            QLabel#ImportTitle {{
                color: {tokens['accent']};
                font-size: {tokens['font_size_title']};
                font-weight: 700;
            }}
            QLabel#ImportFileLabel {{
                color: {tokens['success_text'] if self.label_archivo.property('selected') else tokens['text_secondary']};
            }}
            QLabel#ImportSummary {{
                color: {tokens['text_primary']};
                background: {tokens['surface_alt']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_md']};
                padding: {tokens['spacing_sm']};
            }}
            QListWidget#ImportErrors, QTextEdit#ImportLog {{
                color: {tokens['text_primary']};
                background: {tokens['surface_alt']};
                border: 1px solid {tokens['border']};
                border-radius: {tokens['radius_sm']};
                padding: {tokens['spacing_sm']};
            }}
        """)

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
            self.label_archivo.setProperty("selected", True)
            self._aplicar_tema(self._theme_manager.current())
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
        self.overlay_progreso.mostrar("Analizando Excel...")
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
        self.overlay_progreso.ocultar()
        self.boton_analizar.setEnabled(True)

        self.analisis = resultado
        # usuario en EstadoResolucion es solo para el rastro de auditoría
        # de correcciones; importacion._usuario_id() sabe resolver un id
        # entero directamente.
        self.resoluciones = EstadoResolucion(usuario=get_usuario_id())

        self.resumen_label.setText(importador_reporte.generar_resumen_texto(resultado))
        self.resumen_label.setVisible(True)

        # Las pasadas sin una hora válida se muestran como advertencias y se
        # omiten de la importación, sin bloquear el resto del archivo.
        criticos = [p for p in resultado.problemas if p.tipo == "error_critico"]
        advertencias = [
            p for p in resultado.problemas
            if p.tipo == "advertencia"
            and "Hora normalizada automáticamente" not in p.descripcion
        ]
        self.lista_errores.clear()
        for p in criticos + advertencias:
            self.lista_errores.addItem(
                f"[{p.hoja or '?'} fila {p.fila_excel or '?'}] {p.descripcion}"
            )
        self.lista_errores.setVisible(bool(criticos or advertencias))
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
        self.overlay_progreso.ocultar()
        self.boton_analizar.setEnabled(True)
        mostrar_mensaje(self, "Error", f"No se pudo analizar el archivo: {mensaje}", "error")

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
            mostrar_mensaje(self, "Faltan datos", str(exc), "warning")
            return

        for grupo, tipo, nombre in resoluciones_dialogo:
            for id_problema in grupo["ids_problema"]:
                p = self.analisis.problemas[id_problema]
                if tipo == "existente":
                    self.resoluciones.registrar_match(id_problema, p.hoja, p.objetivo, nombre)
                elif tipo == "alias":
                    self.resoluciones.registrar_alias(id_problema, p.hoja, p.objetivo, nombre)
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
            mostrar_mensaje(self, "Listo", "Informe descargado correctamente.", "success")
        except Exception as exc:
            mostrar_mensaje(self, "Error", f"No se pudo generar el informe: {exc}", "error")

    # ------------------------------------------------------------------
    # Confirmación e importación (Fase 13-14) en segundo plano
    # ------------------------------------------------------------------

    def _importar(self) -> None:
        if not self.analisis or not self.resoluciones:
            return

        if not confirmar_mensaje(
            self,
            "Confirmar importación",
            "¿Confirmás la importación de los datos analizados?",
        ):
            return

        self.boton_importar.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.overlay_progreso.mostrar("Importando datos...")

        conexion = gestor_db.obtener_conexion()
        self._import_worker = ImportWorker(
            self.analisis, self.resoluciones, get_usuario_id(), conexion,
            self.check_forzar.isChecked(),
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
        self.overlay_progreso.ocultar()

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

        mostrar_mensaje(self, "Listo", resultado.get("mensaje", "Importación completada."), "success")

        self._resetear_resultado()
        self.ruta_archivo = None
        self.label_archivo.setText("Ningún archivo seleccionado")
        self.label_archivo.setProperty("selected", False)
        self._aplicar_tema(self._theme_manager.current())
        self.boton_analizar.setEnabled(False)

    def _on_importacion_error(self, mensaje: str) -> None:
        self.progress_bar.setVisible(False)
        self.overlay_progreso.ocultar()
        self.boton_importar.setEnabled(True)
        self.log.append(f"✗ Error: {mensaje}")
        mostrar_mensaje(self, "Error", f"No se pudo completar la importación: {mensaje}", "error")