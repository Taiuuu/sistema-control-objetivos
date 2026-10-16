# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de gestión de turnos y fechas operativas
# =============================================================================

import datetime
from services.logger import registrar_accion
from services.sesion import get_usuario_id
from services.calculo_pasadas import (
    HORA_CORTE_TURNO,
    HORA_FIN_DIURNO_MAXIMO,
    HORA_INICIO_DIURNO as HORA_INICIO_DIURNO_CENTRAL,
    HORA_INICIO_NOCHE,
    fecha_de_turno,
    hora_corresponde_a_turno,
    normalizar_turno,
)


class GestorTurnos:
    """
    Gestiona la lógica de turnos incluyendo el manejo de turnos nocturnos
    que cruzan la medianoche.
    """
    
    TURNO_DIURNO = 'diurno'
    TURNO_NOCTURNO = 'nocturno'
    
    # Configuración de horarios
    HORA_INICIO_DIURNO = HORA_INICIO_DIURNO_CENTRAL
    HORA_FIN_DIURNO = HORA_FIN_DIURNO_MAXIMO
    
    HORA_INICIO_NOCTURNO = HORA_INICIO_NOCHE
    HORA_FIN_NOCTURNO = HORA_CORTE_TURNO
    
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
        
        try:
            turno_normalizado = normalizar_turno(turno)
        except ValueError as error:
            raise ValueError(
                f"Turno inválido: '{turno}'. Debe ser '{GestorTurnos.TURNO_DIURNO}' o "
                f"'{GestorTurnos.TURNO_NOCTURNO}'"
            ) from error

        if not hora_corresponde_a_turno(hora_pasada, turno_normalizado):
            raise ValueError(
                f"Hora {hora_pasada.strftime('%H:%M:%S')} fuera del rango de "
                f"turno {turno_normalizado}"
            )
        return fecha_de_turno(
            datetime.datetime.combine(fecha_registro, hora_pasada),
            turno_normalizado,
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
        try:
            return hora_corresponde_a_turno(hora, turno)
        except ValueError:
            return False
    
    @staticmethod
    def obtener_turno_en_hora(hora: datetime.time) -> str:
        """
        Infiere el turno solo cuando la hora no es ambigua.

        Entre 07:00 y 08:00 o entre 19:00 y 20:00 ambos ciclos pueden
        solaparse; sin el turno declarado no se adivina.

        Args:
            hora: Hora a evaluar
        
        Returns:
            str: 'diurno' o 'nocturno'
        """
        if (
            GestorTurnos.HORA_INICIO_DIURNO <= hora < HORA_CORTE_TURNO
            or HORA_INICIO_NOCHE <= hora < HORA_FIN_DIURNO_MAXIMO
        ):
            raise ValueError(
                "La hora puede corresponder a DIA o NOCHE; indique el turno."
            )
        if HORA_CORTE_TURNO <= hora < HORA_INICIO_NOCHE:
            return GestorTurnos.TURNO_DIURNO
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
