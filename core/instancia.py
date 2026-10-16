"""Bloqueo de instancia asociado a la ruta exacta de la base."""

from PyQt6.QtCore import QLockFile


def adquirir_bloqueo_instancia(ruta_base: str) -> QLockFile | None:
    """Devuelve el bloqueo exclusivo o None si ya existe una instancia."""
    bloqueo = QLockFile(f"{ruta_base}.lock")
    bloqueo.setStaleLockTime(30000)
    return bloqueo if bloqueo.tryLock(0) else None
