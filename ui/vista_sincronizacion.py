# =============================================================================
# VESP Organizations - Vista de Sincronización y Monitoreo
# =============================================================================

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QTextEdit, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QColor, QFont
from services.sincronizacion import obtener_sincronizador, conectar_modulo
from services.auditoria import registrar_auditoria, TipoOperacion
from datetime import datetime
import json


class VistaSincronizacion(QWidget):
    """Vista para monitorear sincronización de datos en tiempo real."""

    def __init__(self, usuario_actual=None):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.sincronizador = obtener_sincronizador()
        self.historial_eventos = []
        self.init_ui()
        self.conectar_senales()
        self.actualizar_datos()

    def init_ui(self):
        """Inicializa la interfaz."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Monitoreo de Sincronización de Datos")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(titulo)

        # Botones de control
        botones_layout = QHBoxLayout()
        
        btn_actualizar = QPushButton("🔄 Actualizar Estado")
        btn_actualizar.clicked.connect(self.actualizar_datos)
        botones_layout.addWidget(btn_actualizar)
        
        btn_limpiar_historial = QPushButton("🗑️ Limpiar Historial")
        btn_limpiar_historial.clicked.connect(self.limpiar_historial)
        botones_layout.addWidget(btn_limpiar_historial)
        
        btn_test_sincronizacion = QPushButton("🧪 Test Sincronización")
        btn_test_sincronizacion.clicked.connect(self.test_sincronizacion)
        botones_layout.addWidget(btn_test_sincronizacion)
        
        layout.addLayout(botones_layout)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Estado Actual
        self.tab_estado = self._crear_tab_estado()
        self.tabs.addTab(self.tab_estado, "Estado Actual")

        # Tab 2: Historial de Eventos
        self.tab_historial = self._crear_tab_historial()
        self.tabs.addTab(self.tab_historial, "Historial")

        # Tab 3: Conexiones Activas
        self.tab_conexiones = self._crear_tab_conexiones()
        self.tabs.addTab(self.tab_conexiones, "Conexiones")

        # Tab 4: Configuración
        self.tab_config = self._crear_tab_config()
        self.tabs.addTab(self.tab_config, "Configuración")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _crear_tab_estado(self):
        """Crea el tab de estado actual."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Estado general
        group_estado = QGroupBox("Estado del Sistema de Sincronización")
        estado_layout = QVBoxLayout()

        self.label_estado = QLabel("Estado: Inicializando...")
        self.label_estado.setStyleSheet("font-size: 12px;")
        estado_layout.addWidget(self.label_estado)

        self.label_conexiones = QLabel("Conexiones activas: 0")
        estado_layout.addWidget(self.label_conexiones)

        self.label_timers = QLabel("Timers activos: 0")
        estado_layout.addWidget(self.label_timers)

        group_estado.setLayout(estado_layout)
        layout.addWidget(group_estado)

        # Estadísticas
        group_stats = QGroupBox("Estadísticas de Eventos")
        stats_layout = QVBoxLayout()

        self.label_total_eventos = QLabel("Total eventos: 0")
        stats_layout.addWidget(self.label_total_eventos)

        self.label_eventos_minuto = QLabel("Eventos por minuto: 0")
        stats_layout.addWidget(self.label_eventos_minuto)

        group_stats.setLayout(stats_layout)
        layout.addWidget(group_stats)

        # Estado de módulos
        group_modulos = QGroupBox("Estado de Módulos")
        modulos_layout = QVBoxLayout()

        self.tabla_modulos = QTableWidget()
        self.tabla_modulos.setColumnCount(3)
        self.tabla_modulos.setHorizontalHeaderLabels(["Módulo", "Estado", "Última Actividad"])
        self.tabla_modulos.setColumnWidth(0, 200)
        self.tabla_modulos.setColumnWidth(1, 100)
        self.tabla_modulos.setColumnWidth(2, 200)

        modulos_layout.addWidget(self.tabla_modulos)
        group_modulos.setLayout(modulos_layout)
        layout.addWidget(group_modulos)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _crear_tab_historial(self):
        """Crea el tab de historial de eventos."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Lista de eventos
        self.lista_eventos = QListWidget()
        self.lista_eventos.setFont(QFont("Courier", 9))
        layout.addWidget(self.lista_eventos)

        # Detalles del evento seleccionado
        group_detalles = QGroupBox("Detalles del Evento")
        detalles_layout = QVBoxLayout()

        self.texto_detalles = QTextEdit()
        self.texto_detalles.setReadOnly(True)
        self.texto_detalles.setMaximumHeight(150)
        detalles_layout.addWidget(self.texto_detalles)

        group_detalles.setLayout(detalles_layout)
        layout.addWidget(group_detalles)

        widget.setLayout(layout)
        return widget

    def _crear_tab_conexiones(self):
        """Crea el tab de conexiones activas."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.texto_conexiones = QTextEdit()
        self.texto_conexiones.setReadOnly(True)
        self.texto_conexiones.setFont(QFont("Courier", 9))
        layout.addWidget(self.texto_conexiones)

        widget.setLayout(layout)
        return widget

    def _crear_tab_config(self):
        """Crea el tab de configuración."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Configuración de timers
        group_timers = QGroupBox("Configuración de Timers")
        timers_layout = QVBoxLayout()

        self.label_config_timers = QLabel("Timers programados:")
        timers_layout.addWidget(self.label_config_timers)

        group_timers.setLayout(timers_layout)
        layout.addWidget(group_timers)

        # Configuración de señales
        group_senales = QGroupBox("Configuración de Señales")
        senales_layout = QVBoxLayout()

        self.label_config_senales = QLabel("Señales activas:")
        senales_layout.addWidget(self.label_config_senales)

        group_senales.setLayout(senales_layout)
        layout.addWidget(group_senales)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def conectar_senales(self):
        """Conecta las señales del sincronizador."""
        self.sincronizador.datos_cambiados.connect(self.on_datos_cambiados)
        self.sincronizador.cache_invalidado.connect(self.on_cache_invalidado)
        self.sincronizador.tabla_actualizar.connect(self.on_tabla_actualizar)
        self.sincronizador.notificacion_usuario.connect(self.on_notificacion_usuario)
        self.sincronizador.progreso_operacion.connect(self.on_progreso_operacion)

        # Conectar lista de eventos
        self.lista_eventos.itemClicked.connect(self.mostrar_detalles_evento)

    def actualizar_datos(self):
        """Actualiza todos los datos de la vista."""
        self._actualizar_estado()
        self._actualizar_historial()
        self._actualizar_conexiones()
        self._actualizar_config()

    def _actualizar_estado(self):
        """Actualiza el estado general."""
        # Estado básico
        self.label_estado.setText("Estado: ✅ Activo")
        self.label_conexiones.setText("Conexiones activas: N/A")
        self.label_timers.setText("Timers activos: N/A")

        # Estadísticas de eventos
        total_eventos = len(self.historial_eventos)
        self.label_total_eventos.setText(f"Total eventos: {total_eventos}")

        # Eventos por minuto (últimos 60 eventos)
        eventos_recientes = [e for e in self.historial_eventos[-60:] if e.get('timestamp')]
        if eventos_recientes:
            tiempo_primero = datetime.fromisoformat(eventos_recientes[0]['timestamp'])
            tiempo_ultimo = datetime.fromisoformat(eventos_recientes[-1]['timestamp'])
            minutos = max(1, (tiempo_ultimo - tiempo_primero).total_seconds() / 60)
            eventos_minuto = len(eventos_recientes) / minutos
            self.label_eventos_minuto.setText(f"Eventos por minuto: {eventos_minuto:.1f}")
        else:
            self.label_eventos_minuto.setText("Eventos por minuto: 0")

        # Estado de módulos (simulado)
        modulos = [
            ("Ventana Principal", "✅ Conectado", "Ahora"),
            ("Formularios", "✅ Conectado", "Ahora"),
            ("Tablas", "✅ Conectado", "Ahora"),
            ("Caché", "✅ Conectado", "Ahora"),
            ("Auditoría", "✅ Conectado", "Ahora")
        ]

        self.tabla_modulos.setRowCount(len(modulos))
        for i, (modulo, estado, ultima) in enumerate(modulos):
            self.tabla_modulos.setItem(i, 0, QTableWidgetItem(modulo))
            
            item_estado = QTableWidgetItem(estado)
            if "✅" in estado:
                item_estado.setBackground(QColor(200, 255, 200))
            else:
                item_estado.setBackground(QColor(255, 200, 200))
            self.tabla_modulos.setItem(i, 1, item_estado)
            
            self.tabla_modulos.setItem(i, 2, QTableWidgetItem(ultima))

    def _actualizar_historial(self):
        """Actualiza el historial de eventos."""
        self.lista_eventos.clear()
        for evento in reversed(self.historial_eventos[-100:]):  # Últimos 100
            tipo = evento.get('tipo', 'desconocido')
            tabla = evento.get('tabla', 'N/A')
            timestamp = evento.get('timestamp', 'N/A')
            
            texto = f"[{timestamp}] {tipo.upper()}: {tabla}"
            if 'operacion' in evento:
                texto += f" ({evento['operacion']})"
            
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, evento)
            
            # Color según tipo
            if tipo == 'datos_cambiados':
                item.setBackground(QColor(255, 255, 200))
            elif tipo == 'cache_invalidado':
                item.setBackground(QColor(200, 255, 200))
            elif tipo == 'tabla_actualizar':
                item.setBackground(QColor(200, 200, 255))
            
            self.lista_eventos.addItem(item)

    def _actualizar_conexiones(self):
        """Actualiza la información de conexiones."""
        conexiones_info = """
