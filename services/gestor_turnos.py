# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de turnos y fechas operativas
# =============================================================================

import datetime
from services.logger import registrar_accion
from services.sesion import get_usuario_id


class GestorTurnos:
    """
    Gestiona la lógica de turnos incluyendo el manejo de turnos nocturnos
    que cruzan la medianoche.
    """
    
    TURNO_DIURNO = 'diurno'
    TURNO_NOCTURNO = 'nocturno'
    
    # Configuración de horarios
    HORA_INICIO_DIURNO = datetime.time(7, 0)      # 07:00
    HORA_FIN_DIURNO = datetime.time(19, 0)         # 19:00
    
    HORA_INICIO_NOCTURNO = datetime.time(19, 0)   # 19:00
    HORA_FIN_NOCTURNO = datetime.time(7, 0)        # 07:00 (día siguiente)
    
    @staticmethod
    def calcular_fecha_operativa(
        fecha_registro: datetime.date,
        hora_pasada: datetime.time,
        turno: str
    ) -> datetime.date:
        """
        Calcula la fecha operativa de una pasada considerando turnos que cruzan medianoche.
        
        Esta es la lógica CRÍTICA del sistema. Una pasada nocturna que ocurre
        después de medianoche (ej: 03:00 AM) pertenece al turno nocturno del día anterior.
        
        Args:
            fecha_registro: Fecha en que se registró/ocurrió la pasada
            hora_pasada: Hora exacta de la pasada (HH:MM:SS)
            turno: 'diurno' o 'nocturno'
        
        Returns:
            datetime.date: La fecha operativa para contabilización
        
        Ejemplos:
            Caso 1: Turno diurno
            - Entrada: fecha=21/04, hora=14:30, turno='diurno'
            - Retorno: 21/04 ✓
            
            Caso 2: Turno nocturno (antes de medianoche)
            - Entrada: fecha=21/04, hora=22:15, turno='nocturno'
            - Retorno: 21/04 ✓
            
            Caso 3: Turno nocturno (después de medianoche)
            - Entrada: fecha=22/04, hora=03:00, turno='nocturno'
            - Retorno: 21/04 ✓ (pertenece al turno nocturno de 21/04)
        
        Raises:
            ValueError: Si la hora no es válida para el turno especificado
        """
        
        if turno == GestorTurnos.TURNO_DIURNO:
            # Turno diurno: 07:00 - 19:00
            # La fecha operativa es siempre la misma que el registro
            if not (GestorTurnos.HORA_INICIO_DIURNO <= hora_pasada < GestorTurnos.HORA_FIN_DIURNO):
                raise ValueError(
                    f"Hora {hora_pasada.strftime('%H:%M:%S')} fuera del rango de turno diurno "
                    f"({GestorTurnos.HORA_INICIO_DIURNO.strftime('%H:%M')} - "
                    f"{GestorTurnos.HORA_FIN_DIURNO.strftime('%H:%M')})"
                )
            return fecha_registro
        
        elif turno == GestorTurnos.TURNO_NOCTURNO:
            # Turno nocturno: 19:00 - 07:00 (cruza medianoche)
            
            if datetime.time(19, 0) <= hora_pasada <= datetime.time(23, 59, 59):
                # Pasada registrada entre 19:00 y 23:59:59
                # Pertenece al turno nocturno del MISMO DÍA
                return fecha_registro
            
            elif datetime.time(0, 0) <= hora_pasada < datetime.time(7, 0):
                # Pasada registrada entre 00:00:00 y 06:59:59
                # Pertenece al turno nocturno del DÍA ANTERIOR
                return fecha_registro - datetime.timedelta(days=1)
            
            else:
                raise ValueError(
                    f"Hora {hora_pasada.strftime('%H:%M:%S')} fuera del rango de turno nocturno "
                    f"(19:00-23:59 o 00:00-06:59)"
                )
        
        else:
            raise ValueError(
                f"Turno inválido: '{turno}'. Debe ser '{GestorTurnos.TURNO_DIURNO}' o "
                f"'{GestorTurnos.TURNO_NOCTURNO}'"
            )
    
    @staticmethod
    def validar_hora_turno(hora: datetime.time, turno: str) -> bool:
        """
        Valida que la hora sea válida para el turno especificado.
        
        Args:
            hora: Hora a validar
            turno: Tipo de turno
        
        Returns:
            bool: True si la hora es válida para el turno
        """
        if turno == GestorTurnos.TURNO_DIURNO:
            return GestorTurnos.HORA_INICIO_DIURNO <= hora < GestorTurnos.HORA_FIN_DIURNO
        elif turno == GestorTurnos.TURNO_NOCTURNO:
            return hora >= datetime.time(19, 0) or hora < datetime.time(7, 0)
        return False
    
    @staticmethod
    def obtener_turno_en_hora(hora: datetime.time) -> str:
        """
        Determina automáticamente el turno basado en la hora.
        
        Args:
            hora: Hora a evaluar
        
        Returns:
            str: 'diurno' o 'nocturno'
        """
        if GestorTurnos.HORA_INICIO_DIURNO <= hora < GestorTurnos.HORA_FIN_DIURNO:
            return GestorTurnos.TURNO_DIURNO
        else:
            return GestorTurnos.TURNO_NOCTURNO
    
    @staticmethod
    def es_turno_nocturno(turno: str) -> bool:
        """Verifica si el turno es nocturno."""
        return turno == GestorTurnos.TURNO_NOCTURNO
    
    @staticmethod
    def es_turno_diurno(turno: str) -> bool:
        """Verifica si el turno es diurno."""
        return turno == GestorTurnos.TURNO_DIURNO
    
    @staticmethod
    def obtener_rango_turno_diurno() -> tuple:
        """Retorna (inicio, fin) del turno diurno."""
        return (GestorTurnos.HORA_INICIO_DIURNO, GestorTurnos.HORA_FIN_DIURNO)
    
    @staticmethod
    def obtener_rango_turno_nocturno() -> tuple:
        """
        Retorna el rango del turno nocturno.
        Nota: retorna dos rangos porque cruza medianoche.
        """
        return (GestorTurnos.HORA_INICIO_NOCTURNO, datetime.time(23, 59, 59)), \
               (datetime.time(0, 0), GestorTurnos.HORA_FIN_NOCTURNO)


# Instancia global para fácil acceso
gestor_turnos = GestorTurnos()
