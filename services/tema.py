# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Gestión de temas de la aplicación
# =============================================================================

# Estado global del tema
tema_actual = "oscuro"


def obtener_tema_actual():
    """Retorna el tema actual de la aplicación."""
    return tema_actual


def establecer_tema_actual(tema):
    """Establece el tema actual de la aplicación."""
    global tema_actual
    tema_actual = tema