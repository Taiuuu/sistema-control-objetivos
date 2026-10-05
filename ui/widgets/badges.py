"""Badges de compatibilidad que siguen el tema visual activo."""

from ui.components import CountChip, StatusBadge


class BadgeEstado(StatusBadge):
    """Badge legado para estados de cobertura."""

    _MAPA = {
        "Pasaron los dos": ("ok", "✔  Pasaron los dos"),
        "No pasó noche": ("warning", "🌙  No pasó noche"),
        "No pasó día": ("warning", "☀  No pasó día"),
        "No pasó nadie": ("danger", "✖  No pasó nadie"),
    }

    def __init__(self, estado: str, oscuro: bool = False, parent=None):
        status, texto = self._MAPA.get(estado, ("info", estado))
        super().__init__(texto, status, parent)


class BadgeNumero(CountChip):
    """Badge numérico legado para contadores de pasadas."""

    def __init__(self, numero: int, oscuro: bool = False, parent=None):
        super().__init__(numero, parent)
