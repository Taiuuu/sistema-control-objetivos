# =============================================================================
# VESP Organizations - Sistema de Sincronización
# Cola local preparada para servidor remoto (desactivada por defecto)
# =============================================================================

import json
import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
from services.data_provider import get_data_provider, Pasada
from services.gestor_turnos import GestorTurnos
from services.config_app import sync_remoto_habilitado, ruta_sync_queue


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
    """Gestiona la cola de sincronización (solo activa con VESP_SYNC_REMOTO=1)."""

    def __init__(self):
        self.cambios_pendientes: List[CambioPendiente] = []
        self.esta_conectado = False
        self.ultima_sync = None
        self._remoto_habilitado = sync_remoto_habilitado()
        self._cargar_cambios_pendientes()
        if self._remoto_habilitado:
            self._iniciar_monitor_conexion()

    def _cargar_cambios_pendientes(self):
        """Carga cambios pendientes desde archivo local."""
        try:
            ruta = ruta_sync_queue()
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cambios_pendientes = [
                        CambioPendiente(**c) for c in data.get('cambios', [])
                    ]
                    self.ultima_sync = data.get('ultima_sync')
        except Exception as e:
            print(f"Error cargando cambios pendientes: {e}")

    def _guardar_cambios_pendientes(self):
        """Guarda cambios pendientes en archivo local."""
        if not self._remoto_habilitado:
            return
        try:
            os.makedirs(os.path.dirname(ruta_sync_queue()), exist_ok=True)
            data = {
                'cambios': [asdict(c) for c in self.cambios_pendientes],
                'ultima_sync': self.ultima_sync
            }
            with open(ruta_sync_queue(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando cambios pendientes: {e}")

    def _iniciar_monitor_conexion(self):
        """Inicia monitoreo de conexión en segundo plano (solo modo remoto)."""
        def monitor():
            while True:
                try:
                    self.esta_conectado = self._verificar_conexion()
                    if self.esta_conectado and self.cambios_pendientes:
                        self._sincronizar_cambios_pendientes()
                    time.sleep(30)
                except Exception as e:
                    print(f"Error en monitor de conexión: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _verificar_conexion(self) -> bool:
        """Verifica si hay conexión al servidor remoto."""
        return False

    def agregar_cambio_pendiente(self, tipo: str, operacion: str, datos: Dict[str, Any]):
        """Agrega un cambio a la cola (solo si sync remoto está habilitado)."""
        if not self._remoto_habilitado:
            return

        cambio = CambioPendiente(
            id=f"{tipo}_{operacion}_{int(time.time())}_{hash(str(datos))}",
            tipo=tipo,
            operacion=operacion,
            datos=datos,
            timestamp=time.time()
        )

        self.cambios_pendientes.append(cambio)
        self._guardar_cambios_pendientes()

    def _sincronizar_cambios_pendientes(self):
        """Intenta sincronizar cambios pendientes."""
        if not self.esta_conectado:
            return

        cambios_exitosos = []
        for cambio in self.cambios_pendientes:
            try:
                if self._enviar_cambio_a_servidor(cambio):
                    cambios_exitosos.append(cambio)
                else:
                    cambio.intentos += 1
                    cambio.ultimo_error = "Error enviando a servidor"
            except Exception as e:
                cambio.intentos += 1
                cambio.ultimo_error = str(e)

        for cambio in cambios_exitosos:
            self.cambios_pendientes.remove(cambio)

        if cambios_exitosos:
            self._guardar_cambios_pendientes()

    def _enviar_cambio_a_servidor(self, cambio: CambioPendiente) -> bool:
        """Envía un cambio al servidor remoto (pendiente de implementar)."""
        return False

    def crear_pasada_offline(self, fecha: str, hora: str, turno: str,
                           supervisor_id: int, objetivo_id: int, notas: str = None,
                           validar_turno: bool = True) -> bool:
        """Crea una pasada en la base local."""

        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        hora_obj = None
        for formato in ("%H:%M:%S", "%H:%M"):
            try:
                hora_obj = datetime.strptime(hora, formato).time()
                break
            except ValueError:
                continue
        if hora_obj is None:
            raise ValueError(f"Formato de hora inválido: {hora}")

        if validar_turno:
            fecha_operativa_obj = GestorTurnos.calcular_fecha_operativa(fecha_obj, hora_obj, turno)
            fecha_operativa = fecha_operativa_obj.strftime("%Y-%m-%d")
        else:
            fecha_operativa = fecha

        pasada_data = {
            'fecha': fecha,
            'hora': hora,
            'turno': turno,
            'supervisor_id': supervisor_id,
            'objetivo_id': objetivo_id,
            'notas': notas,
            'fecha_operativa': fecha_operativa
        }

        provider = get_data_provider()
        pasada = Pasada(
            id=0,
            fecha=fecha,
            hora=hora,
            turno=turno,
            supervisor_id=supervisor_id,
            objetivo_id=objetivo_id,
            notas=notas,
            fecha_operativa=fecha_operativa
        )

        if provider.crear_pasada(pasada):
            self.agregar_cambio_pendiente('pasada', 'crear', pasada_data)
            return True

        return False

    def obtener_estado_sincronizacion(self) -> Dict[str, Any]:
        """Obtiene el estado actual de sincronización."""
        return {
            'remoto_habilitado': self._remoto_habilitado,
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
                } for c in self.cambios_pendientes[:10]
            ]
        }

    def forzar_sincronizacion(self) -> Dict[str, Any]:
        """Fuerza una sincronización manual."""
        if not self._remoto_habilitado:
            return {
                'exito': False,
                'mensaje': 'Sincronización remota desactivada (modo solo escritorio).'
            }
        if not self.esta_conectado:
            return {'exito': False, 'mensaje': 'No hay conexión al servidor'}

        try:
            self._sincronizar_cambios_pendientes()
            self.ultima_sync = time.time()
            self._guardar_cambios_pendientes()
            return {
                'exito': True,
                'mensaje': f'Sincronización completada. Cambios pendientes: {len(self.cambios_pendientes)}'
            }
        except Exception as e:
            return {'exito': False, 'mensaje': f'Error en sincronización: {str(e)}'}


_sync_manager: Optional[SyncManager] = None
_sync_lock = threading.Lock()


def get_sync_manager() -> SyncManager:
    """Obtiene el manager de sincronización (instancia única, sin hilo si no hay remoto)."""
    global _sync_manager
    if _sync_manager is None:
        with _sync_lock:
            if _sync_manager is None:
                _sync_manager = SyncManager()
    return _sync_manager
