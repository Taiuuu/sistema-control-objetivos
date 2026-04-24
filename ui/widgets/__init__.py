# =============================================================================
# VESP Organizations - Paquete de Widgets Modulares
# =============================================================================

from ui.widgets.badges import BadgeEstado, BadgeNumero
from ui.widgets.estilos import obtener_color, PALETA_OSCURA, PALETA_CLARA
from ui.widgets.sidebar import SidebarWidget, BotonMenu, crear_separador
from ui.widgets.tabla_cobertura import TablaCoberturaWidget

__all__ = [
    'BadgeEstado',
    'BadgeNumero',
    'obtener_color',
    'PALETA_OSCURA',
    'PALETA_CLARA',
    'SidebarWidget',
    'BotonMenu',
    'crear_separador',
    'TablaCoberturaWidget',
]