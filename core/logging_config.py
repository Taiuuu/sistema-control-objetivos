"""Configuración común del registro persistente de VESP."""

import logging
from logging.handlers import RotatingFileHandler

from core.configuracion import LOG_DIR, asegurar_directorios


def configurar_logging() -> logging.Logger:
    """Configura un archivo rotativo para que los errores no queden ocultos."""
    asegurar_directorios()
    logger = logging.getLogger("vesp")
    logger.setLevel(logging.INFO)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", "").lower()
        == str(LOG_DIR / "vesp.log").lower()
        for handler in root.handlers
    ):
        handler = RotatingFileHandler(
            LOG_DIR / "vesp.log",
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        ))
        root.addHandler(handler)
    return logger
