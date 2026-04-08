# =============================================================================
# VESP Organizations - Vista de Caché y Rendimiento
# =============================================================================

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QProgressBar, QScrollArea
)
from PyQt6.QtGui import QColor
from services.cache import (
    obtener_cache, cargar_objetivos_en_cache, cargar_supervisores_en_cache,
    cargar_usuarios_en_cache, invalidar_todo
)
from services.auditoria import registrar_auditoria, TipoOperacion
from datetime import datetime


class VistaCache(QWidget):
    """Vista para monitorear y gestionar el caché inteligente."""

    def __init__(self, usuario_actual=None):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.cache = obtener_cache()
        self.init_ui()
        
        # Actualizar stats cada 2 segundos
        self.timer_actualizacion = QTimer()
        self.timer_actualizacion.timeout.connect(self.actualizar_stats)
        self.timer_actualizacion.start(2000)

    def init_ui(self):
        """Inicializa la interfaz."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Monitor de Caché Inteligente")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(titulo)

        # Botones de control
        botones_layout = QHBoxLayout()
        
        btn_cargar = QPushButton("📥 Cargar Todo en Caché")
        btn_cargar.clicked.connect(self.cargar_todo_cache)
        botones_layout.addWidget(btn_cargar)
        
        btn_limpiar = QPushButton("🗑️ Limpiar Caché")
        btn_limpiar.clicked.connect(self.limpiar_cache)
        botones_layout.addWidget(btn_limpiar)
        
        btn_limpiar_expiradas = QPushButton("🧹 Limpiar Expiradas")
        btn_limpiar_expiradas.clicked.connect(self.limpiar_expiradas)
        botones_layout.addWidget(btn_limpiar_expiradas)
        
        layout.addLayout(botones_layout)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Estadísticas
        self.tab_stats = self._crear_tab_stats()
        self.tabs.addTab(self.tab_stats, "Estadísticas")

        # Tab 2: Contenido de Caché
        self.tab_contenido = self._crear_tab_contenido()
        self.tabs.addTab(self.tab_contenido, "Contenido")

        # Tab 3: Rendimiento
        self.tab_rendimiento = self._crear_tab_rendimiento()
        self.tabs.addTab(self.tab_rendimiento, "Rendimiento")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _crear_tab_stats(self):
        """Crea el tab de estadísticas."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Grupo de stats
        group_stats = QGroupBox("Estadísticas Generales")
        stats_layout = QVBoxLayout()

        self.label_stats = QLabel()
        self.label_stats.setStyleSheet("font-family: monospace; font-size: 11px;")
        stats_layout.addWidget(self.label_stats)

        group_stats.setLayout(stats_layout)
        layout.addWidget(group_stats)

        # Progreso
        group_aciertos = QGroupBox("Tasa de Acierto")
        aciertos_layout = QVBoxLayout()

        self.progress_aciertos = QProgressBar()
        self.progress_aciertos.setStyleSheet("""
            QProgressBar {
                border: 1px solid gray;
                border-radius: 3px;
                background: white;
            }
            QProgressBar::chunk {
                background: #90EE90;
            }
        """)
        aciertos_layout.addWidget(self.progress_aciertos)

        self.label_aciertos = QLabel("N/A")
        aciertos_layout.addWidget(self.label_aciertos)

        group_aciertos.setLayout(aciertos_layout)
        layout.addWidget(group_aciertos)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _crear_tab_contenido(self):
        """Crea el tab de contenido del caché."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Tabla de contenido
        self.tabla_contenido = QTableWidget()
        self.tabla_contenido.setColumnCount(5)
        self.tabla_contenido.setHorizontalHeaderLabels(
            ["Clave", "TTL (s)", "Antigüedad (s)", "Hits", "Estado"]
        )
        self.tabla_contenido.setColumnWidth(0, 250)
        self.tabla_contenido.setColumnWidth(1, 80)
        self.tabla_contenido.setColumnWidth(2, 120)
        self.tabla_contenido.setColumnWidth(3, 60)
        self.tabla_contenido.setColumnWidth(4, 100)

        layout.addWidget(self.tabla_contenido)
        widget.setLayout(layout)
        return widget

    def _crear_tab_rendimiento(self):
        """Crea el tab de análisis de rendimiento."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Análisis
        self.texto_rendimiento = QLabel()
        self.texto_rendimiento.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.texto_rendimiento.setWordWrap(True)
        self.texto_rendimiento.setStyleSheet("font-family: monospace; font-size: 10px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.texto_rendimiento)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def actualizar_stats(self):
        """Actualiza las estadísticas en tiempo real."""
        stats = self.cache.obtener_stats()

        # Tab 1: Stats
        texto_stats = f"""
Entradas en caché: {stats['enumerador']}
Hits: {stats['hits']}
Misses: {stats['misses']}
Total accesos: {stats['total_accesos']}
Tasa de acierto: {stats['tasa_acierto_porcentaje']}%
Invalidaciones: {stats['invalidaciones']}
TTL por defecto: {stats['ttl_por_defecto_segundos']}s
        """
        self.label_stats.setText(texto_stats.strip())

        # Progreso bar
        tasa = int(stats['tasa_acierto_porcentaje'])
        self.progress_aciertos.setValue(tasa)
        self.label_aciertos.setText(f"{stats['tasa_acierto_porcentaje']}% de acierto")

        # Tab 2: Contenido
        detalles = self.cache.obtener_detalles()
        self.tabla_contenido.setRowCount(len(detalles))

        for i, (clave, info) in enumerate(detalles.items()):
            item_clave = QTableWidgetItem(clave)
            item_ttl = QTableWidgetItem(str(info['ttl_segundos']))
            item_antiguedad = QTableWidgetItem(f"{info['antiguedad_segundos']:.1f}")
            item_hits = QTableWidgetItem(str(info['hits']))

            estado = "⏳ Expirada" if info['expirada'] else "✅ Válida"
            item_estado = QTableWidgetItem(estado)

            if info['expirada']:
                item_estado.setBackground(QColor(255, 200, 200))
            else:
                item_estado.setBackground(QColor(200, 255, 200))

            self.tabla_contenido.setItem(i, 0, item_clave)
            self.tabla_contenido.setItem(i, 1, item_ttl)
            self.tabla_contenido.setItem(i, 2, item_antiguedad)
            self.tabla_contenido.setItem(i, 3, item_hits)
            self.tabla_contenido.setItem(i, 4, item_estado)

        # Tab 3: Rendimiento
        ahorro_queries = stats['hits']  # Aproximado: cada hit es una query evitada
        tiempo_estimado_ahorrado = ahorro_queries * 0.05  # 50ms por query promedio

        texto_rendimiento = f"""
=== ANÁLISIS DE RENDIMIENTO ===

📊 ESTADÍSTICAS:
  • Entradas activas: {stats['enumerador']}
  • Tasa de acierto: {stats['tasa_acierto_porcentaje']}%
  • Total accesos: {stats['total_accesos']}

⚡ IMPACTO:
  • Queries evitadas: {ahorro_queries}
  • Tiempo estimado ahorrado: {tiempo_estimado_ahorrado:.2f}s

💾 RECOMENDACIONES:
"""
        if stats['tasa_acierto_porcentaje'] > 80:
            texto_rendimiento += "  ✅ Caché funcionando óptimamente\n"
        elif stats['tasa_acierto_porcentaje'] > 50:
            texto_rendimiento += "  ⚠️ Aumentar TTL para mejorar acierto\n"
        else:
            texto_rendimiento += "  ❌ Baja tasa de acierto, revisar estrategia\n"

        if stats['enumerador'] > 50:
            texto_rendimiento += "  ⚠️ Muchas entradas, considerar limpiar periódicamente\n"
        else:
            texto_rendimiento += "  ✅ Tamaño de caché dentro de límites\n"

        self.texto_rendimiento.setText(texto_rendimiento)

    def cargar_todo_cache(self):
        """Carga toda la información en caché."""
        try:
            cargar_objetivos_en_cache()
            cargar_supervisores_en_cache()
            cargar_usuarios_en_cache()

            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.CREATE,
                    tabla="cache",
                    detalles="Caché precargado manualmente",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )

            QMessageBox.information(self, "Éxito", "Caché precargado correctamente")
            self.actualizar_stats()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar caché: {e}")

    def limpiar_cache(self):
        """Limpia todo el caché."""
        respuesta = QMessageBox.question(
            self,
            "Limpiar Caché",
            "¿Está seguro que desea limpiar todo el caché?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            invalidar_todo()

            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.DELETE,
                    tabla="cache",
                    detalles="Caché limpiado manualmente",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )

            self.actualizar_stats()
            QMessageBox.information(self, "Éxito", "Caché limpiado")

    def limpiar_expiradas(self):
        """Limpia solo las entradas expiradas."""
        cantidad = self.cache.limpiar_expiradas()

        if self.usuario_actual:
            registrar_auditoria(
                usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                tipo_operacion=TipoOperacion.DELETE,
                tabla="cache",
                detalles=f"Eliminadas {cantidad} entradas expiradas",
                usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
            )

        self.actualizar_stats()
        QMessageBox.information(self, "Éxito", f"Se eliminaron {cantidad} entradas expiradas")

    def closeEvent(self, event):
        """Detiene el timer al cerrar la ventana."""
        self.timer_actualizacion.stop()
        event.accept()
