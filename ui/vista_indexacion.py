# =============================================================================
# VESP Organizations - Vista de Indexación y Optimización
# =============================================================================

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QTextEdit, QProgressBar, QComboBox
)
from PyQt6.QtGui import QColor, QFont
from services.db_analyzer import AnalisisBD
from services.auditoria import registrar_auditoria, TipoOperacion
from datetime import datetime


class VistaIndexacion(QWidget):
    """Vista para monitorear y optimizar indexación de la BD."""

    def __init__(self, usuario_actual=None):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.analizador = AnalisisBD()
        self.init_ui()
        self.actualizar_datos()

    def init_ui(self):
        """Inicializa la interfaz."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Optimización de Índices y Rendimiento de BD")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(titulo)

        # Botones de control
        botones_layout = QHBoxLayout()
        
        btn_actualizar = QPushButton("🔄 Actualizar Análisis")
        btn_actualizar.clicked.connect(self.actualizar_datos)
        botones_layout.addWidget(btn_actualizar)
        
        btn_optimizar = QPushButton("⚡ Optimizar BD Ahora")
        btn_optimizar.clicked.connect(self.optimizar_bd)
        botones_layout.addWidget(btn_optimizar)
        
        btn_exportar = QPushButton("📄 Exportar Reporte")
        btn_exportar.clicked.connect(self.exportar_reporte)
        botones_layout.addWidget(btn_exportar)
        
        layout.addLayout(botones_layout)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Estadísticas
        self.tab_stats = self._crear_tab_stats()
        self.tabs.addTab(self.tab_stats, "Estadísticas")

        # Tab 2: Índices Actuales
        self.tab_indices = self._crear_tab_indices()
        self.tabs.addTab(self.tab_indices, "Índices Actuales")

        # Tab 3: Recomendaciones
        self.tab_recomendaciones = self._crear_tab_recomendaciones()
        self.tabs.addTab(self.tab_recomendaciones, "Recomendaciones")

        # Tab 4: Reporte Completo
        self.tab_reporte = self._crear_tab_reporte()
        self.tabs.addTab(self.tab_reporte, "Reporte Completo")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _crear_tab_stats(self):
        """Crea el tab de estadísticas generales."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Grupo de estadísticas
        group_stats = QGroupBox("Estadísticas de Base de Datos")
        stats_layout = QVBoxLayout()

        self.tabla_stats = QTableWidget()
        self.tabla_stats.setColumnCount(5)
        self.tabla_stats.setHorizontalHeaderLabels(
            ["Tabla", "Filas", "Tamaño (MB)", "Índices", "Estado"]
        )
        self.tabla_stats.setColumnWidth(0, 150)
        self.tabla_stats.setColumnWidth(1, 100)
        self.tabla_stats.setColumnWidth(2, 120)
        self.tabla_stats.setColumnWidth(3, 80)
        self.tabla_stats.setColumnWidth(4, 100)

        stats_layout.addWidget(self.tabla_stats)
        group_stats.setLayout(stats_layout)
        layout.addWidget(group_stats)

        # Resumen
        group_resumen = QGroupBox("Resumen")
        resumen_layout = QVBoxLayout()

        self.label_resumen = QLabel()
        self.label_resumen.setStyleSheet("font-size: 11px;")
        resumen_layout.addWidget(self.label_resumen)

        group_resumen.setLayout(resumen_layout)
        layout.addWidget(group_resumen)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _crear_tab_indices(self):
        """Crea el tab de índices actuales."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Selector de tabla
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Tabla:"))
        self.combo_tabla = QComboBox()
        self.combo_tabla.currentTextChanged.connect(self.actualizar_indices_tabla)
        selector_layout.addWidget(self.combo_tabla)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Tabla de índices
        self.tabla_indices = QTableWidget()
        self.tabla_indices.setColumnCount(4)
        self.tabla_indices.setHorizontalHeaderLabels(
            ["Nombre", "Columnas", "Único", "Tamaño Est. (KB)"]
        )
        self.tabla_indices.setColumnWidth(0, 250)
        self.tabla_indices.setColumnWidth(1, 250)
        self.tabla_indices.setColumnWidth(2, 80)
        self.tabla_indices.setColumnWidth(3, 120)

        layout.addWidget(self.tabla_indices)

        # Botones
        botones_layout = QHBoxLayout()
        
        btn_borrar = QPushButton("🗑️ Eliminar Índice Seleccionado")
        btn_borrar.clicked.connect(self.eliminar_indice_seleccionado)
        botones_layout.addWidget(btn_borrar)
        
        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        widget.setLayout(layout)
        return widget

    def _crear_tab_recomendaciones(self):
        """Crea el tab de índices recomendados."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Tabla de recomendaciones
        self.tabla_recomendaciones = QTableWidget()
        self.tabla_recomendaciones.setColumnCount(5)
        self.tabla_recomendaciones.setHorizontalHeaderLabels(
            ["Tabla", "Columnas", "Razón", "Impacto %", "Acción"]
        )
        self.tabla_recomendaciones.setColumnWidth(0, 100)
        self.tabla_recomendaciones.setColumnWidth(1, 200)
        self.tabla_recomendaciones.setColumnWidth(2, 250)
        self.tabla_recomendaciones.setColumnWidth(3, 80)
        self.tabla_recomendaciones.setColumnWidth(4, 150)

        layout.addWidget(self.tabla_recomendaciones)

        # Botones
        botones_layout = QHBoxLayout()
        
        btn_crear_uno = QPushButton("✅ Crear Seleccionado")
        btn_crear_uno.clicked.connect(self.crear_indice_seleccionado)
        botones_layout.addWidget(btn_crear_uno)
        
        btn_crear_top5 = QPushButton("✨ Crear Top 5")
        btn_crear_top5.clicked.connect(self.crear_top5_indices)
        botones_layout.addWidget(btn_crear_top5)
        
        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        widget.setLayout(layout)
        return widget

    def _crear_tab_reporte(self):
        """Crea el tab de reporte completo."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.texto_reporte = QTextEdit()
        self.texto_reporte.setReadOnly(True)
        self.texto_reporte.setFont(QFont("Courier", 9))

        layout.addWidget(self.texto_reporte)
        widget.setLayout(layout)
        return widget

    def actualizar_datos(self):
        """Actualiza todos los datos y vistas."""
        try:
            # Tab 1: Estadísticas
            self._actualizar_stats()
            
            # Tab 2: Índices
            tablas = self.analizador.obtener_tablas()
            self.combo_tabla.clear()
            self.combo_tabla.addItems(tablas)
            self.actualizar_indices_tabla()
            
            # Tab 3: Recomendaciones
            self._actualizar_recomendaciones()
            
            # Tab 4: Reporte
            reporte = self.analizador.generar_reporte()
            self.texto_reporte.setText(reporte)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error actualizando datos: {e}")

    def _actualizar_stats(self):
        """Actualiza la tabla de estadísticas."""
        self.tabla_stats.setRowCount(0)
        
        total_filas = 0
        total_mb = 0
        total_indices = 0
        
        for tabla in self.analizador.obtener_tablas():
            stats = self.analizador.obtener_estadisticas_tabla(tabla)
            
            if "error" in stats:
                continue
            
            row = self.tabla_stats.rowCount()
            self.tabla_stats.insertRow(row)
            
            self.tabla_stats.setItem(row, 0, QTableWidgetItem(tabla))
            self.tabla_stats.setItem(row, 1, QTableWidgetItem(f"{stats['total_filas']:,}"))
            self.tabla_stats.setItem(row, 2, QTableWidgetItem(f"{stats['tamaño_mb']:.2f}"))
            self.tabla_stats.setItem(row, 3, QTableWidgetItem(str(stats['indices'])))
            
            # Estado
            estado_item = QTableWidgetItem("✅ OK")
            estado_item.setBackground(QColor(200, 255, 200))
            self.tabla_stats.setItem(row, 4, estado_item)
            
            total_filas += stats['total_filas']
            total_mb += stats['tamaño_mb']
            total_indices += stats['indices']
        
        # Resumen
        self.label_resumen.setText(
            f"Total: {total_filas:,} filas | "
            f"Tamaño: {total_mb:.2f} MB | "
            f"Índices: {total_indices}"
        )

    def actualizar_indices_tabla(self):
        """Actualiza los índices de la tabla seleccionada."""
        tabla = self.combo_tabla.currentText()
        if not tabla:
            return
        
        self.tabla_indices.setRowCount(0)
        
        indices = self.analizador.obtener_indices(tabla)
        for idx in indices:
            row = self.tabla_indices.rowCount()
            self.tabla_indices.insertRow(row)
            
            self.tabla_indices.setItem(row, 0, QTableWidgetItem(idx["nombre"]))
            self.tabla_indices.setItem(row, 1, QTableWidgetItem(", ".join(idx["columnas"])))
            
            unico = "Sí" if idx["unico"] else "No"
            self.tabla_indices.setItem(row, 2, QTableWidgetItem(unico))
            
            tamaño_kb = idx["tamaño_estimado_bytes"] / 1024
            self.tabla_indices.setItem(row, 3, QTableWidgetItem(f"{tamaño_kb:.2f}"))

    def _actualizar_recomendaciones(self):
        """Actualiza la tabla de recomendaciones."""
        self.tabla_recomendaciones.setRowCount(0)
        
        sugerencias = self.analizador.sugerir_indices()
        
        for i, sug in enumerate(sugerencias):
            row = self.tabla_recomendaciones.rowCount()
            self.tabla_recomendaciones.insertRow(row)
            
            self.tabla_recomendaciones.setItem(row, 0, QTableWidgetItem(sug["tabla"]))
            self.tabla_recomendaciones.setItem(row, 1, QTableWidgetItem(", ".join(sug["columnas"])))
            self.tabla_recomendaciones.setItem(row, 2, QTableWidgetItem(sug["razon"]))
            
            impacto_item = QTableWidgetItem(f"{sug['impacto_porcentaje']:.1f}%")
            impacto_item.setBackground(self._color_impacto(sug['impacto_porcentaje']))
            self.tabla_recomendaciones.setItem(row, 3, impacto_item)
            
            btn_crear = QPushButton("Crear")
            btn_crear.clicked.connect(
                lambda checked, t=sug["tabla"], c=sug["columnas"]: self.crear_indice(t, c)
            )
            self.tabla_recomendaciones.setCellWidget(row, 4, btn_crear)

    def _color_impacto(self, impacto: float) -> QColor:
        """Retorna color según impacto."""
        if impacto >= 8.5:
            return QColor(100, 200, 100)  # Verde
        elif impacto >= 7.0:
            return QColor(255, 255, 150)  # Amarillo
        else:
            return QColor(255, 200, 200)  # Rosa

    def crear_indice(self, tabla: str, columnas: list):
        """Crea un índice."""
        nombre_indice = f"idx_{tabla}_{'_'.join(columnas)}"
        
        if self.analizador.crear_indice(tabla, columnas, nombre_indice):
            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.CREATE,
                    tabla="indices",
                    detalles=f"Creado índice {nombre_indice} en tabla {tabla}",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )
            
            QMessageBox.information(self, "Éxito", f"Índice creado: {nombre_indice}")
            self.actualizar_datos()
        else:
            QMessageBox.critical(self, "Error", f"Error al crear índice")

    def crear_indice_seleccionado(self):
        """Crea el índice de la fila seleccionada."""
        fila = self.tabla_recomendaciones.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione una recomendación")
            return
        
        tabla = self.tabla_recomendaciones.item(fila, 0).text()
        columnas_str = self.tabla_recomendaciones.item(fila, 1).text()
        columnas = [c.strip() for c in columnas_str.split(",")]
        
        self.crear_indice(tabla, columnas)

    def crear_top5_indices(self):
        """Crea los top 5 índices recomendados."""
        sugerencias = self.analizador.sugerir_indices()[:5]
        
        creados = 0
        for sug in sugerencias:
            if self.analizador.crear_indice(sug["tabla"], sug["columnas"], sug["nombre_indice"]):
                creados += 1
        
        if self.usuario_actual:
            registrar_auditoria(
                usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                tipo_operacion=TipoOperacion.CREATE,
                tabla="indices",
                detalles=f"Creados {creados} índices automáticamente",
                usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
            )
        
        QMessageBox.information(self, "Éxito", f"Se crearon {creados} índices")
        self.actualizar_datos()

    def eliminar_indice_seleccionado(self):
        """Elimina el índice seleccionado."""
        fila = self.tabla_indices.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un índice")
            return
        
        nombre_indice = self.tabla_indices.item(fila, 0).text()
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el índice '{nombre_indice}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            if self.analizador.eliminar_indice(nombre_indice):
                if self.usuario_actual:
                    registrar_auditoria(
                        usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                        tipo_operacion=TipoOperacion.DELETE,
                        tabla="indices",
                        detalles=f"Eliminado índice {nombre_indice}",
                        usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                    )
                
                QMessageBox.information(self, "Éxito", f"Índice eliminado")
                self.actualizar_datos()
            else:
                QMessageBox.critical(self, "Error", "Error al eliminar índice")

    def optimizar_bd(self):
        """Ejecuta optimización de BD."""
        respuesta = QMessageBox.question(
            self,
            "Optimizar BD",
            "Se ejecutarán: ANALYZE (estadísticas), VACUUM (compactar), REINDEX (reconstruir índices)\n\n"
            "Esto puede tardar unos segundos. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        
        try:
            resultado = self.analizador.optimizar_bd()
            
            if resultado["exitoso"]:
                if self.usuario_actual:
                    registrar_auditoria(
                        usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                        tipo_operacion=TipoOperacion.UPDATE,
                        tabla="bd",
                        detalles="Optimización ejecutada: ANALYZE, VACUUM, REINDEX",
                        usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                    )
                
                QMessageBox.information(self, "Éxito", "BD optimizada correctamente")
                self.actualizar_datos()
            else:
                QMessageBox.critical(self, "Error", f"Error: {resultado.get('error')}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al optimizar: {e}")

    def exportar_reporte(self):
        """Exporta el reporte a archivo."""
        try:
            ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta = f"reportes/indexacion_{ahora}.txt"
            
            reporte = self.analizador.generar_reporte()
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(reporte)
            
            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.READ,
                    tabla="reportes",
                    detalles=f"Reporte de indexación exportado a {ruta}",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )
            
            QMessageBox.information(self, "Éxito", f"Reporte exportado a:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")
