"""
Validación y clasificación de problemas detectados durante el
análisis: errores críticos (bloquean), advertencias (no bloquean) y
matching pendiente (bloquea hasta que el usuario decide).

Se implementa en la Fase 9.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from .modelos import PasadaNormalizada, Problema


# Rangos esperados por turno. Se permiten overrides desde `contexto`.
_RANGOS_TURNO_POR_DEFECTO: dict[str, tuple[int, int]] = {
    "mañana": (5, 13),
    "manana": (5, 13),
    "tarde": (13, 21),
    "noche": (21, 29),  # admite horas posteriores a medianoche normalizadas
}


def validar(
    pasadas_normalizadas: list[PasadaNormalizada],
    contexto: dict,
) -> list[Problema]:
    """
    Recorre las pasadas normalizadas y el contexto del análisis y genera
    Problema clasificados en:

    - error_critico:
        * datos parciales inconsistentes
        * objetivo sin nombre
        * hora inválida no corregida
        * turno inválido

    - advertencia:
        * hora normalizada automáticamente
        * posible pasada en tabla incorrecta
        * hora fuera de rango del turno
        * inconsistencia entre turno de celda y turno de hoja
        * ambigüedad móvil-supervisor

    - matching_pendiente:
        * objetivo o supervisor no reconocido / pendiente de confirmar

    El `contexto` se trata de forma tolerante para permitir que las fases
    anteriores evolucionen sin acoplar esta validación a una estructura única.
    """

    problemas: list[Problema] = []

    for pasada in pasadas_normalizadas:
        datos = _como_dict(pasada)

        hoja = _valor(datos, "hoja", "nombre_hoja", "sheet")
        objetivo = _valor(datos, "objetivo", "objetivo_nombre")
        movil = _valor(datos, "movil", "numero_movil", "interno")
        supervisor = _valor(datos, "supervisor", "supervisor_nombre")
        hora = _valor(datos, "hora", "hora_normalizada", "hora_pasada")
        turno = _valor(datos, "turno", "turno_celda")
        turno_hoja = _valor(datos, "turno_hoja", "turno_detectado_hoja")

        # -------------------------------------------------------------
        # ERRORES CRÍTICOS
        # -------------------------------------------------------------

        # Objetivo vacío.
        if _vacio(objetivo):
            problemas.append(
                _problema(
                    categoria="error_critico",
                    tipo="objetivo_sin_nombre",
                    hoja=hoja,
                    objetivo=None,
                    valor=objetivo,
                    motivo="La pasada no tiene un objetivo identificado.",
                    sugerencias=["Completar el nombre del objetivo en el Excel."],
                )
            )

        # Datos parciales: se espera poder reconstruir al menos
        # móvil + hora + supervisor para una pasada completa.
        campos_pasada = {
            "móvil": movil,
            "hora": hora,
            "supervisor": supervisor,
        }
        presentes = [nombre for nombre, valor in campos_pasada.items() if not _vacio(valor)]

        if presentes and len(presentes) != len(campos_pasada):
            faltantes = [
                nombre
                for nombre, valor in campos_pasada.items()
                if _vacio(valor)
            ]
            problemas.append(
                _problema(
                    categoria="error_critico",
                    tipo="datos_parciales_inconsistentes",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor={
                        "presentes": presentes,
                        "faltantes": faltantes,
                    },
                    motivo=(
                        "La fila contiene información parcial que no permite "
                        "reconstruir una pasada completa."
                    ),
                    sugerencias=[
                        "Completar los campos faltantes o eliminar los datos "
                        "incompletos de la fila."
                    ],
                )
            )

        # Hora inválida no corregida.
        estado_hora = _valor(
            datos,
            "estado_hora",
            "hora_estado",
            "resultado_validacion_hora",
        )
        hora_invalida = (
            estado_hora in {"invalida", "inválida", "irreconocible"}
            or datos.get("hora_invalida", False)
            or datos.get("hora_no_corregida", False)
            or _hora_fuera_de_limite(hora)
        )

        if hora_invalida and not datos.get("hora_corregida", False):
            problemas.append(
                _problema(
                    categoria="error_critico",
                    tipo="hora_invalida",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=hora,
                    motivo=(
                        "La hora no puede interpretarse correctamente o excede "
                        "el rango válido sin haber sido corregida."
                    ),
                    sugerencias=[
                        "Corregir la hora a un formato horario válido.",
                        "Verificar que la hora sea menor a 24 si no corresponde "
                        "a una normalización de cruce de medianoche.",
                    ],
                )
            )

        # Turno inválido.
        turno_normalizado = _normalizar_turno(turno)
        turnos_validos = _turnos_validos(contexto)

        if not _vacio(turno) and turno_normalizado not in turnos_validos:
            problemas.append(
                _problema(
                    categoria="error_critico",
                    tipo="turno_invalido",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=turno,
                    motivo="El turno indicado no es reconocido.",
                    sugerencias=[
                        f"Usar uno de los turnos válidos: "
                        f"{', '.join(sorted(turnos_validos))}."
                    ],
                )
            )

        # -------------------------------------------------------------
        # ADVERTENCIAS
        # -------------------------------------------------------------

        # Hora normalizada automáticamente.
        if (
            datos.get("hora_normalizada_automaticamente", False)
            or datos.get("hora_normalizada", False) is True
            or estado_hora in {"normalizada", "corregida"}
        ):
            valor_original = _valor(
                datos,
                "hora_original",
                "hora_cruda",
                "valor_hora_original",
            )
            problemas.append(
                _problema(
                    categoria="advertencia",
                    tipo="hora_normalizada",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=valor_original if valor_original is not None else hora,
                    motivo=(
                        "La hora fue normalizada automáticamente durante el "
                        "procesamiento."
                    ),
                    sugerencias=(
                        [f"Hora interpretada como: {hora}."]
                        if hora is not None
                        else []
                    ),
                )
            )

        # Posible tabla incorrecta.
        if _flag_contexto(
            contexto,
            pasada,
            datos,
            "tabla_incorrecta",
            "posible_tabla_incorrecta",
            "tabla_anterior_vacia",
        ):
            problemas.append(
                _problema(
                    categoria="advertencia",
                    tipo="posible_tabla_incorrecta",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=movil,
                    motivo=(
                        "Se detectaron datos en esta tabla mientras la tabla "
                        "anterior esperada se encuentra vacía."
                    ),
                    sugerencias=[
                        "Revisar si la pasada fue cargada en la tabla correcta."
                    ],
                )
            )

        # Hora fuera del rango esperado para el turno.
        if (
            turno_normalizado in turnos_validos
            and _hora_valida_para_comparar(hora)
            and not hora_invalida
        ):
            rangos = contexto.get(
                "rangos_horarios_turno",
                _RANGOS_TURNO_POR_DEFECTO,
            )
            rango = rangos.get(turno_normalizado)

            if rango and not _hora_en_rango(hora, rango):
                problemas.append(
                    _problema(
                        categoria="advertencia",
                        tipo="hora_fuera_de_rango_turno",
                        hoja=hoja,
                        objetivo=objetivo,
                        valor=hora,
                        motivo=(
                            f"La hora está fuera del rango esperado para el "
                            f"turno '{turno_normalizado}'."
                        ),
                        sugerencias=[
                            f"Rango esperado: {rango[0]:02d}:00 a "
                            f"{rango[1] % 24:02d}:00 aproximadamente."
                        ],
                    )
                )

        # Ambigüedad móvil -> supervisor.
        if (
            datos.get("movil_supervisor_ambiguo", False)
            or _flag_contexto(
                contexto,
                pasada,
                datos,
                "asociacion_movil_supervisor_ambigua",
                "movil_supervisor_ambiguo",
            )
        ):
            sugerencias = _sugerencias_contexto(
                contexto,
                pasada,
                datos,
                "sugerencias_supervisor",
                "supervisores_posibles",
            )
            problemas.append(
                _problema(
                    categoria="advertencia",
                    tipo="movil_supervisor_ambiguo",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=movil,
                    motivo=(
                        "El móvil puede asociarse a más de un supervisor dentro "
                        "de la hoja."
                    ),
                    sugerencias=sugerencias,
                )
            )

        # Turno de celda vs turno inferido del nombre de hoja.
        turno_hoja_normalizado = _normalizar_turno(turno_hoja)
        if (
            turno_normalizado
            and turno_hoja_normalizado
            and turno_normalizado != turno_hoja_normalizado
        ):
            problemas.append(
                _problema(
                    categoria="advertencia",
                    tipo="inconsistencia_turno_celda_hoja",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor={
                        "turno_celda": turno,
                        "turno_hoja": turno_hoja,
                    },
                    motivo=(
                        "El turno indicado en la celda no coincide con el turno "
                        "inferido del nombre de la hoja. Se prioriza el valor "
                        "de la celda."
                    ),
                    sugerencias=[
                        f"Se utilizará el turno de la celda: '{turno}'."
                    ],
                )
            )

        # -------------------------------------------------------------
        # MATCHING PENDIENTE
        # -------------------------------------------------------------

        estado_objetivo = _estado_matching(
            datos,
            contexto,
            pasada,
            "objetivo",
        )
        if estado_objetivo in {"no_reconocido", "pendiente", "aproximado"}:
            problemas.append(
                _problema(
                    categoria="matching_pendiente",
                    tipo="matching_objetivo_pendiente",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=objetivo,
                    motivo=_motivo_matching("objetivo", estado_objetivo),
                    sugerencias=_sugerencias_matching(
                        datos,
                        contexto,
                        pasada,
                        "objetivo",
                    ),
                )
            )

        estado_supervisor = _estado_matching(
            datos,
            contexto,
            pasada,
            "supervisor",
        )
        if estado_supervisor in {"no_reconocido", "pendiente", "aproximado"}:
            problemas.append(
                _problema(
                    categoria="matching_pendiente",
                    tipo="matching_supervisor_pendiente",
                    hoja=hoja,
                    objetivo=objetivo,
                    valor=supervisor,
                    motivo=_motivo_matching("supervisor", estado_supervisor),
                    sugerencias=_sugerencias_matching(
                        datos,
                        contexto,
                        pasada,
                        "supervisor",
                    ),
                )
            )

    return problemas


def _como_dict(objeto: Any) -> dict[str, Any]:
    """Convierte dataclass/dict/objeto simple a diccionario."""
    if isinstance(objeto, dict):
        return objeto

    if is_dataclass(objeto):
        return {
            campo.name: getattr(objeto, campo.name)
            for campo in fields(objeto)
        }

    return vars(objeto)


def _valor(datos: dict[str, Any], *nombres: str) -> Any:
    for nombre in nombres:
        if nombre in datos and datos[nombre] is not None:
            return datos[nombre]
    return None


def _vacio(valor: Any) -> bool:
    return valor is None or (
        isinstance(valor, str) and not valor.strip()
    )


def _normalizar_turno(turno: Any) -> str | None:
    if _vacio(turno):
        return None

    texto = str(turno).strip().lower()
    equivalencias = {
        "m": "mañana",
        "manana": "mañana",
        "mañana": "mañana",
        "morning": "mañana",
        "t": "tarde",
        "tarde": "tarde",
        "afternoon": "tarde",
        "n": "noche",
        "noche": "noche",
        "night": "noche",
    }
    return equivalencias.get(texto, texto)


def _turnos_validos(contexto: dict) -> set[str]:
    turnos = contexto.get("turnos_validos")

    if turnos:
        return {_normalizar_turno(turno) for turno in turnos}

    return {"mañana", "tarde", "noche"}


def _hora_fuera_de_limite(hora: Any) -> bool:
    """
    Detecta horas claramente inválidas.

    Las horas > 24 pueden ser válidas solamente si una fase previa las
    marcó explícitamente como normalizadas/corregidas para representar
    cruce de medianoche.
    """
    if hora is None:
        return False

    if isinstance(hora, (int, float)):
        return hora >= 24 or hora < 0

    if isinstance(hora, str):
        texto = hora.strip()
        if ":" not in texto:
            return True

        try:
            horas, minutos = texto.split(":", 1)
            h = int(horas)
            m = int(minutos)
            return h >= 24 or h < 0 or m < 0 or m >= 60
        except ValueError:
            return True

    return True


def _hora_valida_para_comparar(hora: Any) -> bool:
    if hora is None:
        return False

    if isinstance(hora, (int, float)):
        return hora >= 0

    if isinstance(hora, str):
        try:
            h, m = hora.strip().split(":", 1)
            int(h)
            int(m)
            return True
        except (ValueError, AttributeError):
            return False

    return False


def _hora_decimal(hora: Any) -> float:
    if isinstance(hora, (int, float)):
        return float(hora)

    h, m = str(hora).strip().split(":", 1)
    return int(h) + int(m) / 60


def _hora_en_rango(hora: Any, rango: tuple[int, int]) -> bool:
    valor = _hora_decimal(hora)
    inicio, fin = rango

    if fin > 24:
        if valor < inicio:
            valor += 24
        return inicio <= valor <= fin

    return inicio <= valor <= fin


def _flag_contexto(
    contexto: dict,
    pasada: Any,
    datos: dict[str, Any],
    *nombres: str,
) -> bool:
    """Busca un flag primero en la pasada y luego en contexto."""
    for nombre in nombres:
        if datos.get(nombre) is True:
            return True

        valor = contexto.get(nombre)
        if valor is True:
            return True

        if isinstance(valor, dict):
            if valor.get(id(pasada)) is True:
                return True

    return False


def _sugerencias_contexto(
    contexto: dict,
    pasada: Any,
    datos: dict[str, Any],
    *nombres: str,
) -> list[str]:
    for nombre in nombres:
        valor = datos.get(nombre, contexto.get(nombre))

        if isinstance(valor, (list, tuple, set)):
            return [str(item) for item in valor]

        if isinstance(valor, str):
            return [valor]

    return []


def _estado_matching(
    datos: dict[str, Any],
    contexto: dict,
    pasada: Any,
    entidad: str,
) -> str | None:
    """
    Estados admitidos:
    reconocido | aproximado | pendiente | no_reconocido
    """
    claves = (
        f"matching_{entidad}",
        f"estado_matching_{entidad}",
        f"{entidad}_matching",
        f"{entidad}_estado_matching",
    )

    for clave in claves:
        valor = datos.get(clave)
        if valor is not None:
            return str(valor).strip().lower()

        valor = contexto.get(clave)
        if isinstance(valor, str):
            return valor.strip().lower()

    return None


def _motivo_matching(entidad: str, estado: str) -> str:
    if estado == "aproximado":
        return (
            f"El {entidad} tiene un match aproximado y debe confirmarse "
            "antes de la confirmación final."
        )

    return (
        f"El {entidad} no fue reconocido y requiere una decisión del usuario: "
        "asociar con un registro existente o crear uno nuevo."
    )


def _sugerencias_matching(
    datos: dict[str, Any],
    contexto: dict,
    pasada: Any,
    entidad: str,
) -> list[str]:
    claves = (
        f"sugerencias_{entidad}",
        f"{entidad}_sugerencias",
        f"matches_{entidad}",
        f"{entidad}_candidatos",
    )

    for clave in claves:
        valor = datos.get(clave, contexto.get(clave))

        if isinstance(valor, (list, tuple, set)):
            return [str(item) for item in valor]

        if isinstance(valor, str):
            return [valor]

    return [
        f"Confirmar una asociación existente para el {entidad}.",
        f"Crear el {entidad} si no existe en la base.",
    ]


def _problema(
    *,
    categoria: str,
    tipo: str,
    hoja: Any,
    objetivo: Any,
    valor: Any,
    motivo: str,
    sugerencias: list[str] | None = None,
) -> Problema:
    """
    Centraliza la construcción para garantizar que todos los problemas
    incluyan siempre hoja, objetivo, valor problemático y motivo.

    Se asume que Problema utiliza estos nombres de campos:
    categoria, tipo, hoja, objetivo, valor, motivo, sugerencias.
    """
    return Problema(
        categoria=categoria,
        tipo=tipo,
        hoja=hoja,
        objetivo=objetivo,
        valor=valor,
        motivo=motivo,
        sugerencias=sugerencias or [],
    )