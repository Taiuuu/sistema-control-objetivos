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

from database import gestor_db
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

    def previsualizar_archivo(
        self,
        ruta_archivo: str,
        sheet_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Previsualiza un archivo Excel y detecta si es CONTROL_RECORRIDOS.

        NUEVA LÓGICA:
        - NO resuelve automáticamente objetivos
        - NO resuelve automáticamente supervisores
        - Devuelve TODOS los detectados para mapeo manual
        """
        try:

            wb = load_workbook(
                ruta_archivo,
                data_only=True,
            )

            sheet_options = self._listar_sheet_options(wb)

            if not sheet_options:
                return {
                    'tipo': 'legacy',
                    'registros': [],
                    'objetivos_detectados': [],
                    'supervisores_detectados': [],
                    'objetivos_no_resueltos': [],
                    'supervisores_no_resueltos': [],
                    'sheet_options': [],
                }

            control = self._parsear_control_recorridos(
                wb,
                sheet_names=sheet_names,
            )

            registros = control.get('registros', [])

            # =====================================================
            # EXTRAER TODOS LOS OBJETIVOS DETECTADOS
            # =====================================================

            objetivos_detectados = sorted({
                r.objetivo.strip()
                for r in registros
                if r.objetivo and str(r.objetivo).strip()
            })

            # =====================================================
            # EXTRAER TODOS LOS SUPERVISORES DETECTADOS
            # =====================================================

            supervisores_detectados = sorted({
                r.supervisor.strip()
                for r in registros
                if r.supervisor and str(r.supervisor).strip()
            })

            # =====================================================
            # DETERMINAR OBJETIVOS Y SUPERVISORES NO RESUELTOS
            # =====================================================

            objetivos_no_resueltos = [
                nombre
                for nombre in objetivos_detectados
                if self._obtener_objetivo_id(nombre) is None
            ]

            supervisores_no_resueltos = [
                nombre
                for nombre in supervisores_detectados
                if self._obtener_supervisor_id(nombre) is None
            ]

            # =====================================================
            # RESPUESTA FINAL
            # =====================================================

            return {
                'tipo': 'control_recorridos',
                'registros': registros,
                'objetivos_detectados': objetivos_detectados,
                'supervisores_detectados': supervisores_detectados,
                'objetivos_no_resueltos': objetivos_no_resueltos,
                'supervisores_no_resueltos': supervisores_no_resueltos,
                'sheet_options': sheet_options,
            }

        except Exception as e:

            return {
                'tipo': 'legacy',
                'registros': [],
                'objetivos_detectados': [],
                'supervisores_detectados': [],
                'objetivos_no_resueltos': [],
                'supervisores_no_resueltos': [],
                'sheet_options': [],
                'error': str(e),
            }

    def importar_excel(self, ruta_archivo: str) -> ResultadoImportacion:
        """Importa datos desde archivo Excel."""
        try:
            preview = self.previsualizar_archivo(ruta_archivo)
            if preview.get('tipo') == 'control_recorridos':
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
        objetivo_mapeo: Dict[str, int],
        supervisor_mapeo: Dict[str, int],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        sheet_names: Optional[List[str]] = None,
        sheet_turno_map: Optional[Dict[str, str]] = None,
    ) -> ResultadoImportacion:

        preview = self.previsualizar_archivo(
            ruta_archivo,
            sheet_names=sheet_names,
        )

        if preview.get('tipo') != 'control_recorridos':
            return self.importar_excel(ruta_archivo)

        registros = preview.get('registros', [])

        # =====================================================
        # Aplicar turno manual por hoja
        # =====================================================

        if sheet_turno_map:
            for r in registros:

                if (
                    (r.sheet_title and r.turno is None)
                    or
                    (r.turno in (None, ''))
                ):

                    mapped = sheet_turno_map.get(
                        r.sheet_title
                    )

                    if mapped:
                        r.turno = mapped

        return self.importar_registros(
            registros,
            objetivo_mapeo=objetivo_mapeo,
            supervisor_mapeo=supervisor_mapeo,
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

    def _procesar_registros(
        self,
        registros: List[RegistroImportacion],
        objetivo_mapeo: Optional[Dict[str, int]] = None,
        supervisor_mapeo: Optional[Dict[str, int]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ResultadoImportacion:
        """Procesa registros importados."""

        total = len(registros)

        validos = 0

        errores = []

        duplicados = []

        objetivo_mapeo = objetivo_mapeo or {}

        supervisor_mapeo = supervisor_mapeo or {}

        procesados = 0

        abort = False

        for registro in registros:

            try:

                supervisor_id = supervisor_mapeo.get(
                    registro.supervisor
                )

                objetivo_id = objetivo_mapeo.get(
                    registro.objetivo
                )

                if not supervisor_id:

                    errores.append(
                        f"Supervisor sin mapear: "
                        f"{registro.supervisor}"
                    )

                    continue

                if not objetivo_id:

                    errores.append(
                        f"Objetivo sin mapear: "
                        f"{registro.objetivo}"
                    )

                    continue

                if registro.turno not in [
                    'diurno',
                    'nocturno',
                ]:

                    errores.append(
                        f"Turno inválido: "
                        f"{registro.turno}"
                    )

                    continue

                try:

                    fecha = datetime.strptime(
                        registro.fecha,
                        "%Y-%m-%d"
                    ).date()

                    hora = datetime.strptime(
                        registro.hora,
                        "%H:%M"
                    ).time()

                    es_control_recorridos = bool(
                        registro.sheet_title
                    )

                    if es_control_recorridos:

                        fecha_operativa = fecha

                    else:

                        fecha_operativa = (
                            GestorTurnos
                            .calcular_fecha_operativa(
                                fecha,
                                hora,
                                registro.turno,
                            )
                        )

                except ValueError as e:

                    errores.append(
                        f"Error en formato fecha/hora "
                        f"({registro.fecha} "
                        f"{registro.hora}): {e}"
                    )

                    continue

                if self._es_duplicado(
                    supervisor_id,
                    objetivo_id,
                    fecha_operativa.strftime('%Y-%m-%d'),
                    registro.hora,
                    registro.turno,
                ):

                    duplicados.append(
                        registro.to_dict()
                    )

                    continue

                creado = self.sync_manager.crear_pasada_offline(
                    fecha_operativa.strftime('%Y-%m-%d'),
                    registro.hora,
                    registro.turno,
                    supervisor_id,
                    objetivo_id,
                    registro.notas,
                    validar_turno=not es_control_recorridos,
                )

                if creado:

                    validos += 1

                else:

                    errores.append(
                        f"Error creando pasada: "
                        f"{registro.supervisor} - "
                        f"{registro.objetivo}"
                    )

            except Exception as e:

                errores.append(
                    f"Error procesando registro: {str(e)}"
                )

            finally:

                procesados += 1

                try:

                    if progress_callback:

                        progress_callback(
                            procesados,
                            total,
                        )

                except Exception:

                    errores.append(
                        "Importación cancelada por usuario."
                    )

                    abort = True

            if abort:
                break

        return ResultadoImportacion(
            total_registros=total,
            registros_validos=validos,
            registros_errores=len(errores),
            registros_duplicados=len(duplicados),
            errores=errores,
            duplicados=duplicados,
            exitoso=(len(errores) == 0),
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
        """
        Parser principal de CONTROL_RECORRIDOS.
        Usa exclusivamente el formato legacy real
        de 3 bloques horizontales.
        """

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

        for row_idx, fila in enumerate(
            ws.iter_rows(
                min_row=1,
                max_row=ws.max_row,
                values_only=True,
            ),
            start=1,
        ):

            # ======================================================
            # FIX:
            # Ignorar filas ocultas por filtros de Excel
            # ======================================================

            if ws.row_dimensions[row_idx].hidden:
                continue

            # ======================================================
            # FIX:
            # Ignorar filas completamente vacías
            # ======================================================

            if not fila:
                continue

            if all(
                self._limpiar_valor(valor) is None
                for valor in fila
            ):
                continue

            for (c_obj, c_turno, c_hora, c_sup) in self._bloques_control_recorridos():

                idx_obj = c_obj - 1
                idx_turno = c_turno - 1
                idx_hora = c_hora - 1
                idx_sup = c_sup - 1

                if len(fila) <= idx_hora:
                    continue

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

                if (
                    not objetivo
                    or str(objetivo).strip() == ''
                    or hora_raw is None
                    or str(hora_raw).strip() == ''
                ):
                    continue

                if self._es_encabezado(objetivo):
                    continue

                turno_fila = None

                if turno_raw is not None:

                    t = str(turno_raw).strip().upper()

                    if t in ('DIA', 'DIURNO', 'D'):
                        turno_fila = 'diurno'

                    elif t in ('NOCHE', 'NOCTURNO', 'N'):
                        turno_fila = 'nocturno'

                turno_final = turno_fila or turno

                if turno_final is None:
                    continue

                # ======================================================
                # Validar coherencia entre turno fila y turno hoja
                # ======================================================

                if turno_fila is not None:

                    if turno is not None and turno_fila != turno:
                        continue

                # ======================================================
                # Validar formato básico de hora
                # ======================================================

                if isinstance(hora_raw, str):

                    hora_test = hora_raw.strip()

                    if not hora_test:
                        continue

                    if not re.match(
                        r'^\d{1,2}:\d{2}(:\d{2})?$',
                        hora_test
                    ):
                        continue

                try:

                    fecha_import, hora_normalizada = (
                        self._normalizar_hora_y_fecha(
                            hora_raw,
                            sheet_date,
                        )
                    )

                except Exception as e:

                    print(
                        f'[CONTROL SHEET ERROR] '
                        f'Hoja={ws.title} | '
                        f'Fila={row_idx} | '
                        f'Objetivo={objetivo} | '
                        f'Hora={hora_raw} | '
                        f'Error={e}'
                    )

                    continue

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

        return registros

    def _listar_sheet_options(self, workbook_or_path) -> List[Dict[str, Any]]:
        """Devuelve las hojas reconocidas como CONTROL_RECORRIDOS y su metadata."""
        if isinstance(workbook_or_path, str):
            workbook = load_workbook(workbook_or_path, data_only=True)
        else:
            workbook = workbook_or_path

        opciones = []
        for ws in workbook.worksheets:
            sheet_date, turno = self._parsear_nombre_sheet(ws.title)
            if not sheet_date or not turno:
                continue

            opciones.append(
                {
                    'title': ws.title,
                    'fecha': sheet_date.isoformat(),
                    'turno': turno,
                }
            )

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

    def _parsear_nombre_sheet(
        self,
        sheet_name: str
    ) -> Tuple[Optional[date], Optional[str]]:
        """
        Extrae fecha y turno desde nombres tipo:

        11-5 (D)
        11/5 (N)
        11-5(D)
        11-5 DIURNO
        11-5 NOCTURNO
        """

        texto = str(sheet_name).strip().upper()

        match_fecha = re.search(
            r'(\d{1,2})\s*[-/]\s*(\d{1,2})',
            texto,
        )

        if not match_fecha:
            return None, None

        dia = int(match_fecha.group(1))
        mes = int(match_fecha.group(2))

        turno = None

        if any(x in texto for x in ['(D)', ' DIURNO', ' DIA', ' D']):
            turno = 'diurno'

        elif any(x in texto for x in ['(N)', ' NOCTURNO', ' NOCHE', ' N']):
            turno = 'nocturno'

        if turno is None:
            return None, None

        today = date.today()

        candidatos = [
            today.year - 1,
            today.year,
            today.year + 1,
        ]

        mejor = None
        mejor_delta = None

        for year in candidatos:

            try:
                fecha = date(year, mes, dia)

            except ValueError:
                continue

            delta = abs(
                (fecha - today).days
            )

            if mejor is None or delta < mejor_delta:
                mejor = fecha
                mejor_delta = delta

        if mejor is None:
            return None, None

        return mejor, turno

    def _normalizar_hora_y_fecha(self, hora_raw: Any, fecha_base: date) -> Tuple[date, str]:
        """Normaliza horas con formato inválido y soporta horas >= 24. Acepta datetime.time."""
        # openpyxl puede devolver datetime.time directamente
        if isinstance(hora_raw, time):
            return fecha_base, hora_raw.strftime('%H:%M')

        texto = str(hora_raw).strip()
        texto = texto.replace(';', ':').replace(',', '.').replace('h', '').replace('H', '')
        texto = texto.replace(' ', '')

        if texto.lower() in ('none', 'n/a', 'na', ''):
            raise ValueError('Hora vacía')

        if re.fullmatch(r'\d{3,4}', texto):
            if len(texto) == 3:
                hora = int(texto[0])
                minuto = int(texto[1:])
            else:
                hora = int(texto[:2])
                minuto = int(texto[2:])
        elif re.fullmatch(r'\d{1,2}:\d{1,2}:\d{1,2}', texto):
            hora, minuto, _ = [int(part) for part in texto.split(':')]
        elif re.fullmatch(r'\d{1,2}:\d{1,2}', texto):
            hora, minuto = [int(part) for part in texto.split(':')]
        elif re.fullmatch(r'\d{1,2}\.\d{1,2}', texto):
            hora, minuto = [int(part) for part in texto.split('.')]
        elif re.fullmatch(r'\d{1,2}\.\d{1,2}\.\d{1,2}', texto):
            hora, minuto, _ = [int(part) for part in texto.split('.')]
        else:
            raise ValueError(f"Formato de hora no reconocido: {hora_raw}")

        total_minutos = hora * 60 + minuto
        dias_desplazados = total_minutos // (24 * 60)
        total_minutos = total_minutos % (24 * 60)
        fecha_resultado = fecha_base + timedelta(days=dias_desplazados)
        hora_resultado = f"{total_minutos // 60:02d}:{total_minutos % 60:02d}"
        return fecha_resultado, hora_resultado

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
        """Convierte diversos formatos de hora a HH:MM."""
        if isinstance(hora, str):
            for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p']:
                try:
                    return datetime.strptime(hora, fmt).strftime('%H:%M')
                except ValueError:
                    continue

            texto = hora.strip().replace(';', ':').replace('.', ':').replace(' ', '')
            if re.fullmatch(r'\d{3,4}', texto):
                if len(texto) == 3:
                    hora_parse = int(texto[0])
                    minuto_parse = int(texto[1:])
                else:
                    hora_parse = int(texto[:2])
                    minuto_parse = int(texto[2:])
                return f"{hora_parse:02d}:{minuto_parse:02d}"

            raise ValueError(f"Formato de hora no reconocido: {hora}")

        if isinstance(hora, time):
            return hora.strftime('%H:%M')

        raise ValueError(f"Tipo de hora no soportado: {type(hora)}")

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

        if self._cache_supervisores is None:

            self._cache_supervisores = {}

            filas = gestor_db.ejecutar(
                "SELECT id, nombre FROM supervisores"
            )

            for fila in filas:

                key = self._normalizar_texto(
                    fila['nombre']
                )

                self._cache_supervisores[key] = int(
                    fila['id']
                )

        normalized = self._normalizar_texto(nombre)

        return self._cache_supervisores.get(
            normalized
        )

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

        if self._cache_objetivos is None:

            self._cache_objetivos = {}

            filas = gestor_db.ejecutar(
                "SELECT id, nombre FROM objetivos"
            )

            for fila in filas:

                key = self._normalizar_texto(
                    fila['nombre']
                )

                self._cache_objetivos[key] = int(
                    fila['id']
                )

        normalized = self._normalizar_texto(nombre)

        return self._cache_objetivos.get(
            normalized
        )

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


importador = ImportadorUniversal()


def get_importador() -> ImportadorUniversal:
    """Obtiene el importador universal."""
    return importador