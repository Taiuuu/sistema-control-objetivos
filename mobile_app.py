# =============================================================================
# VESP Organizations - App Móvil Android (Kivy)
# Supervisores en campo registran pasadas desde tablets Android
#
# Para compilar APK:
#   pip install kivy buildozer cython
#   buildozer android debug
#
# Versión Android: Kivy
# Versión iOS: Flutter (ver mobile/ios/README.md)
# =============================================================================

import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock

import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Importar servicios (ajustar rutas según sea necesario)
try:
    from services.sync_manager import get_sync_manager
    from services.data_provider import get_data_provider
except ImportError:
    # Para desarrollo/testing sin los servicios completos
    class MockSyncManager:
        def crear_pasada_offline(self, *args, **kwargs): return True
        def obtener_estado_sincronizacion(self): return {"conectado": False, "cambios_pendientes": 0}

    class MockDataProvider:
        def get_objetivos(self): return []
        def get_supervisores(self): return []

    get_sync_manager = lambda: MockSyncManager()
    get_data_provider = lambda: MockDataProvider()


class LoginScreen(Screen):
    """Pantalla de login."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # Logo
        logo = Label(text='V.E.S.P\nSupervisor', font_size=dp(24), bold=True,
                    size_hint_y=0.3, halign='center')
        self.layout.add_widget(logo)

        # Usuario
        user_layout = BoxLayout(size_hint_y=0.15)
        user_layout.add_widget(Label(text='Usuario:', size_hint_x=0.3))
        self.user_input = TextInput(multiline=False, size_hint_x=0.7)
        user_layout.add_widget(self.user_input)
        self.layout.add_widget(user_layout)

        # Contraseña
        pass_layout = BoxLayout(size_hint_y=0.15)
        pass_layout.add_widget(Label(text='Contraseña:', size_hint_x=0.3))
        self.pass_input = TextInput(password=True, multiline=False, size_hint_x=0.7)
        pass_layout.add_widget(self.pass_input)
        self.layout.add_widget(pass_layout)

        # Botón login
        self.login_btn = Button(text='Iniciar Sesión', size_hint_y=0.2,
                               background_color=(0.2, 0.6, 1, 1))
        self.login_btn.bind(on_press=self.do_login)
        self.layout.add_widget(self.login_btn)

        # Estado
        self.status_label = Label(text='', size_hint_y=0.2, color=(1, 0, 0, 1))
        self.layout.add_widget(self.status_label)

        self.add_widget(self.layout)

    def do_login(self, instance):
        """Realiza el login."""
        usuario = self.user_input.text.strip()
        password = self.pass_input.text.strip()

        if not usuario or not password:
            self.status_label.text = 'Complete todos los campos'
            return

        # TODO: Implementar autenticación real
        # Por ahora aceptar cualquier usuario/contraseña
        self.manager.current = 'main'


class MainScreen(Screen):
    """Pantalla principal de registro de pasadas."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout principal
        main_layout = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(size_hint_y=0.1, padding=dp(10))
        header.add_widget(Label(text='Registro de Pasadas', bold=True, font_size=dp(18)))
        sync_btn = Button(text='Sync', size_hint_x=0.3, background_color=(0.2, 0.8, 0.2, 1))
        sync_btn.bind(on_press=self.show_sync_status)
        header.add_widget(sync_btn)
        main_layout.add_widget(header)

        # Formulario
        form_layout = BoxLayout(orientation='vertical', size_hint_y=0.6, padding=dp(10), spacing=dp(5))

        # Objetivo
        obj_layout = BoxLayout(size_hint_y=0.2)
        obj_layout.add_widget(Label(text='Objetivo:', size_hint_x=0.3))
        self.objetivo_spinner = Spinner(
            text='Seleccionar...',
            values=['Centro Comercial A', 'Banco Central', 'Shopping Plaza'],  # TODO: Cargar dinámicamente
            size_hint_x=0.7
        )
        obj_layout.add_widget(self.objetivo_spinner)
        form_layout.add_widget(obj_layout)

        # Turno
        turno_layout = BoxLayout(size_hint_y=0.2)
        turno_layout.add_widget(Label(text='Turno:', size_hint_x=0.3))
        self.turno_spinner = Spinner(
            text='Seleccionar...',
            values=['diurno', 'nocturno'],
            size_hint_x=0.7
        )
        turno_layout.add_widget(self.turno_spinner)
        form_layout.add_widget(turno_layout)

        # Notas
        notas_layout = BoxLayout(size_hint_y=0.3)
        notas_layout.add_widget(Label(text='Notas:', size_hint_x=0.3))
        self.notas_input = TextInput(multiline=True, size_hint_x=0.7)
        notas_layout.add_widget(self.notas_input)
        form_layout.add_widget(notas_layout)

        # Botón registrar
        self.registrar_btn = Button(text='REGISTRAR PASADA', size_hint_y=0.3,
                                   background_color=(0.2, 0.8, 0.2, 1), bold=True)
        self.registrar_btn.bind(on_press=self.registrar_pasada)
        form_layout.add_widget(self.registrar_btn)

        main_layout.add_widget(form_layout)

        # Lista de pasadas del día
        list_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        list_layout.add_widget(Label(text='Pasadas de Hoy:', bold=True, size_hint_y=0.1))

        self.scroll_view = ScrollView(size_hint_y=0.9)
        self.pasadas_layout = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.pasadas_layout.bind(minimum_height=self.pasadas_layout.setter('height'))
        self.scroll_view.add_widget(self.pasadas_layout)
        list_layout.add_widget(self.scroll_view)

        main_layout.add_widget(list_layout)

        self.add_widget(main_layout)

        # Cargar pasadas iniciales
        Clock.schedule_once(lambda dt: self.cargar_pasadas_hoy(), 0.1)

    def registrar_pasada(self, instance):
        """Registra una nueva pasada."""
        objetivo = self.objetivo_spinner.text
        turno = self.turno_spinner.text
        notas = self.notas_input.text

        if objetivo == 'Seleccionar...' or turno == 'Seleccionar...':
            self.show_popup('Error', 'Seleccione objetivo y turno')
            return

        # Obtener fecha y hora actual
        ahora = datetime.now()
        fecha = ahora.strftime('%Y-%m-%d')
        hora = ahora.strftime('%H:%M')

        # TODO: Obtener IDs reales de supervisor y objetivo
        supervisor_id = 1  # Mock
        objetivo_id = 1    # Mock

        # Registrar usando sync manager
        sync_mgr = get_sync_manager()
        if sync_mgr.crear_pasada_offline(fecha, hora, turno, supervisor_id, objetivo_id, notas):
            self.show_popup('Éxito', 'Pasada registrada correctamente')

            # Limpiar formulario
            self.objetivo_spinner.text = 'Seleccionar...'
            self.turno_spinner.text = 'Seleccionar...'
            self.notas_input.text = ''

            # Recargar lista
            self.cargar_pasadas_hoy()
        else:
            self.show_popup('Error', 'Error registrando pasada')

    def cargar_pasadas_hoy(self):
        """Carga las pasadas del día actual."""
        self.pasadas_layout.clear_widgets()

        # TODO: Cargar pasadas reales del día
        # Por ahora mostrar datos mock
        pasadas_mock = [
            {'hora': '08:30', 'objetivo': 'Centro Comercial A', 'turno': 'diurno'},
            {'hora': '14:15', 'objetivo': 'Banco Central', 'turno': 'diurno'},
        ]

        for pasada in pasadas_mock:
            item = Button(
                text=f"{pasada['hora']} - {pasada['objetivo']} ({pasada['turno']})",
                size_hint_y=None,
                height=dp(40),
                background_color=(0.9, 0.9, 0.9, 1),
                color=(0, 0, 0, 1)
            )
            self.pasadas_layout.add_widget(item)

    def show_sync_status(self, instance):
        """Muestra el estado de sincronización."""
        sync_mgr = get_sync_manager()
        estado = sync_mgr.obtener_estado_sincronizacion()

        mensaje = f"""
        Estado: {'Conectado' if estado['conectado'] else 'Offline'}
        Cambios pendientes: {estado['cambios_pendientes']}
        """

        if estado['cambios_pendientes'] > 0:
            mensaje += "\n\nCambios se sincronizarán cuando haya conexión."

        self.show_popup('Estado de Sincronización', mensaje)

    def show_popup(self, titulo, mensaje):
        """Muestra un popup con mensaje."""
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=mensaje))

        btn_layout = BoxLayout(size_hint_y=0.3)
        close_btn = Button(text='Cerrar')
        btn_layout.add_widget(close_btn)

        popup_layout.add_widget(btn_layout)

        popup = Popup(title=titulo, content=popup_layout, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class VESPMobileApp(App):
    """Aplicación móvil principal."""

    def build(self):
        # Configurar ventana
        Window.size = (400, 700)  # Tamaño típico de móvil
        Window.title = 'VESP Supervisor'

        # Screen manager
        sm = ScreenManager()

        # Agregar pantallas
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))

        # Iniciar en login
        sm.current = 'login'

        return sm


if __name__ == '__main__':
    VESPMobileApp().run()</content>
<parameter name="filePath">c:\Vesp taiu\sistema-control-objetivos\mobile_app.py