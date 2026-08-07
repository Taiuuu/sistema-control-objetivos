# =============================================================================
# VESP Organizations - Sistema de Importación Universal
# Soporta Excel (formato oficial CONTROL_RECORRIDOS, y hoja "Pasadas"),
# JSON (tablets), y preparado para más formatos.
# =============================================================================

import json
import logging
import os
import re
import unicodedata
import tempfile
import threading
import weakref
from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable, Set

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

logger = logging.getLogger(__name__)

from database.gestor_db import gestor_db
from .gestor_turnos import GestorTurnos
from .sync_manager import get_sync_manager


@dataclass
class RegistroImportacion:
    """Representa un registro a importar."""
    fecha: str
    hora: str
    turno: str
    supervisor: str
    objetivo: str
    fuente: str
    notas: Optional[str] = None
    sheet_title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fecha': self.fecha,
            'hora': self.hora,
            'turno': self.turno,
            'supervisor': self.supervisor,
            'objetivo': self.objetivo,
            'notas': self.notas,
            'fuente': self.fuente,
            'sheet_title': self.sheet_title,
        }


@dataclass
class ResultadoImportacion:
    """Resultado de una importación."""
    total_registros: int
    registros_validos: int
    registros_errores: int
    registros_duplicados: int
    errores: List[str]
    duplicados: List[Dict[str, Any]]
    exitoso: bool


@dataclass
class EvaluacionHojaControl:
    """Resultado estructurado de la evaluación de una hoja de CONTROL_RECORRIDOS."""
    es_valida: bool
    razon: str
    detalle: Optional[str] = None
    fecha: Optional[date] = None
    turno: Optional[str] = None
    tipo: str = 'desconocido'


@dataclass
class WorkbookMetrics:
    total_hojas: int = 0
    hojas_analizadas: int = 0
    hojas_validas: int = 0
    hojas_descartadas: int = 0
    motivos_descarte: Dict[str, int] = None

    def __post_init__(self):
        if self.motivos_descarte is None:
            self.motivos_descarte = {}

    def registrar_descartada(self, motivo: str) -> None:
        self.hojas_descartadas += 1
        self.motivos_descarte[motivo] = self.motivos_descarte.get(motivo, 0) + 1


@dataclass
class RowMetrics:
    total_filas_recorridas: int = 0
    filas_vacias: int = 0
    filas_ocultas: int = 0
    filas_con_error: int = 0
    filas_encabezado: int = 0
    filas_datos: int = 0
    motivos_descarte: Dict[str, int] = None

    def __post_init__(self):
        if self.motivos_descarte is None:
            self.motivos_descarte = {}

    def registrar_descartada(self, motivo: str) -> None:
        self.motivos_descarte[motivo] = self.motivos_descarte.get(motivo, 0) + 1


@dataclass
class ExtractionMetrics:
    objetivos_vacios: int = 0
    supervisores_vacios: int = 0
    horas_vacias: int = 0
    horas_invalidas: int = 0
    turnos_invalidos: int = 0
    registros_creados: int = 0
    registros_descartados: int = 0
    excepciones_parseo: int = 0
    anotaciones_descartadas: int = 0
    motivos_descarte: Dict[str, int] = None

    def __post_init__(self):
        if self.motivos_descarte is None:
            self.motivos_descarte = {}

    def registrar_descartado(self, motivo: str) -> None:
        self.registros_descartados += 1
        self.motivos_descarte[motivo] = self.motivos_descarte.get(motivo, 0) + 1
        if motivo == 'anotacion_supervisor':
            self.anotaciones_descartadas += 1


@dataclass
class ValidationMetrics:
    supervisor_inexistente: int = 0
    objetivo_inexistente: int = 0
    fecha_invalida: int = 0
    hora_invalida: int = 0
    turno_invalido: int = 0
    registros_validos: int = 0
    registros_rechazados: int = 0
    motivos_rechazo: Dict[str, int] = None

    def __post_init__(self):
        if self.motivos_rechazo is None:
            self.motivos_rechazo = {}

    def registrar_rechazo(self, motivo: str) -> None:
        self.registros_rechazados += 1
        self.motivos_rechazo[motivo] = self.motivos_rechazo.get(motivo, 0) + 1