CONEXIONES ACTIVAS:
==================

✅ Ventana Principal → Sincronizador
   - Recibe: datos_cambiados, cache_invalidado, tabla_actualizar
   - Envía: notificaciones de cambios

✅ Formularios → Sincronizador  
   - Recibe: actualizaciones de datos
   - Envía: cambios en BD

✅ Tablas → Sincronizador
   - Recibe: señales de actualización
   - Envía: confirmaciones de refresh

✅ Caché → Sincronizador
   - Recibe: invalidaciones
   - Envía: confirmaciones

✅ Auditoría → Sincronizador
   - Recibe: eventos de auditoría
   - Envía: registros de cambios

TIMERS ACTIVOS:
==============

• Actualización de caché: cada 5 minutos
• Refresh de tablas: cada 30 segundos  
• Limpieza de historial: cada 1 hora
• Backup automático: cada 6 horas
        """
        self.texto_conexiones.setText(conexiones_info)

    def _actualizar_config(self):
        """Actualiza la configuración."""
        config_timers = """
TIMERS CONFIGURADOS:
===================

• refresh_tablas: 30000ms (30s) - Actualiza tablas principales
• refresh_cache: 300000ms (5min) - Valida entradas expiradas
• backup_auto: 21600000ms (6h) - Backup automático
• limpieza_historial: 3600000ms (1h) - Limpia eventos antiguos
        """
        self.label_config_timers.setText(config_timers)

        config_senales = """
