# =============================================================================
# VESP Organizations - Sistema de Importación Universal
# Soporta Excel, JSON (tablets), y preparado para más formatos
# =============================================================================

import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date, time
import os
from services.sync_manager import get_sync_manager
from services.gestor_turnos import calcular_fecha_operativa


@dataclass
class RegistroImportacion:
    """Representa un registro a importar."""
    fecha: str
    hora: str
    turno: str
    supervisor: str
    objetivo: str
    notas: Optional[str] = None
    fuente: str = "manual"  # 'excel', 'tablet', 'manual'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fecha': self.fecha,
            'hora': self.hora,
            'turno': self.turno,
            'supervisor': self.supervisor,
            'objetivo': self.objetivo,
            'notas': self.notas,
            'fuente': self.fuente
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

    def importar_excel(self, ruta_archivo: str) -> ResultadoImportacion:
        """Importa datos desde archivo Excel."""
        try:
            # Leer Excel
            df = pd.read_excel(ruta_archivo, sheet_name='Pasadas')

            # Validar columnas requeridas
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
                    exitoso=False
                )

            # Convertir a registros
            registros = []
            for _, row in df.iterrows():
                try:
                    registro = RegistroImportacion(
                        fecha=self._formatear_fecha(row['Fecha']),
                        hora=self._formatear_hora(row['Hora']),
                        turno=str(row['Turno']).lower(),
                        supervisor=str(row['Supervisor']).strip(),
                        objetivo=str(row['Objetivo']).strip(),
                        notas=str(row.get('Notas', '')) if pd.notna(row.get('Notas')) else None,
                        fuente='excel'
                    )
                    registros.append(registro)
                except Exception as e:
                    continue  # Saltar registros con error de formato

            # Procesar importación
            return self._procesar_registros(registros)

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=0,
                registros_duplicados=0,
                errores=[f"Error leyendo Excel: {str(e)}"],
                duplicados=[],
                exitoso=False
            )

    def importar_json_tablet(self, ruta_archivo: str) -> ResultadoImportacion:
        """Importa datos desde archivo JSON de tablet."""
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)

            registros = []
            for pasada in data.get('pasadas', []):
                try:
                    # Convertir timestamp a fecha y hora
                    timestamp = datetime.fromisoformat(pasada['timestamp'].replace('Z', '+00:00'))
                    fecha_str = timestamp.strftime('%Y-%m-%d')
                    hora_str = timestamp.strftime('%H:%M')

                    registro = RegistroImportacion(
                        fecha=fecha_str,
                        hora=hora_str,
                        turno=pasada['turno'],
                        supervisor=data['meta']['usuario'],  # Del meta del JSON
                        objetivo=pasada['objetivo'],
                        notas=pasada.get('notas'),
                        fuente='tablet'
                    )
                    registros.append(registro)
                except Exception as e:
                    continue  # Saltar registros con error

            return self._procesar_registros(registros)

        except Exception as e:
            return ResultadoImportacion(
                total_registros=0,
                registros_validos=0,
                registros_errores=0,
                registros_duplicados=0,
                errores=[f"Error leyendo JSON: {str(e)}"],
                duplicados=[],
                exitoso=False
            )

    def importar_json_string(self, json_string: str) -> ResultadoImportacion:
        """Importa datos desde string JSON (útil para API futuras)."""
        try:
            data = json.loads(json_string)
            # Guardar temporalmente y usar método existente
            temp_file = f"temp_import_{int(datetime.now().timestamp())}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            resultado = self.importar_json_tablet(temp_file)

            # Limpiar archivo temporal
            try:
                os.remove(temp_file)
            except:
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
                exitoso=False
            )

    def _procesar_registros(self, registros: List[RegistroImportacion]) -> ResultadoImportacion:
        """Procesa una lista de registros y los importa."""
        total = len(registros)
        validos = 0
        errores = []
        duplicados = []

        for registro in registros:
            try:
                # Validar y obtener IDs
                supervisor_id = self._obtener_supervisor_id(registro.supervisor)
                objetivo_id = self._obtener_objetivo_id(registro.objetivo)

                if not supervisor_id:
                    errores.append(f"Supervisor no encontrado: {registro.supervisor}")
                    continue

                if not objetivo_id:
                    errores.append(f"Objetivo no encontrado: {registro.objetivo}")
                    continue

                # Validar turno
                if registro.turno not in ['diurno', 'nocturno']:
                    errores.append(f"Turno inválido: {registro.turno}")
                    continue

                # Calcular fecha operativa
                fecha_operativa = calcular_fecha_operativa(registro.fecha, registro.hora, registro.turno)

                # Verificar duplicado
                if self._es_duplicado(supervisor_id, objetivo_id, fecha_operativa, registro.hora, registro.turno):
                    duplicados.append(registro.to_dict())
                    continue

                # Crear pasada usando sync manager (soporta offline)
                if self.sync_manager.crear_pasada_offline(
                    registro.fecha, registro.hora, registro.turno,
                    supervisor_id, objetivo_id, registro.notas
                ):
                    validos += 1
                else:
                    errores.append(f"Error creando pasada: {registro.supervisor} - {registro.objetivo}")

            except Exception as e:
                errores.append(f"Error procesando registro: {str(e)}")

        return ResultadoImportacion(
            total_registros=total,
            registros_validos=validos,
            registros_errores=len(errores),
            registros_duplicados=len(duplicados),
            errores=errores,
            duplicados=duplicados,
            exitoso=len(errores) == 0
        )

    def _formatear_fecha(self, fecha) -> str:
        """Convierte diversos formatos de fecha a YYYY-MM-DD."""
        if isinstance(fecha, str):
            # Intentar parsear diferentes formatos
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(fecha, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            raise ValueError(f"Formato de fecha no reconocido: {fecha}")
        elif isinstance(fecha, (datetime, date)):
            return fecha.strftime('%Y-%m-%d')
        else:
            raise ValueError(f"Tipo de fecha no soportado: {type(fecha)}")

    def _formatear_hora(self, hora) -> str:
        """Convierte diversos formatos de hora a HH:MM."""
        if isinstance(hora, str):
            # Intentar parsear diferentes formatos
            for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p']:
                try:
                    return datetime.strptime(hora, fmt).strftime('%H:%M')
                except ValueError:
                    continue
            raise ValueError(f"Formato de hora no reconocido: {hora}")
        elif isinstance(hora, time):
            return hora.strftime('%H:%M')
        else:
            raise ValueError(f"Tipo de hora no soportado: {type(hora)}")

    def _obtener_supervisor_id(self, nombre_supervisor: str) -> Optional[int]:
        """Obtiene el ID de un supervisor por nombre."""
        # TODO: Implementar búsqueda en base de datos
        # Por ahora devolver None para simular
        return None

    def _obtener_objetivo_id(self, nombre_objetivo: str) -> Optional[int]:
        """Obtiene el ID de un objetivo por nombre."""
        # TODO: Implementar búsqueda en base de datos
        # Por ahora devolver None para simular
        return None

    def _es_duplicado(self, supervisor_id: int, objetivo_id: int,
                     fecha_operativa: str, hora: str, turno: str) -> bool:
        """Verifica si una pasada ya existe (duplicada)."""
        # TODO: Implementar verificación de duplicados
        return False


# Instancia global del importador
importador = ImportadorUniversal()


def get_importador() -> ImportadorUniversal:
    """Obtiene el importador universal."""
    return importador</content>
<parameter name="filePath">c:\Vesp taiu\sistema-control-objetivos\services\importador_universal.py