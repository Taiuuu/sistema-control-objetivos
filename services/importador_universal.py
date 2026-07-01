# =============================================================================
# VESP Organizations - Sistema de Importación Universal
# Soporta Excel, JSON (tablets), y preparado para más formatos
# =============================================================================

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable

import pandas as pd
from openpyxl import load_workbook

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
    notas: Optional[str] = None
    fuente: str = "manual"
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


class ImportadorUniversal:
    """Sistema unificado para importar datos desde múltiples fuentes."""

    def __init__(self):
        self.sync_manager = get_sync_manager()

        self._cache_objetivos: Dict[str, int] = {}
        self._cache_supervisores: Dict[str, int] = {}
        self._cache_inicializado = False

    def _inicializar_caches(self) -> None:
        """Inicializa los caches de objetivos y supervisores una sola vez."""
        if self._cache_inicializado:
            return
        
        # Cargar objetivos
        try:
            filas = gestor_db.ejecutar(
                "SELECT id, nombre FROM objetivos"
            )
            for fila in filas:
                key = self._normalizar_texto(fila['nombre'])
                self._cache_objetivos[key] = int(fila['id'])
            print(f"[CACHE] Cargados {len(self._cache_objetivos)} objetivos")
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar objetivos: {e}")

        # Cargar supervisores
        try:
            filas = gestor_db.ejecutar(
                "SELECT id, nombre FROM supervisores"
            )
            for fila in filas:
                key = self._normalizar_texto(fila['nombre'])
                self._cache_supervisores[key] = int(fila['id'])
            print(f"[CACHE] Cargados {len(self._cache_supervisores)} supervisores")
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar supervisores: {e}")
        
        self._cache_inicializado = True

    def previsualizar_archivo(
        self,
        ruta_archivo: str,
        sheet_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Previsualiza un archivo Excel y detecta si es CONTROL_RECORRIDOS.

        NUEVA LÓGICA:
        - Extrae TODOS los objetivos detectados
        - Determina cuáles existen en BD (resueltos) y cuáles no
        - Devuelve mapeos preparados para auto-resolver objetivos existentes
        - El usuario solo ve objetivos NO resueltos que necesitan crear o mapear
        """
        try:
            # Inicializar caches una sola vez
            self._inicializar_caches()
            
            wb = load_workbook(
                ruta_archivo,
                data_only=True,
            )

            sheet_options = self._listar_sheet_options(wb)

            # =====================================================
            # Manejo si no hay hojas válidas
            # =====================================================
            if not sheet_options:
                return {
                    'tipo': 'empty',
                    'registros': [],
                    'objetivos_detectados': [],
                    'supervisores_detectados': [],
                    'objetivos_resueltos': {},  # NUEVO: objetivos que SÍ existen
                    'supervisores_resueltos': {},  # NUEVO: supervisores que SÍ existen
                    'objetivos_no_resueltos': [],
                    'supervisores_no_resueltos': [],
                    'sheet_options': [],
                }

            # =====================================================
            # Parsear hojas CONTROL_RECORRIDOS
            # =====================================================
            control = self._parsear_control_recorridos(
                wb,
                sheet_names=sheet_names,
            )

            registros = control.get('registros', [])

            # =====================================================
            # EXTRAER TODOS LOS OBJETIVOS Y SUPERVISORES DETECTADOS
            # =====================================================
            objetivos_detectados = sorted({
                r.objetivo.strip()
                for r in registros
                if r.objetivo and str(r.objetivo).strip()
            })

            supervisores_detectados = sorted({
                r.supervisor.strip()
                for r in registros
                if r.supervisor and str(r.supervisor).strip()
            })

            # =====================================================
            # CLASIFICAR EN RESUELTOS Y NO RESUELTOS
            # =====================================================
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

            # =====================================================
            # LOG DE RESUMEN
            # =====================================================
            print(f"\n[PREVIEW] Archivo: {ruta_archivo}")
            print(f"  Total registros: {len(registros)}")
            print(f"  Objetivos: {len(objetivos_detectados)} ({len(objetivos_resueltos)} resueltos, {len(objetivos_no_resueltos)} nuevos)")
            print(f"  Supervisores: {len(supervisores_detectados)} ({len(supervisores_resueltos)} resueltos, {len(supervisores_no_resueltos)} nuevos)")

            # =====================================================
            # RESPUESTA FINAL
            # =====================================================
            return {
                'tipo': 'control_recorridos',
                'registros': registros,
                'objetivos_detectados': objetivos_detectados,
                'supervisores_detectados': supervisores_detectados,
                'objetivos_resueltos': objetivos_resueltos,
                'supervisores_resueltos': supervisores_resueltos,
                'objetivos_no_resueltos': objetivos_no_resueltos,
                'supervisores_no_resueltos': supervisores_no_resueltos,
                'sheet_options': sheet_options,
            }

        except Exception as e:
            # =====================================================
            # ERROR EXPLÍCITO
            # =====================================================
            import traceback
            traceback.print_exc()
            print(f"[ERROR PREVIEW] {e}")
            return {
                'tipo': 'error',
                'error': str(e),
                'registros': [],
                'objetivos_detectados': [],
                'supervisores_detectados': [],
                'objetivos_resueltos': {},
                'supervisores_resueltos': {},
                'objetivos_no_resueltos': [],
                'supervisores_no_resueltos': [],
                'sheet_options': [],
            }
    
    def importar_excel(self, ruta_archivo: str) -> ResultadoImportacion:
        """Importa datos desde archivo Excel."""
        try:
            preview = self.previsualizar_archivo(ruta_archivo)
            if preview.get('tipo') == 'control_recorridos' and len(preview.get('registros', [])) > 0:
                return self.importar_registros(preview['registros'])

            df = pd.read_excel(ruta_archivo, sheet_name='Pasadas')
            columnas_requeridas = ['Fecha', 'Supervisor', 'Objetivo', 'Hora', 'Turno']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                return ResultadoImportacion(
                    total_registros=0,
                    registros_validos=0,
                    registros_errores=0,
                    registros_duplicados=0,
                    errores=[f"Columnas faltantes: {', '.join(columnas_faltantes)}"],
                    duplicados=[],
                    exitoso=False,
                )

            registros = []
            for _, row in df.iterrows():
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
                except Exception:
                    continue

            return self.importar_registros(registros)

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=0,
                registros_duplicados=0,
                errores=[f"Error leyendo Excel: {str(e)}"],
                duplicados=[],
                exitoso=False,
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
        """
        Importa CONTROL_RECORRIDOS con auto-resolución de objetivos y supervisores.
        
        Si objetivo_mapeo o supervisor_mapeo es None, auto-resuelve los que existen en BD.
        Si preview_precalculado se proporciona, lo reutiliza (evita doble parseo).
        """
        
        # Inicializar caches
        self._inicializar_caches()
        
        # Usar preview precalculado si está disponible
        if preview_precalculado is not None:
            preview = preview_precalculado
        else:
            preview = self.previsualizar_archivo(
                ruta_archivo,
                sheet_names=sheet_names,
            )

        if preview.get('tipo') != 'control_recorridos':
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=1,
                registros_duplicados=0,
                errores=[f"Tipo de archivo inválido: {preview.get('tipo')}"],
                duplicados=[],
                exitoso=False,
            )

        registros = preview.get('registros', [])
        if len(registros) == 0:
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=1,
                registros_duplicados=0,
                errores=['No se encontraron registros válidos'],
                duplicados=[],
                exitoso=False,
            )

        # ================================================================
        # AUTO-RESOLVER OBJETIVOS Y SUPERVISORES QUE EXISTEN EN BD
        # ================================================================
        
        # Mapeo final que combina auto-resueltos + custom mapeos
        mapeo_objetivo_final = dict(preview.get('objetivos_resueltos', {}))
        if objetivo_mapeo:
            mapeo_objetivo_final.update(objetivo_mapeo)

        mapeo_supervisor_final = dict(preview.get('supervisores_resueltos', {}))
        if supervisor_mapeo:
            mapeo_supervisor_final.update(supervisor_mapeo)

        # ================================================================
        # LOG DE MAPEOS
        # ================================================================
        print(f"\n[IMPORTACIÓN] Mapeos finales:")
        print(f"  Objetivos mapeados: {len(mapeo_objetivo_final)}")
        for nombre, obj_id in sorted(mapeo_objetivo_final.items()):
            print(f"    {nombre} -> ID {obj_id}")
        print(f"  Supervisores mapeados: {len(mapeo_supervisor_final)}")
        for nombre, sup_id in sorted(mapeo_supervisor_final.items()):
            print(f"    {nombre} -> ID {sup_id}")

        # Aplicar mapeo de turnos por sheet si es necesario
        if sheet_turno_map:
            for r in registros:
                mapped = sheet_turno_map.get(r.sheet_title)
                if mapped:
                    r.turno = mapped

        return self.importar_registros(
            registros,
            objetivo_mapeo=mapeo_objetivo_final,
            supervisor_mapeo=mapeo_supervisor_final,
            progress_callback=progress_callback,
        )

    def importar_registros(
        self,
        registros: List[RegistroImportacion],
        objetivo_mapeo: Optional[Dict[str, int]] = None,
        supervisor_mapeo: Optional[Dict[str, int]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ResultadoImportacion:
        """Procesa una lista de registros ya normalizados."""

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
            for pasada in data.get('pasadas', []):
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
                except Exception:
                    continue

            return self.importar_registros(registros, progress_callback=progress_callback)

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=0,
                registros_duplicados=0,
                errores=[f"Error leyendo JSON: {str(e)}"],
                duplicados=[],
                exitoso=False,
            )

    def importar_json_string(self, json_string: str) -> ResultadoImportacion:
        """Importa datos desde string JSON (útil para API futuras)."""
        try:
            data = json.loads(json_string)
            temp_file = f"temp_import_{int(datetime.now().timestamp())}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            resultado = self.importar_json_tablet(temp_file)

            try:
                os.remove(temp_file)
            except Exception:
                pass

            return resultado

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=0,
                registros_duplicados=0,
                errores=[f"Error procesando JSON: {str(e)}"],
                duplicados=[],
                exitoso=False,
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
            registro_fecha: str,
            registro_turno: str,
            limite_fecha: date,
            limite_turno: str,
        ) -> int:
            try:
                reg_date = datetime.strptime(registro_fecha, "%Y-%m-%d").date()
            except Exception:
                return 0

            if reg_date < limite_fecha:
                return -1
            if reg_date > limite_fecha:
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
                cmp = _comparar_fecha_turno(
                    registro.fecha,
                    registro.turno,
                    rango_desde[0],
                    rango_desde[1],
                )
                if cmp < 0:
                    incluir = False

            if incluir and rango_hasta is not None:
                cmp = _comparar_fecha_turno(
                    registro.fecha,
                    registro.turno,
                    rango_hasta[0],
                    rango_hasta[1],
                )
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

        procesados = 0
        abort = False

        # Inicializar caches para búsquedas adicionales
        self._inicializar_caches()

        print(f"\n[PROCESAMIENTO] Iniciando con {total} registros")
        print(f"  Mapeo objetivos: {len(objetivo_mapeo)} entradas")
        print(f"  Mapeo supervisores: {len(supervisor_mapeo)} entradas")

        for registro in registros:
            try:
                # ============================================================
                # 1. RESOLVER SUPERVISOR
                # ============================================================
                supervisor_id = supervisor_mapeo.get(registro.supervisor)
                
                if not supervisor_id:
                    # Intentar resolver por caché
                    supervisor_id = self._obtener_supervisor_id(registro.supervisor)

                if not supervisor_id:
                    errores.append(
                        f"Supervisor no encontrado: '{registro.supervisor}'"
                    )
                    print(f"  [ERROR] Supervisor: {registro.supervisor}")
                    procesados += 1
                    continue

                # ============================================================
                # 2. RESOLVER OBJETIVO
                # ============================================================
                objetivo_id = objetivo_mapeo.get(registro.objetivo)
                
                if not objetivo_id:
                    # Intentar resolver por caché
                    objetivo_id = self._obtener_objetivo_id(registro.objetivo)

                if not objetivo_id:
                    errores.append(
                        f"Objetivo no encontrado: '{registro.objetivo}'"
                    )
                    print(f"  [ERROR] Objetivo: {registro.objetivo}")
                    procesados += 1
                    continue

                # ============================================================
                # 3. VALIDAR TURNO
                # ============================================================
                turno_normalizado = str(registro.turno).strip().lower()
                if turno_normalizado not in ['diurno', 'nocturno', 'd', 'n']:
                    errores.append(
                        f"Turno inválido: '{registro.turno}' "
                        f"(debe ser 'diurno' o 'nocturno')"
                    )
                    print(f"  [ERROR] Turno inválido: {turno_normalizado}")
                    procesados += 1
                    continue

                # Normalizar turno
                if turno_normalizado in ('d', 'dia', 'diurno'):
                    turno_normalizado = 'diurno'
                elif turno_normalizado in ('n', 'noche', 'nocturno'):
                    turno_normalizado = 'nocturno'

                # ============================================================
                # 4. PARSEAR FECHA Y HORA
                # ============================================================
                try:
                    fecha = datetime.strptime(
                        registro.fecha,
                        "%Y-%m-%d"
                    ).date()

                    hora = datetime.strptime(
                        registro.hora,
                        "%H:%M"
                    ).time()

                    es_control_recorridos = bool(registro.sheet_title)

                    if es_control_recorridos:
                        fecha_operativa = fecha
                    else:
                        fecha_operativa = (
                            GestorTurnos
                            .calcular_fecha_operativa(
                                fecha,
                                hora,
                                turno_normalizado,
                            )
                        )

                except ValueError as e:
                    errores.append(
                        f"Formato fecha/hora inválido "
                        f"(fecha: {registro.fecha}, hora: {registro.hora}): {e}"
                    )
                    print(f"  [ERROR] Fecha/hora: {e}")
                    procesados += 1
                    continue

                # ============================================================
                # 5. VERIFICAR DUPLICADOS
                # ============================================================
                if self._es_duplicado(
                    supervisor_id,
                    objetivo_id,
                    fecha_operativa.strftime('%Y-%m-%d'),
                    registro.hora,
                    turno_normalizado,
                ):
                    duplicados.append(registro.to_dict())
                    print(f"  [DUP] {fecha_operativa} {registro.hora} "
                          f"{turno_normalizado}: {registro.objetivo}")
                    procesados += 1
                    continue

                # ============================================================
                # 6. CREAR PASADA
                # ============================================================
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
                        print(f"  [OK] {fecha_operativa} {registro.hora}: "
                              f"{registro.objetivo}")
                    else:
                        errores.append(
                            f"No se pudo crear pasada: "
                            f"{registro.supervisor} - {registro.objetivo}"
                        )
                        print(f"  [ERROR] No se creó pasada")

                except Exception as e:
                    errores.append(
                        f"Error creando pasada: {str(e)}"
                    )
                    print(f"  [ERROR] Excepción: {e}")

            except Exception as e:
                errores.append(
                    f"Error procesando registro: {str(e)}"
                )
                print(f"  [ERROR] Excepción general: {e}")

            finally:
                procesados += 1

                try:
                    if progress_callback:
                        progress_callback(procesados, total)
                except Exception as e:
                    errores.append(
                        f"Importación cancelada: {e}"
                    )
                    abort = True

            if abort:
                break

        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print(f"\n[RESUMEN FINAL]")
        print(f"  Total: {total}")
        print(f"  Válidos: {validos}")
        print(f"  Errores: {len(errores)}")
        print(f"  Duplicados: {len(duplicados)}")

        return ResultadoImportacion(
            total_registros=total,
            registros_validos=validos,
            registros_errores=len(errores),
            registros_duplicados=len(duplicados),
            errores=errores,
            duplicados=duplicados,
            exitoso=(len(errores) == 0 and validos > 0),
        )

    def _parsear_control_recorridos(
        self,
        workbook_or_path,
        sheet_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Parsea un workbook CONTROL_RECORRIDOS y devuelve registros normalizados."""

        if isinstance(workbook_or_path, str):
            workbook = load_workbook(workbook_or_path, data_only=True)
        else:
            workbook = workbook_or_path

        registros = []

        sheet_names_set = (
            set(sheet_names)
            if sheet_names
            else None
        )

        for ws in workbook.worksheets:

            try:
                sheet_date, turno = self._parsear_nombre_sheet(
                    ws.title
                )

                if (
                    (not sheet_date or turno is None)
                    and
                    not re.search(
                        r'control',
                        ws.title,
                        re.IGNORECASE,
                    )
                ):
                    continue

                if not sheet_date:
                    sheet_date = date.today()

                if (
                    sheet_names_set is not None
                    and ws.title not in sheet_names_set
                ):
                    continue

                hoja_registros = (
                    self._parsear_hoja_control_recorridos(
                        ws,
                        sheet_date,
                        turno,
                    )
                )

                if not hoja_registros:
                    continue

                registros.extend(hoja_registros)

            except Exception:
                continue

        return {
            'tipo': 'control_recorridos',
            'registros': registros,
            'objetivos_no_resueltos': [],
            'supervisores_no_resueltos': [],
        }

    def _parsear_hoja_control_recorridos(
        self,
        ws,
        sheet_date: date,
        turno: str
    ) -> List[RegistroImportacion]:
        """Parser principal de CONTROL_RECORRIDOS.

        Soporta el formato legacy de 3 bloques horizontales y, si la hoja
        tiene encabezados tipo Objetivo/Supervisor/Hora, también el formato
        tabular simple.
        """

        header_row, columnas = self._buscar_encabezados_control(ws)
        if header_row is not None and columnas:
            return self._parsear_con_encabezados_control(
                ws,
                sheet_date,
                turno,
                columnas,
                header_row,
            )

        return self._parsear_control_recorridos_legacy(
            ws,
            sheet_date,
            turno,
        )

    def _buscar_encabezados_control(self, ws) -> Tuple[Optional[int], Dict[str, Optional[int]]]:
        """Busca la fila de encabezado más probable en la hoja."""
        max_col = ws.max_column
        max_row = min(ws.max_row, 40)
        mejor_fila = None
        mejor_columnas = {}
        mejor_score = 0

        for fila in range(1, max_row + 1):
            columnas = {
                'objetivo': None,
                'supervisor': None,
                'hora': None,
                'veces': None,
                'notas': None,
            }

            for columna in range(1, max_col + 1):
                valor = self._limpiar_valor(ws.cell(row=fila, column=columna).value)
                if not valor:
                    continue

                normalizado = self._normalizar_texto(valor)
                if 'objetivo' in normalizado and columnas['objetivo'] is None:
                    columnas['objetivo'] = columna
                elif 'supervisor' in normalizado and columnas['supervisor'] is None:
                    columnas['supervisor'] = columna
                elif 'hora' in normalizado and columnas['hora'] is None:
                    columnas['hora'] = columna
                elif ('veces' in normalizado or 'cantidad' in normalizado) and columnas['veces'] is None:
                    columnas['veces'] = columna
                elif ('nota' in normalizado or 'observacion' in normalizado) and columnas['notas'] is None:
                    columnas['notas'] = columna

            score = sum(1 for valor in columnas.values() if valor is not None)
            if score > mejor_score and columnas['objetivo'] is not None and columnas['hora'] is not None:
                mejor_score = score
                mejor_fila = fila
                mejor_columnas = columnas

        if mejor_fila is None or mejor_columnas['objetivo'] is None or mejor_columnas['hora'] is None:
            return None, {}

        return mejor_fila, mejor_columnas

    def _parsear_con_encabezados_control(
        self,
        ws,
        sheet_date: date,
        turno: str,
        columnas: Dict[str, Optional[int]],
        header_row: int,
    ) -> List[RegistroImportacion]:
        registros = []
        max_row = ws.max_row

        for fila in range(header_row + 1, max_row + 1):
            objetivo = self._limpiar_valor(ws.cell(row=fila, column=columnas['objetivo']).value)
            if not objetivo or self._es_encabezado(objetivo):
                continue

            hora_raw = self._limpiar_valor(ws.cell(row=fila, column=columnas['hora']).value)
            if not hora_raw:
                continue

            supervisor = self._limpiar_valor(
                ws.cell(row=fila, column=columnas['supervisor']).value
            ) if columnas['supervisor'] is not None else ''
            notas = self._limpiar_valor(
                ws.cell(row=fila, column=columnas['notas']).value
            ) if columnas['notas'] is not None else None
            veces_raw = self._limpiar_valor(
                ws.cell(row=fila, column=columnas['veces']).value
            ) if columnas['veces'] is not None else None

            repeticiones = self._parsear_repeticiones(veces_raw)
            if repeticiones <= 0:
                repeticiones = 1

            try:
                fecha_import, hora_normalizada = self._normalizar_hora_y_fecha(hora_raw, sheet_date)
            except Exception:
                continue

            for _ in range(repeticiones):
                registros.append(
                    RegistroImportacion(
                        fecha=fecha_import.strftime('%Y-%m-%d'),
                        hora=hora_normalizada,
                        turno=turno,
                        supervisor=supervisor or '',
                        objetivo=objetivo,
                        notas=notas,
                        fuente='excel',
                        sheet_title=ws.title,
                    )
                )

        return registros

    def _es_fila_encabezado_global_control_recorridos(self, fila) -> bool:
        """Detecta filas iniciales que contienen títulos generales o cabeceras del formato CONTROL_RECORRIDOS."""
        for valor in fila:
            texto = self._limpiar_valor(valor)
            if not texto:
                continue

            normalizado = self._normalizar_texto(texto)
            if any(keyword in normalizado for keyword in ('control', 'fecha', 'objetivo', 'turno', 'movil', 'supervisor')):
                return True

        return False
    
    def _parsear_control_recorridos_legacy(
        self,
        ws,
        sheet_date: date,
        turno: str
    ) -> List[RegistroImportacion]:
        """
        Parsea el formato CONTROL_RECORRIDOS real con 3 bloques horizontales.

        Cada bloque representa una pasada adicional al mismo objetivo.

        Estructura por bloque:
        NO | OBJETIVO | TURNO | MOVIL | HORA | SUPERVISOR

        Bloques:
        - cols 1-6   -> primera pasada
        - cols 8-13  -> segunda pasada
        - cols 15-20 -> tercera pasada

        Reglas:
        - El turno REAL válido es el de la hoja.
        - Si la fila tiene turno explícito y no coincide con la hoja:
        se ignora.
        - Si la fila no tiene turno:
        se usa el turno de la hoja como fallback.
        """

        import re

        registros = []
        filas_procesadas = 0
        filas_salidas = 0
        filas_con_error = 0

        for row_idx, fila in enumerate(
            ws.iter_rows(
                min_row=1,
                max_row=ws.max_row,
                values_only=True,
            ),
            start=1,
        ):

            # ======================================================
            # FIX: Ignorar filas ocultas por filtros de Excel
            # ======================================================

            if ws.row_dimensions[row_idx].hidden:
                filas_salidas += 1
                continue

            # ======================================================
            # FIX: Ignorar filas completamente vacías
            # ======================================================

            if not fila:
                filas_salidas += 1
                continue

            if all(
                self._limpiar_valor(valor) is None
                for valor in fila
            ):
                filas_salidas += 1
                continue

            # Procesar cada bloque en la fila
            for bloque_idx, (c_obj, c_turno, c_hora, c_sup) in enumerate(self._bloques_control_recorridos()):

                idx_obj = c_obj - 1
                idx_turno = c_turno - 1
                idx_hora = c_hora - 1
                idx_sup = c_sup - 1

                # Saltar si la fila no tiene suficientes columnas
                if len(fila) <= idx_hora:
                    continue

                try:
                    objetivo = self._limpiar_valor(fila[idx_obj])
                    turno_raw = (
                        fila[idx_turno]
                        if len(fila) > idx_turno
                        else None
                    )
                    hora_raw = fila[idx_hora]
                    supervisor = (
                        self._limpiar_valor(fila[idx_sup])
                        if len(fila) > idx_sup
                        else None
                    )

                    # Validaciones básicas
                    if (
                        not objetivo
                        or str(objetivo).strip() == ''
                        or hora_raw is None
                        or str(hora_raw).strip() == ''
                    ):
                        continue

                    if self._es_encabezado(objetivo):
                        continue

                    # Resolver turno
                    turno_fila = None

                    if turno_raw is not None:
                        t = str(turno_raw).strip().upper()

                        if t in ('DIA', 'DIURNO', 'D'):
                            turno_fila = 'diurno'

                        elif t in ('NOCHE', 'NOCTURNO', 'N'):
                            turno_fila = 'nocturno'

                    turno_final = turno_fila or turno

                    if turno_final is None:
                        filas_con_error += 1
                        continue

                    # Validar coherencia entre turno fila y turno hoja
                    if turno_fila is not None and turno is not None and turno_fila != turno:
                        continue

                    # Normalizar hora y fecha
                    try:
                        fecha_import, hora_normalizada = (
                            self._normalizar_hora_y_fecha(
                                hora_raw,
                                sheet_date,
                            )
                        )
                    except Exception as e:
                        print(
                            f'[PARSE ERROR] '
                            f'Hoja={ws.title} | '
                            f'Fila={row_idx} | '
                            f'Bloque={bloque_idx+1} | '
                            f'Objetivo={objetivo} | '
                            f'Hora={hora_raw} | '
                            f'Error: {e}'
                        )
                        filas_con_error += 1
                        continue

                    # Crear registro
                    registros.append(
                        RegistroImportacion(
                            fecha=fecha_import.strftime('%Y-%m-%d'),
                            hora=hora_normalizada,
                            turno=turno_final,
                            supervisor=supervisor or '',
                            objetivo=objetivo,
                            notas=None,
                            fuente='excel',
                            sheet_title=ws.title,
                        )
                    )
                    filas_procesadas += 1

                except Exception as e:
                    print(f'[BLOQUE ERROR] Hoja={ws.title}, Fila={row_idx}, Bloque={bloque_idx+1}: {e}')
                    filas_con_error += 1

        # Log resumen
        print(f"[PARSE SUMMARY] Hoja: {ws.title} | "
              f"Registros: {len(registros)} | "
              f"Filas procesadas: {filas_procesadas} | "
              f"Filas salidas: {filas_salidas} | "
              f"Filas con error: {filas_con_error}")

        return registros

    def _listar_sheet_options(self, workbook_or_path):
        print('\n====================')
        print('DEBUG LISTAR SHEETS')
        print('====================')

        if isinstance(workbook_or_path, str):

            print(f'Abriendo workbook: {workbook_or_path}')

            workbook = load_workbook(
                workbook_or_path,
                data_only=True,
            )

        else:

            workbook = workbook_or_path

        print(f'Total hojas: {len(workbook.worksheets)}')

        opciones = []

        for ws in workbook.worksheets:

            print('--------------------')
            print(f'HOJA RAW: {repr(ws.title)}')

            try:

                sheet_date, turno = self._parsear_nombre_sheet(
                    ws.title
                )

                print(f'PARSE RESULT -> fecha={sheet_date} turno={turno}')

                if not sheet_date or not turno:

                    print('IGNORADA')
                    continue

                opciones.append(
                    {
                        'title': ws.title,
                        'fecha': sheet_date.isoformat(),
                        'turno': turno,
                    }
                )

                print('ACEPTADA')

            except Exception as e:

                print(f'ERROR EN HOJA: {e}')

                import traceback
                traceback.print_exc()

        print('\nRESULTADO FINAL:')
        print(opciones)

        return opciones

    def _bloques_control_recorridos(self) -> List[Tuple[int, int, int, int]]:
        """
        Define los bloques de columnas del formato CONTROL_RECORRIDOS real.
        Cada bloque tiene: NO | OBJETIVO | TURNO | MOVIL | HORA | SUPERVISOR
        Retorna tuplas (col_objetivo, col_turno, col_hora, col_supervisor) — 1-indexed.
        Bloque 1: cols 1-6, Bloque 2: cols 8-13, Bloque 3: cols 15-20.
        """
        return [
            (2, 3, 5, 6),    # bloque 1: cols 1-6
            (9, 10, 12, 13), # bloque 2: cols 8-13
            (16, 17, 19, 20), # bloque 3: cols 15-20
        ]

    def _parsear_nombre_sheet(self, sheet_name: str):
        """
        Extrae fecha y turno desde nombres tipo:

        01-05 D
        01/05 N
        01-05 (D)
        01-05 DIURNO
        01-05 NOCTURNO

        IMPORTANTE:
        Todas las hojas CONTROL_RECORRIDOS pertenecen
        al año operativo actual configurado por la aplicación.

        No intenta adivinar años.
        """

        import re
        from datetime import date

        texto = str(sheet_name).strip().upper()

        match = re.search(
            r'(\d{1,2})\s*[-/]\s*(\d{1,2})',
            texto
        )

        if not match:
            return None, None

        dia = int(match.group(1))
        mes = int(match.group(2))

        turno = None

        if re.search(r'\(D\)|DIURNO|\bD\b', texto):
            turno = 'diurno'

        elif re.search(r'\(N\)|NOCTURNO|\bN\b', texto):
            turno = 'nocturno'

        if turno is None:
            return None, None

        # =====================================================
        # AÑO FIJO
        # =====================================================

        YEAR_IMPORTACION = 2026

        try:
            fecha = date(
                YEAR_IMPORTACION,
                mes,
                dia
            )
        except ValueError:
            return None, None

        return fecha, turno

    def _normalizar_hora_y_fecha(
        self,
        hora_raw: Any,
        fecha_base: date
    ) -> Tuple[date, str]:
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

        from datetime import timedelta, time
        import re

        # =========================
        # 1. TIME directo
        # =========================
        if isinstance(hora_raw, time):
            return fecha_base, hora_raw.strftime("%H:%M")
        
        # =========================
        # 2. DATETIME directo
        # =========================
        if isinstance(hora_raw, datetime):
            return fecha_base, hora_raw.strftime("%H:%M")

        # =========================
        # 3. Normalizar a string base
        # =========================
        if hora_raw is None:
            raise ValueError("Hora vacía")

        if isinstance(hora_raw, float):
            if hora_raw.is_integer():
                texto = str(int(hora_raw))
            else:
                texto = str(hora_raw)
        else:
            texto = str(hora_raw)

        # =========================
        # 4. Limpieza fuerte
        # =========================
        texto = texto.strip().lower()

        texto = (
            texto.replace("\u00a0", " ")
                .replace("h", "")
                .replace("hora", "")
                .replace(" ", "")
        )

        # Unificar separadores raros
        texto = texto.replace(";", ":").replace(".", ":")

        # =========================
        # 5. Casos vacíos
        # =========================
        if texto in ("", "none", "n/a", "na", "null", "-", "--"):
            raise ValueError("Hora vacía o inválida")

        # =========================
        # 6. Normalizaciones especiales
        # =========================

        # ":30" o "30:" o ";30"
        if re.fullmatch(r":\d{1,2}", texto):
            texto = "0" + texto

        if re.fullmatch(r"\d{1,2}:", texto):
            texto = texto + "00"

        # =========================
        # 7. Parsing
        # =========================
        hora = None
        minuto = None

        # SOLO MINUTOS: "12"
        if re.fullmatch(r"\d{1,2}", texto):
            hora = 0
            minuto = int(texto)

        # HHMM: 2149 / 205
        elif re.fullmatch(r"\d{3,4}", texto):
            if len(texto) == 3:
                hora = int(texto[0])
                minuto = int(texto[1:])
            else:
                hora = int(texto[:2])
                minuto = int(texto[2:])

        # HH:MM
        elif re.fullmatch(r"\d{1,2}:\d{1,2}", texto):
            hora, minuto = map(int, texto.split(":"))

        else:
            raise ValueError(f"Formato de hora no reconocido: '{hora_raw}' (procesado como '{texto}')")

        # =========================
        # 8. Validaciones
        # =========================
        if minuto < 0 or minuto >= 60:
            raise ValueError(f"Minutos inválidos: {minuto} (entrada: {hora_raw})")

        if hora < 0:
            raise ValueError(f"Hora inválida: {hora} (entrada: {hora_raw})")

        # =========================
        # 9. Overflow (26:30 -> día siguiente 02:30)
        # =========================
        total_minutos = hora * 60 + minuto

        dias = total_minutos // (24 * 60)
        total_minutos = total_minutos % (24 * 60)

        fecha_final = fecha_base + timedelta(days=dias)

        hora_final = f"{total_minutos // 60:02d}:{total_minutos % 60:02d}"

        return fecha_final, hora_final

    def _parsear_repeticiones(self, valor: Any) -> int:
        texto = self._limpiar_valor(valor)
        if not texto:
            return 1

        try:
            if isinstance(valor, (int, float)):
                return int(valor)
            if re.fullmatch(r'\d+', texto):
                return int(texto)
            if re.fullmatch(r'\d+[.,]\d+', texto):
                return int(float(texto.replace(',', '.')))
        except Exception:
            pass

        return 1

    def _limpiar_valor(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None

        texto = str(valor)
        texto = texto.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto).strip()
        if texto.lower() in ('none', 'n/a', 'na', 'sin dato', 'sin data'):
            return None

        return texto

    def _es_encabezado(self, texto: str) -> bool:
        lower = texto.lower()
        return any(keyword in lower for keyword in ('objetivo', 'supervisor', 'hora', 'turno', 'veces', 'cantidad', 'fecha'))

    def _formatear_fecha(self, fecha) -> str:
        """Convierte diversos formatos de fecha a YYYY-MM-DD."""
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
        fecha_dummy, hora_norm = self._normalizar_hora_y_fecha(
            hora,
            date.today()
        )
        return hora_norm

    def _obtener_supervisor_id(
        self,
        nombre_supervisor: str,
    ) -> Optional[int]:
        """Busca supervisor existente por nombre normalizado."""

        if not nombre_supervisor:
            return None

        nombre = str(nombre_supervisor).strip()

        if not nombre:
            return None

        # Asegurar que los caches estén inicializados
        if not self._cache_inicializado:
            self._inicializar_caches()

        normalized = self._normalizar_texto(nombre)
        return self._cache_supervisores.get(normalized)
    
    def _obtener_objetivo_id(
        self,
        nombre_objetivo: str
    ) -> Optional[int]:
        """Busca objetivo existente por nombre normalizado."""

        if not nombre_objetivo:
            return None

        nombre = str(nombre_objetivo).strip()

        if not nombre:
            return None

        # Asegurar que los caches estén inicializados
        if not self._cache_inicializado:
            self._inicializar_caches()

        normalized = self._normalizar_texto(nombre)
        return self._cache_objetivos.get(normalized)
    
    def _es_duplicado(self, supervisor_id: int, objetivo_id: int, fecha_operativa: str, hora: str, turno: str) -> bool:
        """Verifica si una pasada ya existe (duplicada)."""
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