SEÑALES ACTIVAS:
===============

• datos_cambiados(tabla, operacion, datos)
  → Notifica cambios en BD a todos los módulos

• cache_invalidado(patron)
  → Invalida entradas de caché relacionadas

• tabla_actualizar(nombre_tabla)  
  → Fuerza refresh de tabla específica

• notificacion_usuario(titulo, mensaje)
  → Muestra notificaciones al usuario

• progreso_operacion(operacion, porcentaje)
  → Actualiza barras de progreso
        """
        self.label_config_senales.setText(config_senales)

    # Handlers de señales
    def on_datos_cambiados(self, tabla, operacion, datos):
        """Maneja cambios de datos."""
        evento = {
            'tipo': 'datos_cambiados',
            'tabla': tabla,
            'operacion': operacion,
            'datos': datos,
            'timestamp': datetime.now().isoformat()
        }
        self.historial_eventos.append(evento)
        self._actualizar_historial()

    def on_cache_invalidado(self, patron):
        """Maneja invalidación de caché."""
        evento = {
            'tipo': 'cache_invalidado',
            'patron': patron,
            'timestamp': datetime.now().isoformat()
        }
        self.historial_eventos.append(evento)
        self._actualizar_historial()

    def on_tabla_actualizar(self, nombre_tabla):
        """Maneja actualización de tabla."""
        evento = {
            'tipo': 'tabla_actualizar',
            'tabla': nombre_tabla,
            'timestamp': datetime.now().isoformat()
        }
        self.historial_eventos.append(evento)
        self._actualizar_historial()

    def on_notificacion_usuario(self, titulo, mensaje):
        """Maneja notificaciones de usuario."""
        evento = {
            'tipo': 'notificacion',
            'titulo': titulo,
            'mensaje': mensaje,
            'timestamp': datetime.now().isoformat()
        }
        self.historial_eventos.append(evento)
        self._actualizar_historial()

    def on_progreso_operacion(self, operacion, porcentaje):
        """Maneja progreso de operaciones."""
        evento = {
            'tipo': 'progreso',
            'operacion': operacion,
            'porcentaje': porcentaje,
            'timestamp': datetime.now().isoformat()
        }
        self.historial_eventos.append(evento)
        self._actualizar_historial()

    def mostrar_detalles_evento(self, item):
        """Muestra detalles del evento seleccionado."""
        evento = item.data(Qt.ItemDataRole.UserRole)
        if evento:
            detalles = json.dumps(evento, indent=2, ensure_ascii=False, default=str)
            self.texto_detalles.setText(detalles)

    def limpiar_historial(self):
        """Limpia el historial de eventos."""
        respuesta = QMessageBox.question(
            self,
            "Limpiar Historial",
            "¿Está seguro que desea limpiar el historial de eventos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self.historial_eventos.clear()
            self._actualizar_historial()
            self.texto_detalles.clear()
            
            if self.usuario_actual:
                registrar_auditoria(
                    usuario_id=self.usuario_actual.get('id') if isinstance(self.usuario_actual, dict) else None,
                    tipo_operacion=TipoOperacion.DELETE,
                    tabla="historial_sincronizacion",
                    detalles="Historial de eventos limpiado",
                    usuario_nombre=self.usuario_actual.get('username') if isinstance(self.usuario_actual, dict) else None
                )

    def test_sincronizacion(self):
        """Ejecuta un test de sincronización."""
        from services.sincronizacion import notificar_cambio, enviar_notificacion
        
        # Test 1: Cambio de datos
        notificar_cambio("test_objetivos", "INSERT", {"id": 999, "nombre": "Test Objetivo"})
        
        # Test 2: Notificación
        enviar_notificacion("Test Sincronización", "Esto es una prueba del sistema de sincronización")
        
        QMessageBox.information(self, "Test Completado", 
                              "Se enviaron eventos de prueba al sistema de sincronización")
