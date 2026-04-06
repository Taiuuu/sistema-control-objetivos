# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Dashboard Ejecutivo con métricas y gráficos
# =============================================================================

import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QGridLayout, QGroupBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
from services.reportes import obtener_objetivos_del_dia
from database.db import DB_PATH
from ui.animaciones import animar_entrada


class TarjetaMetrica(QWidget):
    """Widget para mostrar una métrica individual con título y valor."""

    def __init__(self, titulo: str, valor: str, color: str = "#2a82da"):
        super().__init__()
        self.setFixedSize(180, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-size: 11px; color: #666; font-weight: bold;")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        valor_label = QLabel(valor)
        valor_label.setStyleSheet(f"""
            font-size: 24px; font-weight: bold; color: {color};
            font-family: 'Segoe UI';
        """)
        valor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(titulo_label)
        layout.addWidget(valor_label)

        self.setStyleSheet(f"""
            TarjetaMetrica {{
                background-color: white;
                border: 2px solid {color}20;
                border-radius: 8px;
            }}
            TarjetaMetrica:hover {{
                border-color: {color}40;
                background-color: {color}05;
            }}
        """)


class BarraProgresoTurno(QWidget):
    """Barra de progreso para mostrar cumplimiento por turno."""

    def __init__(self, turno: str, cumplidos: int, total: int):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        titulo = QLabel(f"{turno.capitalize()}")
        titulo.setStyleSheet("font-weight: bold; font-size: 12px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        porcentaje = int((cumplidos / total * 100) if total > 0 else 0)

        barra = QProgressBar()
        barra.setRange(0, 100)
        barra.setValue(porcentaje)
        barra.setFixedHeight(20)
        barra.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {'#90EE90' if porcentaje >= 80 else '#FFD700' if porcentaje >= 50 else '#FF6B6B'};
                border-radius: 3px;
            }}
        """)

        detalle = QLabel(f"{cumplidos}/{total} objetivos ({porcentaje}%)")
        detalle.setStyleSheet("font-size: 10px; color: #666;")
        detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(titulo)
        layout.addWidget(barra)
        layout.addWidget(detalle)


class SoloDashboard(QWidget):
    """SoloDashboard principal con métricas de seguridad."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoloDashboard - VESP Control")
        self.setGeometry(200, 200, 1000, 700)
        self.setMinimumSize(800, 600)

        # Timer para actualización automática cada 30 segundos
        self.timer_actualizacion = QTimer()
        self.timer_actualizacion.timeout.connect(self.actualizar_datos)
        self.timer_actualizacion.start(30000)  # 30 segundos

        self.setup_ui()
        self.actualizar_datos()
        animar_entrada(self)

    def setup_ui(self):
        """Configura la interfaz del dashboard."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("Dashboard Ejecutivo de Seguridad")
        titulo.setStyleSheet("""
            font-size: 24px; font-weight: bold; color: #2a82da;
            margin-bottom: 10px;
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Fecha actual
        from PyQt6.QtCore import QDate
        fecha_label = QLabel(f"Fecha: {QDate.currentDate().toString('dddd, dd/MM/yyyy')}")
        fecha_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 15px;")
        fecha_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(fecha_label)

        # Métricas principales
        self.setup_metricas_principales(layout_principal)

        # Gráficos y detalles
        layout_inferior = QHBoxLayout()
        layout_inferior.setSpacing(15)

        # Panel izquierdo: Cumplimiento por turno
        self.setup_panel_turnos(layout_inferior)

        # Panel derecho: Estado detallado
        self.setup_panel_detalles(layout_inferior)

        layout_principal.addLayout(layout_inferior)

    def setup_metricas_principales(self, parent_layout):
        """Configura las tarjetas de métricas principales."""
        layout_metricas = QHBoxLayout()
        layout_metricas.setSpacing(15)

        # Crear tarjetas de métricas (se actualizarán con datos reales)
        self.tarjeta_total = TarjetaMetrica("Total Objetivos", "0", "#2a82da")
        self.tarjeta_cumplidos = TarjetaMetrica("Cumplidos", "0", "#28a745")
        self.tarjeta_pendientes = TarjetaMetrica("Pendientes", "0", "#ffc107")
        self.tarjeta_criticos = TarjetaMetrica("Críticos", "0", "#dc3545")

        layout_metricas.addWidget(self.tarjeta_total)
        layout_metricas.addWidget(self.tarjeta_cumplidos)
        layout_metricas.addWidget(self.tarjeta_pendientes)
        layout_metricas.addWidget(self.tarjeta_criticos)
        layout_metricas.addStretch()

        parent_layout.addLayout(layout_metricas)

    def setup_panel_turnos(self, parent_layout):
        """Configura el panel de cumplimiento por turno."""
        grupo_turnos = QGroupBox("Cumplimiento por Turno")
        grupo_turnos.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2a82da;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        layout_turnos = QVBoxLayout(grupo_turnos)
        layout_turnos.setSpacing(10)

        # Barras de progreso para cada turno (se actualizarán con datos reales)
        self.barra_dia = BarraProgresoTurno("Diurno", 0, 1)
        self.barra_noche = BarraProgresoTurno("Nocturno", 0, 1)

        layout_turnos.addWidget(self.barra_dia)
        layout_turnos.addWidget(self.barra_noche)
        layout_turnos.addStretch()

        parent_layout.addWidget(grupo_turnos)

    def setup_panel_detalles(self, parent_layout):
        """Configura el panel de detalles adicionales."""
        grupo_detalles = QGroupBox("Estado General")
        grupo_detalles.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #28a745;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        layout_detalles = QVBoxLayout(grupo_detalles)

        # Estado general
        self.estado_general = QLabel("Calculando estado general...")
        self.estado_general.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
            background-color: #f8f9fa;
        """)
        self.estado_general.setWordWrap(True)

        # Próximas actualizaciones
        self.proximas_alertas = QLabel("Sin alertas pendientes")
        self.proximas_alertas.setStyleSheet("""
            font-size: 12px;
            color: #666;
            padding: 8px;
            border-radius: 3px;
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
        """)
        self.proximas_alertas.setWordWrap(True)

        layout_detalles.addWidget(self.estado_general)
        layout_detalles.addWidget(self.proximas_alertas)
        layout_detalles.addStretch()

        parent_layout.addWidget(grupo_detalles)

    def actualizar_datos(self):
        """Actualiza todas las métricas del dashboard."""
        from PyQt6.QtCore import QDate
        fecha = QDate.currentDate().toString("yyyy-MM-dd")

        try:
            # Obtener datos básicos
            objetivos = obtener_objetivos_del_dia(fecha)

            # Calcular métricas
            total_objetivos = len(objetivos)
            cumplidos = 0
            criticos = 0

            for obj in objetivos:
                obj_id = obj[0]

                # Contar pasadas totales (diurno + nocturno)
                pasadas_dia = self._contar_pasadas(fecha, obj_id, "diurno")
                pasadas_noche = self._contar_pasadas(fecha, obj_id, "nocturno")

                if pasadas_dia > 0 or pasadas_noche > 0:
                    cumplidos += 1

                # Considerar crítico si no tiene ninguna pasada
                if pasadas_dia == 0 and pasadas_noche == 0:
                    criticos += 1

            pendientes = total_objetivos - cumplidos

            # Actualizar tarjetas
            self.tarjeta_total.setText(str(total_objetivos))
            self.tarjeta_cumplidos.setText(str(cumplidos))
            self.tarjeta_pendientes.setText(str(pendientes))
            self.tarjeta_criticos.setText(str(criticos))

            # Actualizar barras de progreso por turno
            cumplidos_dia = sum(1 for obj in objetivos
                              if self._contar_pasadas(fecha, obj[0], "diurno") > 0)
            cumplidos_noche = sum(1 for obj in objetivos
                                if self._contar_pasadas(fecha, obj[0], "nocturno") > 0)

            # Actualizar barras
            self._actualizar_barra_turno(self.barra_dia, cumplidos_dia, total_objetivos)
            self._actualizar_barra_turno(self.barra_noche, cumplidos_noche, total_objetivos)

            # Actualizar estado general
            self._actualizar_estado_general(total_objetivos, cumplidos, criticos)

        except Exception as e:
            print(f"Error actualizando dashboard: {e}")
            import traceback
            traceback.print_exc()

    def _contar_pasadas(self, fecha: str, obj_id: int, turno: str = None) -> int:
        """Cuenta las pasadas para un objetivo y turno específicos."""
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        query = "SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?"
        params = [fecha, obj_id]

        if turno:
            query += " AND turno = ?"
            params.append(turno)

        cursor.execute(query, params)
        resultado = cursor.fetchone()[0]
        conexion.close()
        return resultado

    def _actualizar_barra_turno(self, barra_widget, cumplidos: int, total: int):
        """Actualiza una barra de progreso de turno."""
        porcentaje = int((cumplidos / total * 100) if total > 0 else 0)

        # Acceder a los widgets internos de BarraProgresoTurno
        layout = barra_widget.layout()
        barra = layout.itemAt(1).widget()  # La QProgressBar está en posición 1
        detalle = layout.itemAt(2).widget()  # El QLabel de detalle está en posición 2

        barra.setValue(porcentaje)
        detalle.setText(f"{cumplidos}/{total} objetivos ({porcentaje}%)")

        # Actualizar colores según porcentaje
        if porcentaje >= 80:
            color = "#90EE90"
        elif porcentaje >= 50:
            color = "#FFD700"
        else:
            color = "#FF6B6B"

        barra.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

    def _actualizar_estado_general(self, total: int, cumplidos: int, criticos: int):
        """Actualiza el texto de estado general."""
        if total == 0:
            self.estado_general.setText("No hay objetivos programados para hoy.")
            self.estado_general.setStyleSheet("""
                font-size: 14px; padding: 10px; border-radius: 5px;
                background-color: #e9ecef; color: #6c757d;
            """)
            return

        porcentaje_general = int((cumplidos / total) * 100)

        if porcentaje_general >= 90:
            estado = "EXCELENTE"
            color_bg = "#d4edda"
            color_text = "#155724"
        elif porcentaje_general >= 75:
            estado = "BUENO"
            color_bg = "#d1ecf1"
            color_text = "#0c5460"
        elif porcentaje_general >= 50:
            estado = "REGULAR"
            color_bg = "#fff3cd"
            color_text = "#856404"
        else:
            estado = "CRÍTICO"
            color_bg = "#f8d7da"
            color_text = "#721c24"

        texto = f"""Estado General: {estado} ({porcentaje_general}% de cumplimiento)
• Total objetivos: {total}
• Cumplidos: {cumplidos}
• Pendientes: {total - cumplidos}
• Críticos: {criticos}"""

        self.estado_general.setText(texto)
        self.estado_general.setStyleSheet(f"""
            font-size: 14px; padding: 10px; border-radius: 5px;
            background-color: {color_bg}; color: {color_text};
            border: 1px solid {color_text}20;
        """)

        # Actualizar alertas
        if criticos > 0:
            self.proximas_alertas.setText(f"⚠️ {criticos} objetivos críticos requieren atención inmediata")
            self.proximas_alertas.setStyleSheet("""
                font-size: 12px; color: #721c24; padding: 8px; border-radius: 3px;
                background-color: #f8d7da; border: 1px solid #f5c6cb;
            """)
        else:
            self.proximas_alertas.setText("✅ Todos los objetivos están bajo control")
            self.proximas_alertas.setStyleSheet("""
                font-size: 12px; color: #155724; padding: 8px; border-radius: 3px;
                background-color: #d4edda; border: 1px solid #c3e6cb;
            """)

    def closeEvent(self, event):
        """Detiene el timer al cerrar la ventana."""
        self.timer_actualizacion.stop()
        super().closeEvent(event)