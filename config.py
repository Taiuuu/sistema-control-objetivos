# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Configuración Centralizada
# =============================================================================

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN BASE
# =============================================================================

class Config:
    """Sistema de configuración centralizada con validación y tipos."""

    # Rutas base
    BASE_DIR = Path(__file__).parent
    CONFIG_DIR = BASE_DIR / "config"
    LOGS_DIR = BASE_DIR / "logs"
    BACKUP_DIR = BASE_DIR / "backups"

    # Crear directorios necesarios
    CONFIG_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)

    # =============================================================================
    # CONFIGURACIONES POR DEFECTO
    # =============================================================================

    DEFAULTS = {
        # Base de datos
        "DB_PATH": str(BASE_DIR / "database" / "vesp.db"),
        "DB_TIMEOUT": 30.0,
        "DB_MAX_CONNECTIONS": 10,

        # Seguridad
        "JWT_SECRET_KEY": None,  # Debe configurarse
        "ENCRYPTION_KEY": None,  # Debe configurarse
        "BCRYPT_ROUNDS": 12,
        "SESSION_TIMEOUT_HOURS": 8,
        "SESSION_INACTIVITY_HOURS": 2,
        "RATE_LIMIT_MAX_ATTEMPTS": 5,
        "RATE_LIMIT_WINDOW_MINUTES": 15,

        # Caché
        "CACHE_DEFAULT_TTL": 300,
        "CACHE_MEMORY_LIMIT_MB": 50,
        "CACHE_MAX_ENTRIES": 10000,

        # Logging
        "LOG_LEVEL": "INFO",
        "LOG_MAX_SIZE_MB": 10,
        "LOG_BACKUP_COUNT": 5,
        "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",

        # API
        "API_HOST": "localhost",
        "API_PORT": 5000,
        "API_DEBUG": False,
        "API_TIMEOUT": 30,

        # UI
        "UI_THEME_DEFAULT": "claro",
        "UI_LANGUAGE_DEFAULT": "es",

        # Backup
        "BACKUP_AUTO_ENABLED": True,
        "BACKUP_INTERVAL_HOURS": 24,
        "BACKUP_RETENTION_DAYS": 30,
        "BACKUP_COMPRESSION": True,

        # Validaciones
        "VALIDATION_PASSWORD_MIN_LENGTH": 8,
        "VALIDATION_USERNAME_MIN_LENGTH": 3,
        "VALIDATION_USERNAME_MAX_LENGTH": 50,
        "VALIDATION_NAME_MAX_LENGTH": 100,

        # Límites
        "MAX_FILE_SIZE_MB": 10,
        "MAX_UPLOAD_FILES": 5,
        "MAX_CONCURRENT_USERS": 50,
    }

    def __init__(self):
        self._config = {}
        self._loaded = False
        self.load_config()

    def load_config(self) -> None:
        """Carga configuración desde múltiples fuentes."""
        # 1. Valores por defecto
        self._config = self.DEFAULTS.copy()

        # 2. Variables de entorno
        self._load_from_env()

        # 3. Archivo de configuración JSON
        self._load_from_file()

        # 4. Validar configuración crítica
        self._validate_config()

        self._loaded = True

    def _load_from_env(self) -> None:
        """Carga configuración desde variables de entorno."""
        env_mappings = {
            "VESP_DB_PATH": "DB_PATH",
            "VESP_JWT_SECRET": "JWT_SECRET_KEY",
            "VESP_ENCRYPTION_KEY": "ENCRYPTION_KEY",
            "VESP_LOG_LEVEL": "LOG_LEVEL",
            "VESP_API_HOST": "API_HOST",
            "VESP_API_PORT": "API_PORT",
            "VESP_API_DEBUG": "API_DEBUG",
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convertir tipos automáticamente
                if config_key.endswith("_PORT"):
                    self._config[config_key] = int(value)
                elif config_key.endswith("_DEBUG"):
                    self._config[config_key] = value.lower() in ('true', '1', 'yes')
                elif config_key.endswith("_HOURS") or config_key.endswith("_MINUTES"):
                    self._config[config_key] = int(value)
                else:
                    self._config[config_key] = value

    def _load_from_file(self) -> None:
        """Carga configuración desde archivo JSON."""
        config_file = self.CONFIG_DIR / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)

                # Fusionar con configuración existente
                for key, value in file_config.items():
                    if key in self._config:
                        self._config[key] = value

            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error cargando configuración desde archivo: {e}")

    def _validate_config(self) -> None:
        """Valida configuración crítica."""
        required_keys = ["JWT_SECRET_KEY", "ENCRYPTION_KEY"]

        for key in required_keys:
            if not self._config.get(key):
                raise RuntimeError(
                    f"Configuración crítica faltante: {key}\n"
                    "Configure la variable de entorno o el archivo config.json"
                )

        # Validar tipos y rangos
        if self._config["API_PORT"] < 1 or self._config["API_PORT"] > 65535:
            raise ValueError("Puerto API inválido")

        if self._config["BCRYPT_ROUNDS"] < 4 or self._config["BCRYPT_ROUNDS"] > 20:
            raise ValueError("Rounds de bcrypt inválidos")

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Establece un valor de configuración."""
        if key not in self.DEFAULTS:
            raise KeyError(f"Clave de configuración desconocida: {key}")

        self._config[key] = value

    def save_to_file(self) -> None:
        """Guarda configuración actual a archivo."""
        config_file = self.CONFIG_DIR / "config.json"

        # Solo guardar valores que difieren de los defaults
        to_save = {}
        for key, value in self._config.items():
            if value != self.DEFAULTS.get(key):
                to_save[key] = value

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(to_save, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Error guardando configuración: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Retorna toda la configuración."""
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Restaura configuración a valores por defecto."""
        self._config = self.DEFAULTS.copy()
        self._loaded = True

# =============================================================================
# INSTANCIA GLOBAL
# =============================================================================

config = Config()

# =============================================================================
# FUNCIONES DE ACCESO RÁPIDO
# =============================================================================

def get_config(key: str, default: Any = None) -> Any:
    """Función de acceso rápido a configuración."""
    return config.get(key, default)

def set_config(key: str, value: Any) -> None:
    """Función de acceso rápido para establecer configuración."""
    config.set(key, value)

def save_config() -> None:
    """Guarda configuración actual."""
    config.save_to_file()