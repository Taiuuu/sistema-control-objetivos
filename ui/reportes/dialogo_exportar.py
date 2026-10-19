"""Diálogo común para elegir el contenido y el formato de un informe."""

from __future__ import annotations

import calendar
import json
import logging
from datetime import date
from typing import Callable, Iterable, Mapping

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from services.permisos import tiene_permiso
from services.background_task import run_background_task
from services.reportes_unificados.modelos import ColumnaReporte, ReporteDatos
from ui.theme.theme_manager import ThemeManager

logger = logging.getLogger(__name__)
_PLANTILLAS_KEY = "reportes/plantillas"


class DialogoExportar(QDialog):
    """Centraliza las opciones de exportación y muestra una vista previa."""

    def __init__(
        self,
        tipo_informe: str,
        fecha_inicio: date,
        fecha_fin: date,
        filtros_iniciales: Mapping[str, object] | None = None,
        objetivos: Iterable[tuple[int, str]] = (),
        supervisores: Iterable[tuple[int, str]] = (),
        equipos: Iterable[tuple[int, str]] = (),
        columnas: Iterable[ColumnaReporte] = (),
        proveedor_vista_previa: Callable[[dict], ReporteDatos] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        if not tiene_permiso("reportes.exportar"):
            raise PermissionError("El usuario no tiene permiso para exportar reportes.")

        self.tipo_informe = tipo_informe
        self._proveedor_vista_previa = proveedor_vista_previa
        self._filtros_iniciales = dict(filtros_iniciales or {})
        self._datos_previa: ReporteDatos | None = None
        self._seleccion_previa: dict | None = None
        self._tarea_previa = None
        self._previsualizando = False
        self._columnas = tuple(columnas)
        self._theme_manager = ThemeManager.instance()
        self.setWindowTitle("Exportar")
        self.resize(900, 760)

        layout = QVBoxLayout(self)
        self._construir_periodo(layout, fecha_inicio, fecha_fin)
        self._construir_filtros(
            layout, self._filtros_iniciales, objetivos, supervisores, equipos
        )
        self._construir_columnas(layout)
        self._construir_contenido(layout)
        self._construir_vista_previa(layout)
        self._construir_plantillas(layout)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Continuar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self._theme_manager.theme_changed.connect(self._aplicar_tema)
        self._aplicar_tema(self._theme_manager.current())

    def _construir_periodo(
        self, layout: QVBoxLayout, fecha_inicio: date, fecha_fin: date
    ) -> None:
        grupo = QGroupBox("Período")
        forma = QFormLayout(grupo)
        self.selector_periodo = QComboBox()
        self.selector_periodo.addItem("Mes", "mes")
        self.selector_periodo.addItem("Rango de fechas", "rango")
        self.selector_periodo.addItem("Día", "dia")
        self.fecha_desde = self._crear_selector_fecha(fecha_inicio)
        self.fecha_hasta = self._crear_selector_fecha(fecha_fin)
        self.selector_periodo.currentIndexChanged.connect(self._actualizar_periodo)
        forma.addRow("Tipo:", self.selector_periodo)
        forma.addRow("Desde:", self.fecha_desde)
        forma.addRow("Hasta:", self.fecha_hasta)
        layout.addWidget(grupo)

    @staticmethod
    def _crear_selector_fecha(fecha: date) -> QDateEdit:
        selector = QDateEdit(QDate(fecha.year, fecha.month, fecha.day))
        selector.setCalendarPopup(True)
        selector.setDisplayFormat("dd/MM/yyyy")
        return selector

    def _construir_filtros(
        self,
        layout: QVBoxLayout,
        filtros_iniciales: Mapping[str, object],
        objetivos: Iterable[tuple[int, str]],
        supervisores: Iterable[tuple[int, str]],
        equipos: Iterable[tuple[int, str]],
    ) -> None:
        grupo = QGroupBox("Filtros")
        grilla = QGridLayout(grupo)

        self.todos_objetivos = QCheckBox("Todos los objetivos")
        self.todos_objetivos.setChecked(True)
        self.todos_objetivos.toggled.connect(self._alternar_objetivos)
        self.busqueda_objetivos = QLineEdit()
        self.busqueda_objetivos.setPlaceholderText("Buscar objetivo")
        self.busqueda_objetivos.textChanged.connect(self._filtrar_objetivos)
        self.lista_objetivos = self._crear_lista(objetivos)
        self.lista_objetivos.setMaximumHeight(110)

        self.lista_supervisores = self._crear_lista(supervisores)
        self.lista_supervisores.setMaximumHeight(110)
        self.todos_supervisores = QCheckBox("Todos los supervisores")
        self.todos_supervisores.setChecked(True)
        self.todos_supervisores.toggled.connect(self._alternar_supervisores)
        self.lista_equipos = QComboBox()
        self.lista_equipos.addItem("Todos los equipos", None)
        for equipo_id, nombre in equipos:
            self.lista_equipos.addItem(nombre, equipo_id)

        self.turno_dia = QCheckBox("Día")
        self.turno_noche = QCheckBox("Noche")
        self.turno_dia.setChecked(True)
        self.turno_noche.setChecked(True)
        self._aplicar_filtro_inicial(filtros_iniciales)

        grilla.addWidget(self.todos_objetivos, 0, 0, 1, 2)
        grilla.addWidget(self.busqueda_objetivos, 1, 0, 1, 2)
        grilla.addWidget(self.lista_objetivos, 2, 0, 1, 2)
        grilla.addWidget(QLabel("Supervisores:"), 0, 2)
        grilla.addWidget(self.lista_supervisores, 1, 2, 2, 1)
        grilla.addWidget(self.todos_supervisores, 4, 2, 1, 1)
        grilla.addWidget(QLabel("Equipo:"), 3, 0)
        grilla.addWidget(self.lista_equipos, 3, 1)
        turnos = QHBoxLayout()
        turnos.addWidget(self.turno_dia)
        turnos.addWidget(self.turno_noche)
        grilla.addWidget(QLabel("Turnos:"), 3, 2)
        grilla.addLayout(turnos, 3, 3)
        layout.addWidget(grupo)

    @staticmethod
    def _crear_lista(opciones: Iterable[tuple[int, str]]) -> QListWidget:
        lista = QListWidget()
        for identificador, etiqueta in opciones:
            item = QListWidgetItem(etiqueta)
            item.setData(Qt.ItemDataRole.UserRole, identificador)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            lista.addItem(item)
        return lista

    def _aplicar_filtro_inicial(self, filtros: Mapping[str, object]) -> None:
        supervisor_id = filtros.get("supervisor_id")
        if supervisor_id is not None:
            self.todos_supervisores.setChecked(False)
            self._seleccionar_ids(self.lista_supervisores, {supervisor_id})
        objetivo_id = filtros.get("objetivo_id")
        if objetivo_id is not None:
            self.todos_objetivos.setChecked(False)
            self._seleccionar_ids(self.lista_objetivos, {objetivo_id})
        turno = str(filtros.get("turno") or "").strip().lower()
        if turno in {"diurno", "dia", "d"}:
            self.turno_dia.setChecked(True)
            self.turno_noche.setChecked(False)
        elif turno in {"nocturno", "noche", "n"}:
            self.turno_dia.setChecked(False)
            self.turno_noche.setChecked(True)

    @staticmethod
    def _seleccionar_ids(lista: QListWidget, ids: set[object]) -> None:
        for indice in range(lista.count()):
            item = lista.item(indice)
            item.setCheckState(
                Qt.CheckState.Checked
                if item.data(Qt.ItemDataRole.UserRole) in ids
                else Qt.CheckState.Unchecked
            )

    def _alternar_objetivos(self, todos: bool) -> None:
        self.lista_objetivos.setEnabled(not todos)
        self.busqueda_objetivos.setEnabled(not todos)

    def _alternar_supervisores(self, todos: bool) -> None:
        self.lista_supervisores.setEnabled(not todos)

    def _filtrar_objetivos(self, texto: str) -> None:
        texto = texto.casefold().strip()
        for indice in range(self.lista_objetivos.count()):
            item = self.lista_objetivos.item(indice)
            item.setHidden(texto not in item.text().casefold())

    def _construir_columnas(self, layout: QVBoxLayout) -> None:
        grupo = QGroupBox("Columnas y orden")
        fila = QHBoxLayout(grupo)
        self.lista_columnas = QListWidget()
        for columna in self._columnas:
            item = QListWidgetItem(columna.etiqueta)
            item.setData(Qt.ItemDataRole.UserRole, columna.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.lista_columnas.addItem(item)

        acciones = QVBoxLayout()
        self.boton_subir = QPushButton("Subir")
        self.boton_bajar = QPushButton("Bajar")
        self.boton_subir.clicked.connect(lambda: self._mover_columna(-1))
        self.boton_bajar.clicked.connect(lambda: self._mover_columna(1))
        acciones.addWidget(self.boton_subir)
        acciones.addWidget(self.boton_bajar)
        acciones.addStretch()
        fila.addWidget(self.lista_columnas)
        fila.addLayout(acciones)
        layout.addWidget(grupo)

    def _mover_columna(self, desplazamiento: int) -> None:
        indice = self.lista_columnas.currentRow()
        destino = indice + desplazamiento
        if indice < 0 or not 0 <= destino < self.lista_columnas.count():
            return
        item = self.lista_columnas.takeItem(indice)
        self.lista_columnas.insertItem(destino, item)
        self.lista_columnas.setCurrentRow(destino)

    def _construir_contenido(self, layout: QVBoxLayout) -> None:
        grupo = QGroupBox("Contenido")
        forma = QFormLayout(grupo)
        self.selector_contenido = QComboBox()
        self.selector_contenido.addItem("Resumen", "resumen")
        self.selector_contenido.addItem("Detalle de pasadas", "detalle")
        self.selector_contenido.addItem("Resumen y detalle", "ambos")
        self.incluir_totales = QCheckBox("Incluir totales")
        self.incluir_totales.setChecked(True)
        self.incluir_notas = QCheckBox("Incluir observaciones o notas diarias")
        self.selector_agrupacion = QComboBox()
        self.selector_agrupacion.addItem("Sin agrupación", "ninguna")
        self.selector_agrupacion.addItem("Por objetivo", "objetivo")
        self.selector_agrupacion.addItem("Por supervisor", "supervisor")
        self.selector_agrupacion.addItem("Por día", "dia")
        self.selector_formato = QComboBox()
        self.selector_formato.addItem("Excel", "excel")
        self.selector_formato.addItem("PDF", "pdf")
        self.selector_formato.addItem("Excel y PDF", "ambos")
        forma.addRow("Mostrar:", self.selector_contenido)
        forma.addRow(self.incluir_totales)
        forma.addRow(self.incluir_notas)
        forma.addRow("Agrupar:", self.selector_agrupacion)
        forma.addRow("Formato:", self.selector_formato)
        layout.addWidget(grupo)

    def _construir_vista_previa(self, layout: QVBoxLayout) -> None:
        fila = QHBoxLayout()
        self.boton_previsualizar = QPushButton("Actualizar vista previa")
        self.boton_previsualizar.clicked.connect(self._actualizar_vista_previa)
        self.cantidad_filas = QLabel("Vista previa pendiente")
        fila.addWidget(self.boton_previsualizar)
        fila.addWidget(self.cantidad_filas)
        layout.addLayout(fila)
        self.tabla_previa = QTableWidget()
        self.tabla_previa.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_previa.setMaximumHeight(150)
        layout.addWidget(self.tabla_previa)

    def _construir_plantillas(self, layout: QVBoxLayout) -> None:
        fila = QHBoxLayout()
        self.selector_plantilla = QComboBox()
        self.nombre_plantilla = QLineEdit()
        self.nombre_plantilla.setPlaceholderText("Nombre de plantilla")
        self.boton_guardar_plantilla = QPushButton("Guardar plantilla")
        self.boton_cargar_plantilla = QPushButton("Usar plantilla")
        self.boton_guardar_plantilla.clicked.connect(self._guardar_plantilla)
        self.boton_cargar_plantilla.clicked.connect(self._cargar_plantilla)
        fila.addWidget(self.selector_plantilla)
        fila.addWidget(self.boton_cargar_plantilla)
        fila.addWidget(self.nombre_plantilla)
        fila.addWidget(self.boton_guardar_plantilla)
        layout.addLayout(fila)
        self._refrescar_plantillas()

    def _actualizar_periodo(self) -> None:
        es_dia = self.selector_periodo.currentData() == "dia"
        self.fecha_hasta.setEnabled(not es_dia)

    def _selection(self) -> dict:
        tipo_periodo = str(self.selector_periodo.currentData())
        desde = self.fecha_desde.date().toPyDate()
        hasta = self.fecha_hasta.date().toPyDate()
        if tipo_periodo == "dia":
            hasta = desde
        elif tipo_periodo == "mes":
            desde = desde.replace(day=1)
            ultimo_dia = calendar.monthrange(desde.year, desde.month)[1]
            hasta = desde.replace(day=ultimo_dia)
        if hasta < desde:
            raise ValueError("La fecha final no puede ser anterior a la inicial")

        objetivo_ids = (
            None
            if self.todos_objetivos.isChecked()
            else self._ids_seleccionados(self.lista_objetivos)
        )
        return {
            "tipo_informe": self.tipo_informe,
            "filtros_pantalla": dict(self._filtros_iniciales),
            "tipo_periodo": tipo_periodo,
            "fecha_inicio": desde,
            "fecha_fin": hasta,
            "objetivo_ids": objetivo_ids,
            "supervisor_ids": (
                None
                if self.todos_supervisores.isChecked()
                else self._ids_seleccionados(self.lista_supervisores)
            ),
            "equipo_id": self.lista_equipos.currentData(),
            "turnos": [
                turno
                for marcado, turno in (
                    (self.turno_dia.isChecked(), "diurno"),
                    (self.turno_noche.isChecked(), "nocturno"),
                )
                if marcado
            ],
            "columnas": self._columnas_seleccionadas(),
            "contenido": str(self.selector_contenido.currentData()),
            "incluir_totales": self.incluir_totales.isChecked(),
            "incluir_notas": self.incluir_notas.isChecked(),
            "agrupacion": str(self.selector_agrupacion.currentData()),
            "formato": str(self.selector_formato.currentData()),
        }

    @staticmethod
    def _ids_seleccionados(lista: QListWidget) -> list[object]:
        return [
            lista.item(indice).data(Qt.ItemDataRole.UserRole)
            for indice in range(lista.count())
            if lista.item(indice).checkState() == Qt.CheckState.Checked
        ]

    def _columnas_seleccionadas(self) -> list[str]:
        return [
            str(self.lista_columnas.item(indice).data(Qt.ItemDataRole.UserRole))
            for indice in range(self.lista_columnas.count())
            if self.lista_columnas.item(indice).checkState()
            == Qt.CheckState.Checked
        ]

    def _actualizar_vista_previa(self) -> None:
        if self._proveedor_vista_previa is None:
            self._datos_previa = None
            QMessageBox.information(
                self, "Vista previa", "No hay un proveedor de vista previa configurado."
            )
            return
        try:
            seleccion = self._selection()
            if self._previsualizando:
                return
            self._previsualizando = True
            self._datos_previa = None
            self._seleccion_previa = None
            self.cantidad_filas.setText("Preparando vista previa…")
            self.boton_previsualizar.setEnabled(False)
            self._tarea_previa = run_background_task(
                self._proveedor_vista_previa, seleccion
            )
            self._tarea_previa.signals.finished.connect(
                lambda datos: self._mostrar_vista_previa(datos, seleccion)
            )
            self._tarea_previa.signals.error.connect(self._error_vista_previa)
        except Exception as error:
            self._finalizar_previsualizacion()
            logger.exception("No se pudo preparar la vista previa del informe")
            QMessageBox.critical(self, "Error de vista previa", str(error))

    def _mostrar_vista_previa(self, datos: ReporteDatos, seleccion: dict) -> None:
        try:
            if seleccion["contenido"] == "detalle":
                catalogo = datos.columnas_detalle or datos.columnas
                filas = datos.filas_detalle or datos.filas
            else:
                catalogo = datos.columnas
                filas = datos.filas
            disponibles = {columna.id: columna for columna in catalogo}
            columnas = [
                disponibles[columna_id]
                for columna_id in seleccion["columnas"]
                if columna_id in disponibles
            ]
            self.tabla_previa.setColumnCount(len(columnas))
            self.tabla_previa.setHorizontalHeaderLabels(
                [columna.etiqueta for columna in columnas]
            )
            filas_visibles = filas[:100]
            self.tabla_previa.setRowCount(len(filas_visibles))
            for fila_idx, fila in enumerate(filas_visibles):
                for columna_idx, columna in enumerate(columnas):
                    self.tabla_previa.setItem(
                        fila_idx,
                        columna_idx,
                        QTableWidgetItem(str(fila.get(columna.id, ""))),
                    )
            if seleccion["contenido"] == "resumen":
                total_filas = len(datos.filas)
            elif seleccion["contenido"] == "detalle":
                total_filas = len(datos.filas_detalle or datos.filas)
            else:
                total_filas = len(datos.filas) + len(datos.filas_detalle)
            self.cantidad_filas.setText(f"{total_filas} filas")
            self._datos_previa = datos
            self._seleccion_previa = seleccion
        except Exception as error:
            logger.exception("No se pudo mostrar la vista previa del informe")
            self._error_vista_previa(str(error))
            return
        self._finalizar_previsualizacion()

    def _error_vista_previa(self, mensaje: str) -> None:
        logger.error("Falló la vista previa de exportación: %s", mensaje)
        self._finalizar_previsualizacion()
        self._datos_previa = None
        self._seleccion_previa = None
        QMessageBox.critical(self, "Error de vista previa", mensaje)

    def _finalizar_previsualizacion(self) -> None:
        self._previsualizando = False
        self.boton_previsualizar.setEnabled(True)

    def _leer_plantillas(self) -> dict[str, dict]:
        from PyQt6.QtCore import QSettings

        settings = QSettings("VESP Organizations", "Reportes")
        valor = settings.value(_PLANTILLAS_KEY, "{}")
        try:
            plantillas = json.loads(str(valor))
        except json.JSONDecodeError as error:
            raise ValueError("El almacenamiento de plantillas está dañado") from error
        if not isinstance(plantillas, dict):
            raise ValueError("El almacenamiento de plantillas no tiene el formato esperado")
        return plantillas

    def _guardar_plantilla(self) -> None:
        nombre = self.nombre_plantilla.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Plantilla", "Escribí un nombre para la plantilla.")
            return
        try:
            from PyQt6.QtCore import QSettings

            plantillas = self._leer_plantillas()
            seleccion = self._selection()
            seleccion.pop("filtros_pantalla", None)
            normalizadas = {
                clave: self._serializar(valor)
                for clave, valor in seleccion.items()
            }
            plantillas[nombre] = normalizadas
            settings = QSettings("VESP Organizations", "Reportes")
            settings.setValue(
                _PLANTILLAS_KEY,
                json.dumps(plantillas, ensure_ascii=False),
            )
            self._refrescar_plantillas(nombre)
        except (OSError, ValueError, TypeError) as error:
            logger.exception("No se pudo guardar la plantilla de informe")
            QMessageBox.critical(self, "Error", str(error))

    @staticmethod
    def _serializar(valor):
        if isinstance(valor, date):
            return valor.isoformat()
        if isinstance(valor, (list, dict, str, int, float, bool)) or valor is None:
            return valor
        raise TypeError(f"Valor de plantilla no serializable: {type(valor).__name__}")

    def _cargar_plantilla(self) -> None:
        nombre = self.selector_plantilla.currentText()
        if not nombre:
            return
        try:
            datos = self._leer_plantillas()[nombre]
            periodo_idx = self.selector_periodo.findData(datos["tipo_periodo"])
            fecha_desde = QDate.fromString(datos["fecha_inicio"], "yyyy-MM-dd")
            fecha_hasta = QDate.fromString(datos["fecha_fin"], "yyyy-MM-dd")
            if periodo_idx < 0 or not fecha_desde.isValid() or not fecha_hasta.isValid():
                raise ValueError("La plantilla contiene un período inválido")
            self.selector_periodo.setCurrentIndex(periodo_idx)
            self.fecha_desde.setDate(fecha_desde)
            self.fecha_hasta.setDate(fecha_hasta)
            self.todos_objetivos.setChecked(datos["objetivo_ids"] is None)
            if datos["objetivo_ids"] is not None:
                self._seleccionar_ids(self.lista_objetivos, set(datos["objetivo_ids"]))
            supervisores = datos.get("supervisor_ids")
            self.todos_supervisores.setChecked(supervisores is None)
            if supervisores is not None:
                self._seleccionar_ids(self.lista_supervisores, set(supervisores))
            self.lista_equipos.setCurrentIndex(
                self.lista_equipos.findData(datos["equipo_id"])
            )
            self.turno_dia.setChecked("diurno" in datos["turnos"])
            self.turno_noche.setChecked("nocturno" in datos["turnos"])
            self._restaurar_columnas(datos["columnas"])
            self.selector_contenido.setCurrentIndex(
                self.selector_contenido.findData(datos["contenido"])
            )
            self.incluir_totales.setChecked(datos["incluir_totales"])
            self.incluir_notas.setChecked(datos["incluir_notas"])
            self.selector_agrupacion.setCurrentIndex(
                self.selector_agrupacion.findData(datos["agrupacion"])
            )
            self.selector_formato.setCurrentIndex(
                self.selector_formato.findData(datos["formato"])
            )
        except (KeyError, TypeError, ValueError) as error:
            logger.exception("No se pudo cargar la plantilla de informe %s", nombre)
            QMessageBox.critical(self, "Error", str(error))

    def _restaurar_columnas(self, columnas: list[str]) -> None:
        items = {}
        while self.lista_columnas.count():
            item = self.lista_columnas.takeItem(0)
            items[str(item.data(Qt.ItemDataRole.UserRole))] = item
        for columna_id in columnas:
            if columna_id in items:
                self.lista_columnas.addItem(items.pop(columna_id))
        for item in items.values():
            self.lista_columnas.addItem(item)
            item.setCheckState(Qt.CheckState.Unchecked)

    def _refrescar_plantillas(self, seleccionada: str | None = None) -> None:
        plantillas = self._leer_plantillas()
        self.selector_plantilla.clear()
        self.selector_plantilla.addItems(sorted(plantillas))
        if seleccionada:
            self.selector_plantilla.setCurrentText(seleccionada)

    def _aplicar_tema(self, nombre_tema: str) -> None:
        tokens = self._theme_manager.tokens(nombre_tema)
        self.setStyleSheet(
            f"""
            QDialog, QGroupBox {{ background: {tokens['surface']}; color: {tokens['text_primary']}; }}
            QLabel {{ color: {tokens['text_primary']}; }}
            QLineEdit, QComboBox, QDateEdit, QListWidget, QTableWidget {{
                background: {tokens['surface_alt']}; color: {tokens['text_primary']};
                border: 1px solid {tokens['border']}; border-radius: {tokens['radius_sm']};
            }}
            QPushButton {{ background: {tokens['accent']}; color: {tokens['accent_text']}; }}
            """
        )

    def closeEvent(self, evento) -> None:
        self._theme_manager.theme_changed.disconnect(self._aplicar_tema)
        super().closeEvent(evento)

    def seleccion(self) -> dict:
        """Devuelve una copia validada de la configuración elegida."""
        return self._selection()

    def datos_previsualizados(self) -> ReporteDatos | None:
        """Retorna la misma instantánea que se mostró en la vista previa."""
        return self._datos_previa

    def accept(self) -> None:
        if self._previsualizando:
            QMessageBox.information(
                self, "Vista previa", "Esperá a que termine la vista previa."
            )
            return
        try:
            seleccion = self._selection()
        except ValueError as error:
            QMessageBox.warning(self, "Período inválido", str(error))
            return
        if not seleccion["columnas"]:
            QMessageBox.warning(
                self, "Columnas", "Seleccioná al menos una columna para exportar."
            )
            return
        if self._seleccion_previa != seleccion:
            self._actualizar_vista_previa()
            if self._datos_previa is not None:
                QMessageBox.information(
                    self,
                    "Vista previa actualizada",
                    "Revisá los datos y volvé a presionar «Continuar».",
                )
            return
        contenido = seleccion["contenido"]
        if self._datos_previa is None:
            cantidad = 0
        elif contenido == "resumen":
            cantidad = len(self._datos_previa.filas)
        elif contenido == "detalle":
            cantidad = len(self._datos_previa.filas_detalle or self._datos_previa.filas)
        else:
            cantidad = len(self._datos_previa.filas) + len(
                self._datos_previa.filas_detalle
            )
        if cantidad == 0:
            QMessageBox.warning(
                self,
                "Sin datos",
                "No hay datos para el período y los filtros seleccionados.",
            )
            return
        if contenido == "ambos":
            seleccionadas = set(seleccion["columnas"])
            if self._datos_previa.filas and not seleccionadas.intersection(
                columna.id for columna in self._datos_previa.columnas
            ):
                QMessageBox.warning(
                    self,
                    "Columnas",
                    "Elegí al menos una columna disponible en el resumen.",
                )
                return
            if self._datos_previa.filas_detalle and not seleccionadas.intersection(
                columna.id for columna in self._datos_previa.columnas_detalle
            ):
                QMessageBox.warning(
                    self,
                    "Columnas",
                    "Elegí al menos una columna disponible en el detalle.",
                )
                return
        super().accept()
