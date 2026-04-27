# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Excepciones personalizadas para la capa de servicios
# =============================================================================
"""
Módulo de excepciones personalizadas para servicios.

Define excepciones específicas para operaciones de:
- Caché
- Sincronización
- Reportes
- Usuarios
- Datos
"""


class ServiceError(Exception):
    """Excepción base para errores en servicios."""
    pass


# =============================================================================
# EXCEPCIONES DE CACHÉ
# =============================================================================

class CacheError(ServiceError):
    """Error general en operaciones de caché."""
    pass


class CacheLleno(CacheError):
    """Se lanza cuando el caché alcanza su límite máximo."""
    def __init__(self, tamaño_actual: int, limite: int):
        self.tamaño_actual = tamaño_actual
        self.limite = limite
        super().__init__(
            f"Caché lleno: {tamaño_actual} / {limite} entradas"
        )


class CacheInvalidoError(CacheError):
    """Se lanza cuando hay error invalidando caché."""
    pass


# =============================================================================
# EXCEPCIONES DE SINCRONIZACIÓN
# =============================================================================

class SincronizacionError(ServiceError):
    """Error en operaciones de sincronización."""
    pass


class ConexionError(SincronizacionError):
    """Se lanza cuando hay error de conexión con servidor."""
    def __init__(self, servidor: str, detalles: str):
        self.servidor = servidor
        super().__init__(f"Error conectando a {servidor}: {detalles}")


class ConflictoSincronizacion(SincronizacionError):
    """Se lanza cuando hay conflicto en sincronización de datos."""
    def __init__(self, tabla: str, conflicto_id: int):
        self.tabla = tabla
        self.conflicto_id = conflicto_id
        super().__init__(
            f"Conflicto de sincronización en {tabla} ID {conflicto_id}"
        )


# =============================================================================
# EXCEPCIONES DE REPORTES
# =============================================================================

class ReporteError(ServiceError):
    """Error en generación de reportes."""
    pass


class FechaInvalidaReporte(ReporteError):
    """Se lanza cuando la fecha del reporte no es válida."""
    def __init__(self, fecha: str):
        self.fecha = fecha
        super().__init__(f"Fecha inválida para reporte: {fecha}")


class DatosInsuficientesReporte(ReporteError):
    """Se lanza cuando hay datos insuficientes para generar reporte."""
    def __init__(self, motivo: str):
        super().__init__(f"Datos insuficientes: {motivo}")


# =============================================================================
# EXCEPCIONES DE USUARIOS
# =============================================================================

class UsuarioError(ServiceError):
    """Error en operaciones con usuarios."""
    pass


class UsuarioYaExiste(UsuarioError):
    """Se lanza cuando se intenta crear usuario que ya existe."""
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Usuario '{username}' ya existe")


class ContraseñaInvalida(UsuarioError):
    """Se lanza cuando la contraseña no cumple requisitos."""
    def __init__(self, requisitos: str):
        super().__init__(f"Contraseña inválida: {requisitos}")


class CredencialesIncorrectas(UsuarioError):
    """Se lanza cuando usuario/contraseña son incorrectos."""
    def __init__(self):
        super().__init__("Usuario o contraseña incorrectos")


class PermisoDenegado(UsuarioError):
    """Se lanza cuando el usuario no tiene permisos."""
    def __init__(self, accion: str, rol_requerido: str):
        self.accion = accion
        self.rol_requerido = rol_requerido
        super().__init__(
            f"Permiso denegado para {accion}. Se requiere rol: {rol_requerido}"
        )


# =============================================================================
# EXCEPCIONES DE DATOS
# =============================================================================

class DataProviderError(ServiceError):
    """Error en proveedor de datos."""
    pass


class ProveedorNoDisponible(DataProviderError):
    """Se lanza cuando el proveedor de datos no está disponible."""
    def __init__(self, proveedor: str):
        self.proveedor = proveedor
        super().__init__(f"Proveedor de datos no disponible: {proveedor}")


class DatosCorruptosError(DataProviderError):
    """Se lanza cuando se detectan datos corruptos."""
    def __init__(self, tabla: str, detalles: str):
        super().__init__(f"Datos corruptos en tabla '{tabla}': {detalles}")


# =============================================================================
# EXCEPCIONES DE IMPORTACIÓN/EXPORTACIÓN
# =============================================================================

class ImportExportError(ServiceError):
    """Error en importación o exportación de datos."""
    pass


class FormatoInvalido(ImportExportError):
    """Se lanza cuando el formato de archivo es inválido."""
    def __init__(self, formato_esperado: str, formato_recibido: str):
        super().__init__(
            f"Formato inválido. Esperado: {formato_esperado}, "
            f"Recibido: {formato_recibido}"
        )


class ArchivoNoEncontrado(ImportExportError):
    """Se lanza cuando no se encuentra el archivo."""
    def __init__(self, ruta: str):
        self.ruta = ruta
        super().__init__(f"Archivo no encontrado: {ruta}")


class ErrorExportacion(ImportExportError):
    """Se lanza cuando hay error durante exportación."""
    def __init__(self, motivo: str):
        super().__init__(f"Error durante exportación: {motivo}")


# =============================================================================
# EXCEPCIONES DE BACKUP
# =============================================================================

class BackupError(ServiceError):
    """Error en operaciones de backup."""
    pass


class NoHayEspacioBackup(BackupError):
    """Se lanza cuando no hay espacio para backup."""
    def __init__(self, espacio_requerido: int, espacio_disponible: int):
        super().__init__(
            f"No hay espacio suficiente. Requerido: {espacio_requerido}MB, "
            f"Disponible: {espacio_disponible}MB"
        )


class BackupCorruptoError(BackupError):
    """Se lanza cuando un backup está corrupto."""
    def __init__(self, archivo_backup: str):
        super().__init__(f"Backup corrupto: {archivo_backup}")
