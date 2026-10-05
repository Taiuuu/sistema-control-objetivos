"""Utilities for converting theme colors into Qt color values."""

import re

from PyQt6.QtGui import QColor


_RGBA_PATTERN = re.compile(
    r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
)


def parse_color(value: str) -> QColor:
    """Parse a QColor name/hex value or CSS rgba() token."""
    if not isinstance(value, str):
        raise TypeError("El color debe ser una cadena.")

    match = _RGBA_PATTERN.fullmatch(value)
    if match:
        channels = tuple(map(int, match.groups()))
        if any(channel > 255 for channel in channels):
            raise ValueError(f"Canal de color fuera de rango: {value!r}")
        return QColor(*channels)

    color = QColor(value)
    if not color.isValid():
        raise ValueError(f"Color no válido: {value!r}")
    return color