@dataclass
class ImportMetrics:
    workbook: WorkbookMetrics = None
    filas: RowMetrics = None
    extraccion: ExtractionMetrics = None
    validacion: ValidationMetrics = None
    importacion: Dict[str, int] = None

    def __post_init__(self):
        if self.workbook is None:
            self.workbook = WorkbookMetrics()
        if self.filas is None:
            self.filas = RowMetrics()
        if self.extraccion is None:
            self.extraccion = ExtractionMetrics()
        if self.validacion is None:
            self.validacion = ValidationMetrics()
        if self.importacion is None:
            self.importacion = {
                'registros_insertados': 0,
                'registros_duplicados': 0,
                'errores_sql': 0,
                'inserciones_fallidas': 0,
            }

    def reset(self) -> None:
        self.workbook = WorkbookMetrics()
        self.filas = RowMetrics()
        self.extraccion = ExtractionMetrics()
        self.validacion = ValidationMetrics()
        self.importacion = {
            'registros_insertados': 0,
            'registros_duplicados': 0,
            'errores_sql': 0,
            'inserciones_fallidas': 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImportadorUniversal:
    """Sistema unificado para importar datos desde múltiples fuentes."""

    _INSTANCIAS: "weakref.WeakSet[ImportadorUniversal]" = weakref.WeakSet()
    _INSTANCIAS_LOCK = threading.Lock()

    _ALIAS_ENCABEZADOS: Dict[str, Tuple[str, ...]] = {
        'objetivo': ('objetivo', 'objetivos'),
        'supervisor': ('supervisor', 'supervisores'),
        'hora': ('hora', 'horas'),
        'turno': ('turno', 'turnos'),
        'notas': ('nota', 'notas', 'observacion', 'observaciones'),
    }

    _PATRONES_ANOTACION = (
        "ingreso a obra",
        "ingresa a obra",
        "se deja garita",
        "garita nro",
        "garita n°",
        "sale movil",
        "sale móvil",
        "llama supervisor",
        "se retira",
        "se entrega",
        "se recibe",
    )

    # Formato oficial CONTROL_RECORRIDOS: cada fila tiene hasta 3 bloques
    # horizontales, cada uno representando una pasada independiente con
    # columnas NO | OBJETIVO | TURNO | MOVIL | HORA | SUPERVISOR.
    # Cada tupla es (col_objetivo, col_turno, col_hora, col_supervisor),
    # 1-indexed (como usa openpyxl). Único lugar donde se define este mapeo.
    CONTROL_RECORRIDOS_BLOCKS: Tuple[Tuple[int, int, int, int], ...] = (
        (2, 3, 5, 6),     # bloque 1: cols 1-6
        (9, 10, 12, 13),  # bloque 2: cols 8-13
        (16, 17, 19, 20), # bloque 3: cols 15-20
    )

    def __init__(self):
        self.sync_manager = get_sync_manager()

        self._cache_objetivos: Dict[str, int] = {}
        self._cache_supervisores: Dict[str, int] = {}
        self._cache_inicializado = False
        self._metrics = ImportMetrics()
        try:
            with type(self)._INSTANCIAS_LOCK:
                type(self)._INSTANCIAS.add(self)
        except Exception:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("No se pudo registrar instancia en _INSTANCIAS", exc_info=True)

    @classmethod
    def invalidar_cache_global(cls) -> None:
        """Invalida el cache interno de todos los importadores activos."""
        try:
            with cls._INSTANCIAS_LOCK:
                instancias = list(cls._INSTANCIAS)
        except Exception:
            instancias = list(cls._INSTANCIAS)

        for instancia in instancias:
            try:
                instancia.invalidate_cache()
            except Exception as exc:
                logger.warning("No se pudo invalidar cache del importador %s: %s", instancia, exc)

    def _reset_cache_state(self) -> None:
        self._cache_objetivos = {}
        self._cache_supervisores = {}
        self._cache_inicializado = False

    def invalidate_cache(self) -> None:
        self._reset_cache_state()
        logger.info("[CACHE] Cache del importador invalidado")

    def reload_cache(self) -> None:
        self._reset_cache_state()
        self._inicializar_caches()
        logger.info("[CACHE] Cache del importador recargado")

    def _cargar_cache_objetivos(self) -> bool:
        try:
            filas = gestor_db.ejecutar("SELECT id, nombre FROM objetivos")
            for fila in filas:
                key = self._normalizar_texto(fila['nombre'])
                self._cache_objetivos[key] = int(fila['id'])
            logger.info("[CACHE] Cargados %d objetivos", len(self._cache_objetivos))
            return True
        except Exception as e:
            logger.error("No se pudieron cargar objetivos: %s", e)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Cache objetivos traceback", exc_info=True)
            return False

    def _cargar_cache_supervisores(self) -> bool:
        try:
            filas = gestor_db.ejecutar("SELECT id, nombre FROM supervisores")
            for fila in filas:
                key = self._normalizar_texto(fila['nombre'])
                self._cache_supervisores[key] = int(fila['id'])
            logger.info("[CACHE] Cargados %d supervisores", len(self._cache_supervisores))
            return True
        except Exception as e:
            logger.error("No se pudieron cargar supervisores: %s", e)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Cache supervisores traceback", exc_info=True)
            return False

    def _inicializar_caches(self) -> None:
        """Carga los caches si aún no están inicializados o si fueron invalidados.

        Si alguna de las dos cargas falla, el cache NO se marca como
        inicializado, para que el próximo llamado reintente la carga.
        """
        if self._cache_inicializado:
            return

        ok_objetivos = self._cargar_cache_objetivos()
        ok_supervisores = self._cargar_cache_supervisores()

        self._cache_inicializado = ok_objetivos and ok_supervisores

    def previsualizar_archivo(
        self,
        ruta_archivo: str,
        sheet_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Previsualiza un archivo Excel de CONTROL_RECORRIDOS.

        - Extrae TODOS los objetivos y supervisores detectados.
        - Determina cuáles existen en BD (resueltos) y cuáles no.
        - Devuelve además los errores de parseo (bloques con datos parciales
          o inválidos) para mostrarlos al usuario antes de importar.
        """
        try:
            self._metrics.reset()
            self._inicializar_caches()

            try:
                wb_data = load_workbook(ruta_archivo, data_only=True)
            except FileNotFoundError:
                return self._preview_error(f"Archivo no encontrado: {ruta_archivo}")
            except PermissionError:
                return self._preview_error(f"Sin permisos para leer el archivo: {ruta_archivo}")
            except InvalidFileException as e:
                return self._preview_error(f"Archivo inválido o corrupto: {e}")
            except Exception as e:
                logger.error("Error abriendo Excel: %s", e)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Traceback abriendo Excel", exc_info=True)
                return self._preview_error(f"Error leyendo Excel: {str(e)}")

            # Detectar fórmulas sin valor calculado: si una celda quedó en
            # None en la versión data_only pero tiene una fórmula en la
            # versión con fórmulas, avisamos al usuario para que reabra y
            # guarde el archivo en Excel/LibreOffice antes de reintentar.
            try:
                wb_formulas = load_workbook(ruta_archivo, data_only=False)
                problemas = []
                for ws_data, ws_formula in zip(wb_data.worksheets, wb_formulas.worksheets):
                    max_row = min(ws_data.max_row, 40)
                    max_col = min(ws_data.max_column, 20)
                    for r in range(1, max_row + 1):
                        for c in range(1, max_col + 1):
                            val_data = ws_data.cell(row=r, column=c).value
                            val_formula = ws_formula.cell(row=r, column=c).value
                            if (val_data is None or (isinstance(val_data, str) and val_data.strip() == "")) and isinstance(val_formula, str) and val_formula.startswith('='):
                                problemas.append(f"{ws_data.title}:{r}:{c}")
                if problemas:
                    return self._preview_error(
                        'El archivo contiene celdas con fórmulas sin valor calculado. '
                        'Abrilo en Excel/LibreOffice, guardalo y volvé a subirlo. '
                        f'Ejemplos: {problemas[:5]}'
                    )
            except Exception:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug('No se pudo abrir workbook en modo fórmulas para verificar celdas', exc_info=True)

            wb = wb_data
            sheet_options = self._listar_sheet_options(wb)

            if not sheet_options:
                return self._preview_empty()

            control = self._parsear_control_recorridos(wb, sheet_names=sheet_names)
            registros = control.get('registros', [])
            errores_parseo = control.get('errores', [])

            objetivos_detectados = sorted({
                r.objetivo.strip() for r in registros if r.objetivo and str(r.objetivo).strip()
            })
            supervisores_detectados = sorted({
                r.supervisor.strip() for r in registros if r.supervisor and str(r.supervisor).strip()
            })

            objetivos_resueltos = {}
            objetivos_no_resueltos = []
            for nombre in objetivos_detectados:
                objetivo_id = self._obtener_objetivo_id(nombre)
                if objetivo_id is not None:
                    objetivos_resueltos[nombre] = objetivo_id
                else:
                    objetivos_no_resueltos.append(nombre)

            supervisores_resueltos = {}
            supervisores_no_resueltos = []
            for nombre in supervisores_detectados:
                supervisor_id = self._obtener_supervisor_id(nombre)
                if supervisor_id is not None:
                    supervisores_resueltos[nombre] = supervisor_id
                else:
                    supervisores_no_resueltos.append(nombre)

            logger.info("[PREVIEW] Archivo: %s", ruta_archivo)
            logger.info("  Total registros: %d", len(registros))
            logger.info("  Errores de parseo: %d", len(errores_parseo))
            logger.info(
                "  Objetivos: %d (%d resueltos, %d nuevos)",
                len(objetivos_detectados), len(objetivos_resueltos), len(objetivos_no_resueltos),
            )
            logger.info(
                "  Supervisores: %d (%d resueltos, %d nuevos)",
                len(supervisores_detectados), len(supervisores_resueltos), len(supervisores_no_resueltos),
            )

            return {
                'tipo': 'control_recorridos',
                'registros': registros,
                'errores_parseo': errores_parseo,
                'objetivos_detectados': objetivos_detectados,
                'supervisores_detectados': supervisores_detectados,
                'objetivos_resueltos': objetivos_resueltos,
                'supervisores_resueltos': supervisores_resueltos,
                'objetivos_no_resueltos': objetivos_no_resueltos,
                'supervisores_no_resueltos': supervisores_no_resueltos,
                'sheet_options': sheet_options,
            }

        except Exception as e:
            logger.error("Error en previsualizar_archivo: %s", e)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Traceback en previsualizar_archivo", exc_info=True)
            return self._preview_error(str(e))

    @staticmethod
    def _preview_error(mensaje: str) -> Dict[str, Any]:
        return {
            'tipo': 'error',
            'error': mensaje,
            'registros': [],
            'errores_parseo': [],
            'objetivos_detectados': [],
            'supervisores_detectados': [],
            'objetivos_resueltos': {},
            'supervisores_resueltos': {},
            'objetivos_no_resueltos': [],
            'supervisores_no_resueltos': [],
            'sheet_options': [],
        }

    @staticmethod
    def _preview_empty() -> Dict[str, Any]:
        return {
            'tipo': 'empty',
            'registros': [],
            'errores_parseo': [],
            'objetivos_detectados': [],
            'supervisores_detectados': [],
            'objetivos_resueltos': {},
            'supervisores_resueltos': {},
            'objetivos_no_resueltos': [],
            'supervisores_no_resueltos': [],
            'sheet_options': [],
        }

    def importar_excel(self, ruta_archivo: str) -> ResultadoImportacion:
        """Importa datos desde archivo Excel (CONTROL_RECORRIDOS, o la hoja 'Pasadas')."""
        try:
            preview = self.previsualizar_archivo(ruta_archivo)
            if preview.get('tipo') == 'control_recorridos' and len(preview.get('registros', [])) > 0:
                return self.importar_control_recorridos(ruta_archivo, preview_precalculado=preview)

            df = pd.read_excel(ruta_archivo, sheet_name='Pasadas')
            columnas_requeridas = ['Fecha', 'Supervisor', 'Objetivo', 'Hora', 'Turno']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                return ResultadoImportacion(
                    total_registros=0, registros_validos=0, registros_errores=0,
                    registros_duplicados=0,
                    errores=[f"Columnas faltantes: {', '.join(columnas_faltantes)}"],
                    duplicados=[], exitoso=False,
                )

            registros = []
            for index, row in df.iterrows():
                try:
                    registro = RegistroImportacion(
                        fecha=self._formatear_fecha(row['Fecha']),
                        hora=self._formatear_hora(row['Hora']),
                        turno=str(row['Turno']).strip().lower(),
                        supervisor=str(row['Supervisor']).strip(),
                        objetivo=str(row['Objetivo']).strip(),
                        notas=str(row.get('Notas', '')) if pd.notna(row.get('Notas')) else None,
                        fuente='excel',
                    )
                    registros.append(registro)
                except Exception as e:
                    logger.warning("Fila %s de Excel inválida: %s", index, e)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Traceback fila inválida Excel: %s", e, exc_info=True)
                    continue

            return self.importar_registros(registros)

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0, registros_validos=0, registros_errores=0,
                registros_duplicados=0, errores=[f"Error leyendo Excel: {str(e)}"],
                duplicados=[], exitoso=False,
            )

    def importar_control_recorridos(
        self,
        ruta_archivo: str,
        objetivo_mapeo: Optional[Dict[str, int]] = None,
        supervisor_mapeo: Optional[Dict[str, int]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        sheet_names: Optional[List[str]] = None,
        sheet_turno_map: Optional[Dict[str, str]] = None,
        preview_precalculado: Optional[Dict[str, Any]] = None,
    ) -> ResultadoImportacion:
        """Importa CONTROL_RECORRIDOS con auto-resolución de objetivos y supervisores."""

        self._inicializar_caches()

        preview = preview_precalculado if preview_precalculado is not None else self.previsualizar_archivo(
            ruta_archivo, sheet_names=sheet_names,
        )

        if preview.get('tipo') != 'control_recorridos':
            return ResultadoImportacion(
                total_registros=0, registros_validos=0, registros_errores=1,
                registros_duplicados=0,
                errores=[f"Tipo de archivo inválido: {preview.get('tipo')}"],
                duplicados=[], exitoso=False,
            )

        registros = preview.get('registros', [])
        errores_parseo = preview.get('errores_parseo', [])

        if len(registros) == 0 and not errores_parseo:
            return ResultadoImportacion(
                total_registros=0, registros_validos=0, registros_errores=1,
                registros_duplicados=0, errores=['No se encontraron registros válidos'],
                duplicados=[], exitoso=False,
            )

        mapeo_objetivo_final = dict(preview.get('objetivos_resueltos', {}))
        if objetivo_mapeo:
            mapeo_objetivo_final.update(objetivo_mapeo)

        mapeo_supervisor_final = dict(preview.get('supervisores_resueltos', {}))
        if supervisor_mapeo:
            mapeo_supervisor_final.update(supervisor_mapeo)

        logger.info("[IMPORTACIÓN] Mapeos finales:")
        logger.info("  Objetivos mapeados: %d", len(mapeo_objetivo_final))
        for nombre, obj_id in sorted(mapeo_objetivo_final.items()):
            logger.debug("    %s -> ID %s", nombre, obj_id)
        logger.info("  Supervisores mapeados: %d", len(mapeo_supervisor_final))
        for nombre, sup_id in sorted(mapeo_supervisor_final.items()):
            logger.debug("    %s -> ID %s", nombre, sup_id)

        if sheet_turno_map:
            for r in registros:
                mapped = sheet_turno_map.get(r.sheet_title)
                if mapped:
                    r.turno = mapped

        resultado = self.importar_registros(
            registros,
            objetivo_mapeo=mapeo_objetivo_final,
            supervisor_mapeo=mapeo_supervisor_final,
            progress_callback=progress_callback,
        )

        # Los errores de parseo (bloques incompletos/inválidos detectados
        # al leer el Excel) se muestran junto a los errores de validación.
        if errores_parseo:
            resultado.errores = list(errores_parseo) + resultado.errores
            resultado.registros_errores = len(resultado.errores)
            resultado.exitoso = resultado.exitoso and False if resultado.registros_validos == 0 else resultado.exitoso

        return resultado

    def importar_registros(
        self,
        registros: List[RegistroImportacion],
        objetivo_mapeo: Optional[Dict[str, int]] = None,
        supervisor_mapeo: Optional[Dict[str, int]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ResultadoImportacion:
        return self._procesar_registros(
            registros,
            objetivo_mapeo=objetivo_mapeo or {},
            supervisor_mapeo=supervisor_mapeo or {},
            progress_callback=progress_callback,
        )

    def importar_json_tablet(self, ruta_archivo: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> ResultadoImportacion:
        """Importa datos desde archivo JSON de tablet."""
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)

            registros = []
            for index, pasada in enumerate(data.get('pasadas', []), start=1):
                try:
                    timestamp = datetime.fromisoformat(pasada['timestamp'].replace('Z', '+00:00'))
                    registro = RegistroImportacion(
                        fecha=timestamp.strftime('%Y-%m-%d'),
                        hora=timestamp.strftime('%H:%M'),
                        turno=pasada['turno'],
                        supervisor=data['meta']['usuario'],
                        objetivo=pasada['objetivo'],
                        notas=pasada.get('notas'),
                        fuente='tablet',
                    )
                    registros.append(registro)
                except Exception as e:
                    logger.warning("Pasada JSON tablet inválida #%s en %s: %s", index, ruta_archivo, e)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Traceback pasada JSON inválida: %s", e, exc_info=True)
                    continue

            return self.importar_registros(registros, progress_callback=progress_callback)

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0, registros_validos=0, registros_errores=0,
                registros_duplicados=0, errores=[f"Error leyendo JSON: {str(e)}"],
                duplicados=[], exitoso=False,
            )

    def importar_json_string(self, json_string: str) -> ResultadoImportacion:
        """Importa datos desde string JSON (útil para API futuras)."""
        try:
            data = json.loads(json_string)

            tmp_name = None
            try:
                with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False) as tmpf:
                    json.dump(data, tmpf)
                    tmp_name = tmpf.name

                return self.importar_json_tablet(tmp_name)
            finally:
                if tmp_name:
                    try:
                        os.remove(tmp_name)
                    except Exception as e:
                        logger.debug(
                            "No se pudo eliminar archivo temporal %s: %s", tmp_name, e,
                            exc_info=logger.isEnabledFor(logging.DEBUG),
                        )

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0, registros_validos=0, registros_errores=0,
                registros_duplicados=0, errores=[f"Error procesando JSON: {str(e)}"],
                duplicados=[], exitoso=False,
            )

    def filtrar_registros_por_rango(
        self,
        registros: List[RegistroImportacion],
        rango_desde: Optional[Tuple[date, str]] = None,
        rango_hasta: Optional[Tuple[date, str]] = None,
    ) -> List[RegistroImportacion]:
        """Filtra registros por un rango de fechas/turnos inclusive."""
        if rango_desde is None and rango_hasta is None:
            return list(registros)

        def _orden_turno(turno: Optional[str]) -> int:
            turno_norm = str(turno or "").strip().lower()
            if turno_norm in ("n", "noche", "nocturno"):
                return 0
            if turno_norm in ("d", "dia", "diurno"):
                return 1
            return 2

        def _comparar_fecha_turno(
            registro_fecha: str, registro_turno: str,
            limite_fecha, limite_turno: str,
        ) -> int:
            try:
                reg_date = datetime.strptime(registro_fecha, "%Y-%m-%d").date()
            except Exception as e:
                logger.debug(
                    "Comparación fecha/turno inválida: %s | registro_fecha=%s registro_turno=%s limite_fecha=%s limite_turno=%s",
                    e, registro_fecha, registro_turno, limite_fecha, limite_turno,
                )
                return 0

            if isinstance(limite_fecha, str):
                try:
                    lim_date = datetime.strptime(limite_fecha, "%Y-%m-%d").date()
                except Exception as e:
                    logger.debug(
                        "Comparación fecha/turno inválida para limite_fecha: %s | limite_fecha=%s",
                        e, limite_fecha,
                    )
                    return 0
            else:
                lim_date = limite_fecha

            if reg_date < lim_date:
                return -1
            if reg_date > lim_date:
                return 1

            reg_turno = _orden_turno(registro_turno)
            lim_turno = _orden_turno(limite_turno)
            if reg_turno < lim_turno:
                return -1
            if reg_turno > lim_turno:
                return 1
            return 0

        filtrados: List[RegistroImportacion] = []
        for registro in registros:
            incluir = True

            if rango_desde is not None:
                cmp = _comparar_fecha_turno(registro.fecha, registro.turno, rango_desde[0], rango_desde[1])
                if cmp < 0:
                    incluir = False

            if incluir and rango_hasta is not None:
                cmp = _comparar_fecha_turno(registro.fecha, registro.turno, rango_hasta[0], rango_hasta[1])
                if cmp > 0:
                    incluir = False

            if incluir:
                filtrados.append(registro)

        return filtrados

    def _procesar_registros(
        self,
        registros: List[RegistroImportacion],
        objetivo_mapeo: Optional[Dict[str, int]] = None,
        supervisor_mapeo: Optional[Dict[str, int]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ResultadoImportacion:
        """Procesa registros importados con auto-resolución de referencias."""

        total = len(registros)
        validos = 0
        errores = []
        duplicados = []

        objetivo_mapeo = objetivo_mapeo or {}
        supervisor_mapeo = supervisor_mapeo or {}

        objetivo_mapeo_norm: Dict[str, int] = {
            self._normalizar_texto(k): v for k, v in objetivo_mapeo.items() if k is not None
        }
        supervisor_mapeo_norm: Dict[str, int] = {
            self._normalizar_texto(k): v for k, v in supervisor_mapeo.items() if k is not None
        }

        procesados = 0
        abort = False

        self._inicializar_caches()

        # Pre-cargar pasadas existentes en el rango de fechas cubierto por
        # los registros a importar (con un día de margen) para evitar N+1.
        fechas = []
        for r in registros:
            try:
                fechas.append(datetime.strptime(r.fecha, "%Y-%m-%d").date())
            except Exception:
                continue

        pasadas_cache = None
        if fechas:
            min_fecha = min(fechas) - timedelta(days=1)
            max_fecha = max(fechas) + timedelta(days=1)
            try:
                filas = gestor_db.ejecutar(
                    """
                    SELECT fecha, hora, turno, supervisor_id, objetivo_id
                    FROM pasadas
                    WHERE fecha BETWEEN ? AND ?
                    """,
                    (min_fecha.strftime('%Y-%m-%d'), max_fecha.strftime('%Y-%m-%d')),
                )
                pasadas_cache = set()
                for f in filas:
                    fecha_f = f['fecha']
                    hora_f = f.get('hora')
                    turno_f = f.get('turno')
                    sup_id = int(f['supervisor_id']) if f.get('supervisor_id') is not None else None
                    obj_id = int(f['objetivo_id']) if f.get('objetivo_id') is not None else None
                    pasadas_cache.add((fecha_f, hora_f, turno_f, sup_id, obj_id))
                self._pasadas_cache_current_import = pasadas_cache
                logger.info(
                    "[PROCESAMIENTO] Precargadas %d pasadas existentes para rango %s - %s",
                    len(pasadas_cache), min_fecha, max_fecha,
                )
            except Exception as e:
                pasadas_cache = None
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("No se pudo precargar pasadas: %s", e, exc_info=True)

        logger.info("[PROCESAMIENTO] Iniciando con %d registros", total)
        logger.info("  Mapeo objetivos: %d entradas", len(objetivo_mapeo))
        logger.info("  Mapeo supervisores: %d entradas", len(supervisor_mapeo))

        for registro in registros:
            try:
                # 1. Resolver supervisor
                supervisor_id = None
                if registro.supervisor:
                    supervisor_id = supervisor_mapeo_norm.get(self._normalizar_texto(registro.supervisor))
                if supervisor_id is None:
                    supervisor_id = self._obtener_supervisor_id(registro.supervisor)
                if supervisor_id is None:
                    self._metrics.validacion.supervisor_inexistente += 1
                    self._metrics.validacion.registrar_rechazo('supervisor_inexistente')
                    errores.append(f"Supervisor no encontrado: '{registro.supervisor}'")
                    logger.warning(
                        "Registro inválido: supervisor no encontrado: %s | sheet=%s",
                        registro.supervisor, registro.sheet_title,
                    )
                    procesados += 1
                    continue

                # 2. Resolver objetivo
                objetivo_id = None
                if registro.objetivo:
                    objetivo_id = objetivo_mapeo_norm.get(self._normalizar_texto(registro.objetivo))
                if objetivo_id is None:
                    objetivo_id = self._obtener_objetivo_id(registro.objetivo)
                if objetivo_id is None:
                    self._metrics.validacion.objetivo_inexistente += 1
                    self._metrics.validacion.registrar_rechazo('objetivo_inexistente')
                    errores.append(f"Objetivo no encontrado: '{registro.objetivo}'")
                    logger.warning(
                        "Registro inválido: objetivo no encontrado: %s | sheet=%s",
                        registro.objetivo, registro.sheet_title,
                    )
                    procesados += 1
                    continue

                # 3. Validar turno
                turno_normalizado = self._normalizar_turno(registro.turno)
                if turno_normalizado is None:
                    self._metrics.validacion.turno_invalido += 1
                    self._metrics.validacion.registrar_rechazo('turno_invalido')
                    errores.append(f"Turno inválido: '{registro.turno}' (debe ser 'diurno' o 'nocturno')")
                    logger.warning("Registro inválido: turno inválido: %s | sheet=%s", registro.turno, registro.sheet_title)
                    procesados += 1
                    continue

                # 4. Parsear fecha y hora
                try:
                    fecha = datetime.strptime(registro.fecha, "%Y-%m-%d").date()
                    hora = datetime.strptime(registro.hora, "%H:%M").time() if registro.hora else None

                    es_control_recorridos = bool(registro.sheet_title)
                    if es_control_recorridos:
                        fecha_operativa = fecha
                    else:
                        fecha_operativa = GestorTurnos.calcular_fecha_operativa(fecha, hora, turno_normalizado)
                except ValueError as e:
                    self._metrics.validacion.fecha_invalida += 1
                    self._metrics.validacion.hora_invalida += 1
                    self._metrics.validacion.registrar_rechazo('fecha_hora_invalida')
                    errores.append(f"Formato fecha/hora inválido (fecha: {registro.fecha}, hora: {registro.hora}): {e}")
                    logger.warning(
                        "Registro inválido: fecha/hora no parseable: %s | sheet=%s | row_fecha=%s | row_hora=%s",
                        e, registro.sheet_title, registro.fecha, registro.hora,
                    )
                    procesados += 1
                    continue

                # 5. Verificar duplicados
                if self._es_duplicado(
                    supervisor_id, objetivo_id, fecha_operativa.strftime('%Y-%m-%d'), registro.hora, turno_normalizado,
                ):
                    self._metrics.importacion['registros_duplicados'] += 1
                    duplicados.append(registro.to_dict())
                    logger.info(
                        "[DUP] %s %s %s: %s | sheet=%s",
                        fecha_operativa, registro.hora, turno_normalizado, registro.objetivo, registro.sheet_title,
                    )
                    procesados += 1
                    continue

                # 6. Crear pasada
                try:
                    creado = self.sync_manager.crear_pasada_offline(
                        fecha_operativa.strftime('%Y-%m-%d'),
                        registro.hora,
                        turno_normalizado,
                        supervisor_id,
                        objetivo_id,
                        registro.notas,
                        validar_turno=not es_control_recorridos,
                    )
                    if creado:
                        validos += 1
                        self._metrics.validacion.registros_validos += 1
                        self._metrics.importacion['registros_insertados'] += 1
                        logger.info(
                            "Pasada creada: %s %s %s | objetivo=%s | supervisor=%s",
                            fecha_operativa, registro.hora, turno_normalizado, registro.objetivo, registro.supervisor,
                        )
                    else:
                        self._metrics.importacion['inserciones_fallidas'] += 1
                        self._metrics.validacion.registrar_rechazo('insercion_fallida')
                        errores.append(f"No se pudo crear pasada: {registro.supervisor} - {registro.objetivo}")
                        logger.warning("No se pudo crear pasada: %s | sheet=%s", registro.objetivo, registro.sheet_title)
                except Exception as e:
                    self._metrics.importacion['errores_sql'] += 1
                    self._metrics.validacion.registrar_rechazo('error_sql')
                    errores.append(f"Error creando pasada: {str(e)}")
                    logger.error(
                        "Exception al crear pasada: %s | sheet=%s | row_fecha=%s | row_hora=%s",
                        e, registro.sheet_title, registro.fecha, registro.hora,
                    )
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Traceback crear pasada", exc_info=True)

            except Exception as e:
                self._metrics.extraccion.excepciones_parseo += 1
                self._metrics.extraccion.registrar_descartado('excepcion_parseo')
                errores.append(f"Error procesando registro: {str(e)}")
                logger.error(
                    "Exception procesando registro: %s | sheet=%s | registro=%s",
                    e, registro.sheet_title, registro.to_dict(),
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Traceback registro", exc_info=True)

            finally:
                procesados += 1
                try:
                    if progress_callback:
                        progress_callback(procesados, total)
                except Exception as e:
                    errores.append(f"Importación cancelada: {e}")
                    logger.error(
                        "Error en progress_callback: %s | processed=%d total=%d", e, procesados, total,
                    )
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Traceback progress_callback", exc_info=True)
                    abort = True

            if abort:
                break

        try:
            if hasattr(self, '_pasadas_cache_current_import'):
                delattr(self, '_pasadas_cache_current_import')
        except Exception:
            try:
                del self._pasadas_cache_current_import
            except Exception:
                pass

        logger.info("[RESUMEN FINAL]")
        logger.info("[METRICS] %s", self._metrics.to_dict())
        logger.info("  Total: %d", total)
        logger.info("  Válidos: %d", validos)
        logger.info("  Errores: %d", len(errores))
        logger.info("  Duplicados: %d", len(duplicados))

        return ResultadoImportacion(
            total_registros=total,
            registros_validos=validos,
            registros_errores=len(errores),
            registros_duplicados=len(duplicados),
            errores=errores,
            duplicados=duplicados,
            exitoso=(len(errores) == 0 and validos > 0),
        )

    # =========================================================================
    # Parser único de CONTROL_RECORRIDOS
    # =========================================================================

    def _parsear_control_recorridos(
        self,
        workbook_or_path,
        sheet_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Recorre todas las hojas válidas de un workbook y devuelve registros + errores."""

        workbook = load_workbook(workbook_or_path, data_only=True) if isinstance(workbook_or_path, str) else workbook_or_path

        registros: List[RegistroImportacion] = []
        errores: List[str] = []
        sheet_names_set = set(sheet_names) if sheet_names else None
        self._metrics.workbook.total_hojas = len(workbook.worksheets)

        for ws in workbook.worksheets:
            self._metrics.workbook.hojas_analizadas += 1
            try:
                evaluacion = self._evaluar_hoja_control_recorridos(ws, sheet_names_set)
                if not evaluacion.es_valida:
                    self._metrics.workbook.registrar_descartada(evaluacion.razon)
                    logger.info(
                        "Hoja descartada: %s | razon=%s | detalle=%s", ws.title, evaluacion.razon, evaluacion.detalle,
                    )
                    continue

                self._metrics.workbook.hojas_validas += 1
                hoja_registros, hoja_errores = self._parsear_hoja_control_recorridos(
                    ws, evaluacion.fecha or date.today(), evaluacion.turno,
                )
                registros.extend(hoja_registros)
                errores.extend(hoja_errores)

                if not hoja_registros and not hoja_errores:
                    self._metrics.extraccion.registrar_descartado('sin_registros')
                    logger.info("Hoja sin registros: %s", ws.title)

            except Exception as e:
                self._metrics.workbook.registrar_descartada('error_analisis_hoja')
                self._metrics.extraccion.excepciones_parseo += 1
                logger.warning("Error durante el análisis de hoja: sheet=%s | error=%s", ws.title, e)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Traceback hoja inválida: %s", ws.title, exc_info=True)
                continue

        return {'registros': registros, 'errores': errores}

    def _parsear_hoja_control_recorridos(
        self,
        ws,
        sheet_date: date,
        turno_hoja: Optional[str],
    ) -> Tuple[List[RegistroImportacion], List[str]]:
        """Parsea una hoja completa: hasta 3 bloques horizontales por fila."""
        registros: List[RegistroImportacion] = []
        errores: List[str] = []
        filas_procesadas = 0

        for row_idx, fila in enumerate(
            ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True), start=1,
        ):
            self._metrics.filas.total_filas_recorridas += 1

            if ws.row_dimensions[row_idx].hidden:
                self._metrics.filas.filas_ocultas += 1
                self._metrics.filas.registrar_descartada('fila_oculta')
                continue

            if not fila or all(self._limpiar_valor(v) is None for v in fila):
                self._metrics.filas.filas_vacias += 1
                self._metrics.filas.registrar_descartada('fila_vacia')
                continue

            fila_tuvo_datos = False
            for bloque_idx, (c_obj, c_turno, c_hora, c_sup) in enumerate(self.CONTROL_RECORRIDOS_BLOCKS, start=1):
                idx_obj, idx_turno, idx_hora, idx_sup = c_obj - 1, c_turno - 1, c_hora - 1, c_sup - 1
                if len(fila) <= idx_obj:
                    continue

                objetivo_raw = fila[idx_obj] if len(fila) > idx_obj else None
                turno_raw = fila[idx_turno] if len(fila) > idx_turno else None
                hora_raw = fila[idx_hora] if len(fila) > idx_hora else None
                supervisor_raw = fila[idx_sup] if len(fila) > idx_sup else None

                try:
                    registro, error = self._crear_registro_bloque(
                        objetivo_raw=objetivo_raw,
                        turno_raw=turno_raw,
                        hora_raw=hora_raw,
                        supervisor_raw=supervisor_raw,
                        sheet_date=sheet_date,
                        turno_hoja=turno_hoja,
                        ws_title=ws.title,
                    )
                except Exception as e:
                    self._metrics.filas.filas_con_error += 1
                    self._metrics.filas.registrar_descartada('error_parseo_bloque')
                    self._metrics.extraccion.excepciones_parseo += 1
                    errores.append(f"{ws.title} fila {row_idx} bloque {bloque_idx}: error inesperado ({e})")
                    logger.warning(
                        "Error en bloque: %s | sheet=%s | fila=%d | bloque=%d", e, ws.title, row_idx, bloque_idx,
                    )
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Traceback bloque", exc_info=True)
                    continue

                if registro is not None:
                    registros.append(registro)
                    fila_tuvo_datos = True
                    self._metrics.filas.filas_datos += 1
                    self._metrics.extraccion.registros_creados += 1
                elif error is not None:
                    errores.append(f"{ws.title} fila {row_idx} bloque {bloque_idx}: {error}")
                    fila_tuvo_datos = True

            if fila_tuvo_datos:
                filas_procesadas += 1

        logger.info(
            "[PARSE SUMMARY] Hoja: %s | Registros: %d | Errores: %d | Filas procesadas: %d",
            ws.title, len(registros), len(errores), filas_procesadas,
        )
        return registros, errores

    def _crear_registro_bloque(
        self,
        objetivo_raw: Any,
        turno_raw: Any,
        hora_raw: Any,
        supervisor_raw: Any,
        sheet_date: date,
        turno_hoja: Optional[str],
        ws_title: str,
    ) -> Tuple[Optional[RegistroImportacion], Optional[str]]:
        """Construye el registro de un único bloque (Turno | Móvil | Hora | Supervisor).

        Devuelve:
        - (registro, None) si el bloque tiene datos válidos.
        - (None, None) si el bloque está completamente vacío (se ignora, no es error).
        - (None, mensaje) si el bloque tiene datos parciales o inválidos (es un error a reportar).
        """
        objetivo = self._limpiar_valor(objetivo_raw)
        supervisor = self._limpiar_valor(supervisor_raw)
        turno_txt = self._limpiar_valor(turno_raw)

        bloque_vacio = (
            not self._campo_presente(turno_raw)
            and not self._campo_presente(hora_raw)
            and not self._campo_presente(supervisor_raw)
        )
        if bloque_vacio:
            return None, None

        if objetivo and self._es_anotacion_supervisor(objetivo):
            self._metrics.extraccion.registrar_descartado('anotacion_supervisor')
            return None, None

        if objetivo and self._es_encabezado(objetivo):
            self._metrics.filas.filas_encabezado += 1
            self._metrics.filas.registrar_descartada('encabezado')
            return None, None

        # El bloque tiene datos: cualquier campo obligatorio faltante es
        # un error a reportar, no un descarte silencioso.
        faltantes = []
        if not objetivo:
            faltantes.append('objetivo')
            self._metrics.extraccion.objetivos_vacios += 1
        if not supervisor:
            faltantes.append('supervisor')
            self._metrics.extraccion.supervisores_vacios += 1
        if not self._campo_presente(hora_raw):
            faltantes.append('hora')
            self._metrics.extraccion.horas_vacias += 1

        if faltantes:
            self._metrics.extraccion.registrar_descartado('bloque_incompleto')
            return None, f"bloque incompleto, falta {', '.join(faltantes)}"

        # Turno: se toma el de la celda del bloque; si además el nombre de
        # la hoja indica un turno, se usa como validación cruzada.
        turno_bloque = self._normalizar_turno(turno_txt) if turno_txt else None
        if turno_txt and turno_bloque is None:
            self._metrics.extraccion.turnos_invalidos += 1
            self._metrics.extraccion.registrar_descartado('turno_invalido')
            return None, f"turno inválido: '{turno_raw}'"

        if turno_bloque and turno_hoja and turno_bloque != turno_hoja:
            self._metrics.extraccion.turnos_invalidos += 1
            self._metrics.extraccion.registrar_descartado('turno_inconsistente')
            return None, (
                f"turno inconsistente (la hoja indica '{turno_hoja}', "
                f"el bloque indica '{turno_bloque}')"
            )

        turno_final = turno_bloque or turno_hoja
        if turno_final is None:
            self._metrics.extraccion.turnos_invalidos += 1
            self._metrics.extraccion.registrar_descartado('turno_desconocido')
            return None, "no se pudo determinar el turno (ni la hoja ni el bloque lo indican)"

        try:
            fecha_final, hora_normalizada = self._normalizar_hora_y_fecha(hora_raw, sheet_date)
        except Exception as e:
            self._metrics.extraccion.horas_invalidas += 1
            self._metrics.extraccion.registrar_descartado('hora_invalida')
            return None, f"hora inválida: '{hora_raw}' ({e})"

        registro = RegistroImportacion(
            fecha=fecha_final.strftime('%Y-%m-%d'),
            hora=hora_normalizada,
            turno=turno_final,
            supervisor=supervisor,
            objetivo=objetivo,
            notas=None,
            fuente='excel',
            sheet_title=ws_title,
        )
        return registro, None

    def _campo_presente(self, valor: Any) -> bool:
        """True si la celda tiene contenido real (soporta time/datetime de Excel)."""
        if valor is None:
            return False
        if isinstance(valor, (time, datetime)):
            return True
        return self._limpiar_valor(valor) is not None

    def _normalizar_turno(self, valor: Any) -> Optional[str]:
        """Normaliza variantes textuales de turno a 'diurno' o 'nocturno'. None si no se reconoce."""
        if valor is None:
            return None

        texto = str(valor).strip().lower()
        if not texto:
            return None

        diurno_aliases = {'d', 'dia', 'diurno', 'diaria', 'diario', 'day', 'dayshift', 'matutino'}
        nocturno_aliases = {'n', 'noche', 'nocturno', 'night', 'nightshift'}

        if texto in diurno_aliases:
            return 'diurno'
        if texto in nocturno_aliases:
            return 'nocturno'
        return None

    def _es_anotacion_supervisor(self, texto: str) -> bool:
        """Determina si el texto corresponde a una anotación libre del supervisor
        (ej. "SE RETIRA A LAS 22:00") y no a un objetivo válido."""
        if not texto:
            return False

        texto = self._normalizar_texto(texto)

        for patron in self._PATRONES_ANOTACION:
            patron_norm = self._normalizar_texto(patron)
            if texto == patron_norm:
                return True

            if texto.startswith(patron_norm + ' '):
                resto = texto[len(patron_norm):].strip()
                if not resto:
                    return True
                if re.search(r"\d", resto) and len(resto) <= 25:
                    return True

        return False

    def _listar_sheet_options(self, workbook_or_path):
        workbook = load_workbook(workbook_or_path, data_only=True) if isinstance(workbook_or_path, str) else workbook_or_path

        opciones = []
        for ws in workbook.worksheets:
            try:
                evaluacion = self._evaluar_hoja_control_recorridos(ws)
                if not evaluacion.es_valida:
                    logger.debug(
                        'Hoja ignorada en listado: %s | razon=%s | detalle=%s',
                        ws.title, evaluacion.razon, evaluacion.detalle,
                    )
                    continue

                opciones.append({
                    'title': ws.title,
                    'fecha': (evaluacion.fecha or date.today()).isoformat(),
                    'turno': evaluacion.turno,
                })
            except Exception as e:
                logger.warning("Error en hoja al listar opciones: %s | sheet=%s", e, ws.title)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Traceback listar opciones hoja %s", ws.title, exc_info=True)

        return opciones

    def _analizar_nombre_hoja(self, sheet_name: str) -> Dict[str, Any]:
        """Extrae fecha y turno del nombre de la hoja (ej. '01-05 D', '01/05 NOCTURNO')."""
        texto = str(sheet_name).strip().upper()
        if not texto:
            return {'es_valido': False, 'razon': 'nombre inválido', 'fecha': None, 'turno': None}

        match = re.search(r'(\d{1,2})\s*[-/]\s*(\d{1,2})', texto)
        if not match:
            return {'es_valido': False, 'razon': 'sin fecha en el nombre', 'fecha': None, 'turno': None}

        dia = int(match.group(1))
        mes = int(match.group(2))

        turno = None
        if re.search(r'\(D\)|DIURNO|\bD\b', texto):
            turno = 'diurno'
        elif re.search(r'\(N\)|NOCTURNO|\bN\b', texto):
            turno = 'nocturno'

        YEAR_IMPORTACION = date.today().year
        try:
            fecha = date(YEAR_IMPORTACION, mes, dia)
        except ValueError:
            return {'es_valido': False, 'razon': 'fecha inválida', 'fecha': None, 'turno': turno}

        if turno is None:
            return {'es_valido': False, 'razon': 'sin turno en el nombre', 'fecha': fecha, 'turno': None}

        return {'es_valido': True, 'razon': 'nombre con fecha y turno', 'fecha': fecha, 'turno': turno}

    def _evaluar_hoja_control_recorridos(
        self,
        ws,
        sheet_names_set: Optional[Set[str]] = None,
    ) -> EvaluacionHojaControl:
        """Evalúa si una hoja debe procesarse y determina su fecha/turno base.

        Todas las hojas no vacías (y seleccionadas, si corresponde) son
        CONTROL_RECORRIDOS: es el único formato de Excel que soporta este
        parser. El nombre de la hoja se usa únicamente para deducir la
        fecha y, si está disponible, el turno de la jornada (que luego se
        valida contra el turno indicado en cada bloque).
        """
        try:
            title = self._limpiar_valor(ws.title)
            if not title:
                return EvaluacionHojaControl(False, 'nombre inválido', 'la hoja no tiene nombre')

            if sheet_names_set is not None and title not in sheet_names_set:
                return EvaluacionHojaControl(False, 'sheet no seleccionado', 'la hoja no fue solicitada para procesar')

            if self._hoja_esta_vacia(ws):
                return EvaluacionHojaControl(False, 'hoja vacía', 'la hoja no contiene datos')

            nombre_analizado = self._analizar_nombre_hoja(title)
            fecha = nombre_analizado['fecha'] or date.today()
            turno = nombre_analizado['turno']

            return EvaluacionHojaControl(
                True,
                'hoja válida',
                nombre_analizado['razon'],
                fecha=fecha,
                turno=turno,
                tipo='control_recorridos',
            )
        except Exception as exc:
            return EvaluacionHojaControl(False, 'error durante el análisis', str(exc))

    def _hoja_esta_vacia(self, ws) -> bool:
        """Determina si una hoja está vacía o sin datos útiles."""
        try:
            if ws.max_row <= 1 and ws.max_column <= 1:
                return True
            for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 5), values_only=True):
                if any(self._limpiar_valor(valor) is not None for valor in row):
                    return False
            return True
        except Exception:
            return True

    def _normalizar_hora_y_fecha(self, hora_raw: Any, fecha_base: date) -> Tuple[date, str]:
        """
        Normaliza horas provenientes de Excel / Google Sheets / inputs sucios.

        Soporta:
        - 2149 -> 21:49
        - 205 -> 02:05
        - 14 -> 00:14
        - 5 -> 00:05
        - 2149.0 -> 21:49
        - 21:49 / 21;49 / 21.49
        - 03: / 03; -> 03:00
        - :30 / ;30 -> 00:30
        - 26:30 -> día siguiente 02:30
        - datetime.time
        - datetime.datetime
        """
        if isinstance(hora_raw, time):
            return fecha_base, hora_raw.strftime("%H:%M")

        if isinstance(hora_raw, datetime):
            return fecha_base, hora_raw.strftime("%H:%M")

        if hora_raw is None:
            raise ValueError("Hora vacía")

        if isinstance(hora_raw, float):
            texto = str(int(hora_raw)) if hora_raw.is_integer() else str(hora_raw)
        else:
            texto = str(hora_raw)

        texto = texto.strip().lower()
        texto = (
            texto.replace("\u00a0", " ")
                .replace("h", "")
                .replace("hora", "")
                .replace(" ", "")
        )
        texto = texto.replace(";", ":").replace(".", ":")
        texto = re.sub(r":{2,}", ":", texto)

        if texto in ("", "none", "n/a", "na", "null", "-", "--", "cerrado", "closed"):
            raise ValueError("Hora vacía o inválida")

        if re.fullmatch(r":\d{1,2}", texto):
            texto = "0" + texto
        if re.fullmatch(r"\d{1,2}:", texto):
            texto = texto + "00"

        hora = None
        minuto = None

        if re.fullmatch(r"\d{1,2}", texto):
            hora = 0
            minuto = int(texto)
        elif re.fullmatch(r"\d{3,4}", texto):
            if len(texto) == 3:
                hora = int(texto[0])
                minuto = int(texto[1:])
            else:
                hora = int(texto[:2])
                minuto = int(texto[2:])
        elif re.fullmatch(r"\d{1,2}:\d{1,2}", texto):
            hora, minuto = map(int, texto.split(":"))
        elif re.fullmatch(r"\d{1,2}:\d{1,2}:\d{1,2}", texto):
            hora, minuto, _ = map(int, texto.split(":"))
        else:
            raise ValueError(f"Formato de hora no reconocido: '{hora_raw}' (procesado como '{texto}')")

        if minuto < 0 or minuto >= 60:
            raise ValueError(f"Minutos inválidos: {minuto} (entrada: {hora_raw})")
        if hora < 0:
            raise ValueError(f"Hora inválida: {hora} (entrada: {hora_raw})")

        total_minutos = hora * 60 + minuto
        dias = total_minutos // (24 * 60)
        total_minutos = total_minutos % (24 * 60)
        fecha_final = fecha_base + timedelta(days=dias)
        hora_final = f"{total_minutos // 60:02d}:{total_minutos % 60:02d}"

        return fecha_final, hora_final

    def _limpiar_valor(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None

        texto = str(valor)
        texto = texto.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto).strip()
        if texto.lower() in ('none', 'n/a', 'na', 'sin dato', 'sin data'):
            return None
        return texto

    def _identificar_tipo_encabezado(self, texto: Any) -> Optional[str]:
        """Identifica si un valor corresponde a un encabezado conocido (ej. 'Objetivo', 'Supervisor')."""
        if texto is None:
            return None

        limpio = self._limpiar_valor(texto)
        if not limpio:
            return None

        normalizado = self._normalizar_texto(limpio)
        if not normalizado:
            return None

        for tipo, aliases in self._ALIAS_ENCABEZADOS.items():
            for alias in aliases:
                pattern = re.compile(rf"^(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])$")
                if pattern.fullmatch(normalizado):
                    return tipo

        if normalizado in {'objetivo supervisor', 'supervisor objetivo'}:
            return 'encabezado_general'

        return None

    def _es_encabezado(self, texto: str) -> bool:
        return self._identificar_tipo_encabezado(texto) is not None

    def _formatear_fecha(self, fecha) -> str:
        """Convierte diversos formatos de fecha a YYYY-MM-DD (usado por la hoja 'Pasadas')."""
        if isinstance(fecha, str):
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(fecha, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            raise ValueError(f"Formato de fecha no reconocido: {fecha}")

        if isinstance(fecha, (datetime, date)):
            return fecha.strftime('%Y-%m-%d')

        raise ValueError(f"Tipo de fecha no soportado: {type(fecha)}")

    def _formatear_hora(self, hora) -> str:
        _, hora_norm = self._normalizar_hora_y_fecha(hora, date.today())
        return hora_norm

    def _obtener_supervisor_id(self, nombre_supervisor: str) -> Optional[int]:
        """Busca supervisor existente por nombre normalizado (asume cache ya inicializado)."""
        if not nombre_supervisor:
            return None
        nombre = str(nombre_supervisor).strip()
        if not nombre:
            return None
        return self._cache_supervisores.get(self._normalizar_texto(nombre))

    def _obtener_objetivo_id(self, nombre_objetivo: str) -> Optional[int]:
        """Busca objetivo existente por nombre normalizado (asume cache ya inicializado)."""
        if not nombre_objetivo:
            return None
        nombre = str(nombre_objetivo).strip()
        if not nombre:
            return None
        return self._cache_objetivos.get(self._normalizar_texto(nombre))

    def _es_duplicado(self, supervisor_id: int, objetivo_id: int, fecha_operativa: str, hora: str, turno: str) -> bool:
        """Verifica si una pasada ya existe (duplicada)."""
        cache = getattr(self, '_pasadas_cache_current_import', None)
        if cache is not None:
            key = (fecha_operativa, hora, turno, int(supervisor_id), int(objetivo_id))
            return key in cache

        try:
            resultados = gestor_db.ejecutar(
                """
                SELECT 1
                FROM pasadas
                WHERE fecha = ?
                  AND hora = ?
                  AND turno = ?
                  AND supervisor_id = ?
                  AND objetivo_id = ?
                LIMIT 1
                """,
                (fecha_operativa, hora, turno, supervisor_id, objetivo_id),
            )
            return bool(resultados)
        except Exception as e:
            logger.warning("No se pudo verificar duplicado (asumiendo no duplicado): %s", e)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Traceback _es_duplicado", exc_info=True)
            return False

    def _normalizar_texto(self, valor: Any) -> str:
        texto = str(valor).strip().lower()
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join(ch for ch in texto if not unicodedata.combining(ch))
        texto = re.sub(r'[^a-z0-9 ]+', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto


_importador: Optional[ImportadorUniversal] = None


def get_importador() -> ImportadorUniversal:
    """Obtiene el importador universal (inicialización diferida)."""
    global _importador
    if _importador is None:
        _importador = ImportadorUniversal()
    return _importador