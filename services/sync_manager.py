# =============================================================================
# VESP Organizations - Sistema de Sincronización
# Preparado para multi-usuario y trabajo offline/online
# =============================================================================

import json
import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
from services.data_provider import get_data_provider, Pasada, Objetivo


@dataclass
class CambioPendiente:
    """Representa un cambio que espera sincronización."""
    id: str
    tipo: str  # 'pasada', 'objetivo', etc.
    operacion: str  # 'crear', 'actualizar', 'eliminar'
    datos: Dict[str, Any]
    timestamp: float
    intentos: int = 0
    ultimo_error: Optional[str] = None


class SyncManager:
    """Gestiona la sincronización de datos entre local y remoto."""

    def __init__(self):
        self.cambios_pendientes: List[CambioPendiente] = []
        self.esta_conectado = False
        self.ultima_sync = None
        self._cargar_cambios_pendientes()
        self._iniciar_monitor_conexion()

    def _cargar_cambios_pendientes(self):
        """Carga cambios pendientes desde archivo local."""
        try:
            if os.path.exists('sync_queue.json'):
                with open('sync_queue.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cambios_pendientes = [
                        CambioPendiente(**c) for c in data.get('cambios', [])
                    ]
                    self.ultima_sync = data.get('ultima_sync')
        except Exception as e:
            print(f"Error cargando cambios pendientes: {e}")

    def _guardar_cambios_pendientes(self):
        """Guarda cambios pendientes en archivo local."""
        try:
            data = {
                'cambios': [asdict(c) for c in self.cambios_pendientes],
                'ultima_sync': self.ultima_sync
            }
            with open('sync_queue.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando cambios pendientes: {e}")

    def _iniciar_monitor_conexion(self):
        """Inicia monitoreo de conexión en segundo plano."""
        def monitor():
            while True:
                try:
                    # TODO: Implementar verificación real de conexión
                    self.esta_conectado = self._verificar_conexion()
                    if self.esta_conectado and self.cambios_pendientes:
                        self._sincronizar_cambios_pendientes()
                    time.sleep(30)  # Verificar cada 30 segundos
                except Exception as e:
                    print(f"Error en monitor de conexión: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _verificar_conexion(self) -> bool:
        """Verifica si hay conexión al servidor."""
        # TODO: Implementar verificación real (ping al servidor)
        return False  # Por ahora siempre offline

    def agregar_cambio_pendiente(self, tipo: str, operacion: str, datos: Dict[str, Any]):
        """Agrega un cambio a la cola de sincronización."""
        cambio = CambioPendiente(
            id=f"{tipo}_{operacion}_{int(time.time())}_{hash(str(datos))}",
            tipo=tipo,
            operacion=operacion,
            datos=datos,
            timestamp=time.time()
        )

        self.cambios_pendientes.append(cambio)
        self._guardar_cambios_pendientes()

        print(f"Cambio agregado a cola: {tipo} {operacion}")

    def _sincronizar_cambios_pendientes(self):
        """Intenta sincronizar cambios pendientes."""
        if not self.esta_conectado:
            return

        cambios_exitosos = []
        for cambio in self.cambios_pendientes:
            try:
                if self._enviar_cambio_a_servidor(cambio):
                    cambios_exitosos.append(cambio)
                    print(f"Cambio sincronizado: {cambio.tipo} {cambio.operacion}")
                else:
                    cambio.intentos += 1
                    cambio.ultimo_error = "Error enviando a servidor"
            except Exception as e:
                cambio.intentos += 1
                cambio.ultimo_error = str(e)

        # Remover cambios exitosos
        for cambio in cambios_exitosos:
            self.cambios_pendientes.remove(cambio)

        if cambios_exitosos:
            self._guardar_cambios_pendientes()

    def _enviar_cambio_a_servidor(self, cambio: CambioPendiente) -> bool:
        """Envía un cambio al servidor remoto."""
        # TODO: Implementar envío real a API
        return False  # Por ahora simular fallo

    def crear_pasada_offline(self, fecha: str, hora: str, turno: str,
                           supervisor_id: int, objetivo_id: int, notas: str = None) -> bool:
        """Crea una pasada que se sincronizará cuando haya conexión."""

        # Calcular fecha operativa (lógica de turnos nocturnos)
        from services.gestor_turnos import calcular_fecha_operativa
        fecha_operativa = calcular_fecha_operativa(fecha, hora, turno)

        # Crear en local
        pasada_data = {
            'fecha': fecha,
            'hora': hora,
            'turno': turno,
            'supervisor_id': supervisor_id,
            'objetivo_id': objetivo_id,
            'notas': notas,
            'fecha_operativa': fecha_operativa
        }

        # Intentar crear localmente primero
        provider = get_data_provider()
        pasada = Pasada(
            id=0,  # Se asignará en BD
            fecha=fecha,
            hora=hora,
            turno=turno,
            supervisor_id=supervisor_id,
            objetivo_id=objetivo_id,
            notas=notas,
            fecha_operativa=fecha_operativa
        )

        if provider.crear_pasada(pasada):
            # Si se creó localmente, agregarlo a cola de sync por si hay servidor
            self.agregar_cambio_pendiente('pasada', 'crear', pasada_data)
            return True

        return False

    def obtener_estado_sincronizacion(self) -> Dict[str, Any]:
        """Obtiene el estado actual de sincronización."""
        return {
            'conectado': self.esta_conectado,
            'cambios_pendientes': len(self.cambios_pendientes),
            'ultima_sync': self.ultima_sync,
            'cambios_detalle': [
                {
                    'tipo': c.tipo,
                    'operacion': c.operacion,
                    'timestamp': datetime.fromtimestamp(c.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                    'intentos': c.intentos,
                    'error': c.ultimo_error
                } for c in self.cambios_pendientes[:10]  # Últimos 10
            ]
        }

    def forzar_sincronizacion(self) -> Dict[str, Any]:
        """Fuerza una sincronización manual."""
        if not self.esta_conectado:
            return {'exito': False, 'mensaje': 'No hay conexión al servidor'}

        try:
            self._sincronizar_cambios_pendientes()
            # TODO: También descargar cambios del servidor
            self.ultima_sync = time.time()
            self._guardar_cambios_pendientes()

            return {
                'exito': True,
                'mensaje': f'Sincronización completada. Cambios pendientes: {len(self.cambios_pendientes)}'
            }
        except Exception as e:
            return {'exito': False, 'mensaje': f'Error en sincronización: {str(e)}'}


# Instancia global del manager de sincronización
sync_manager = SyncManager()


def get_sync_manager() -> SyncManager:
    """Obtiene el manager de sincronización."""
    return sync_manager
