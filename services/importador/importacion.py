"""
Confirmación e importación transaccional a la base de datos,
con registro de auditoría.

FASE 13:
    - validación de estado;
    - creación de objetivos/supervisores;
    - inserción de pasadas;
    - actualización de pasadas;
    - omisión de duplicados;
    - transacción única;
    - rollback completo.

FASE 14:
    - auditoría de correcciones;
    - auditoría de altas;
    - auditoría de sobrescrituras;
    - auditoría del resumen de importación;
    - retención de históricos durante 10 días;
    - sin purga automática.

IMPORTANTE:
    Este módulo NO guarda una copia del Excel original.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from .modelos import (
    PasadaNormalizada,
    Problema,
    ResultadoAnalisis,
    ResultadoMatchObjetivo,
    ResultadoMatchSupervisor,
)
from .matcher import normalizar_nombre


# ============================================================================
# CONSTANTES
# ============================================================================

DIAS_RETENCION_HISTORICO = 10
logger = logging.getLogger(__name__)


# ============================================================================
# UTILIDADES
# ============================================================================


def _valor_sql(valor: Any) -> Any:
    """Convierte tipos Python a valores compatibles con SQLite."""

    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.isoformat(sep=" ")

    if isinstance(valor, date):
        return valor.isoformat()

    if isinstance(valor, time):
        return valor.strftime("%H:%M:%S")

    return valor


def _serializar(valor: Any) -> str:
    """
    Serializa un valor para guardarlo en las columnas TEXT de auditoria.
    """

    if valor is None:
        return ""

    if isinstance(valor, (dict, list, tuple)):
        try:
            return json.dumps(
                valor,
                ensure_ascii=False,
                default=str,
            )
        except Exception:
            return str(valor)

    return str(valor)


def _nombre_usuario(usuario) -> str:
    """Obtiene el nombre identificable del usuario."""

    if usuario is None:
        return ""

    if isinstance(usuario, str):
        return usuario

    if hasattr(usuario, "username"):
        return str(usuario.username)

    if hasattr(usuario, "nombre"):
        return str(usuario.nombre)

    if hasattr(usuario, "id"):
        return str(usuario.id)

    return str(usuario)


def _usuario_id(conexion_bd, usuario) -> int | None:
    """
    Resuelve el ID del usuario de la tabla usuarios.

    Acepta:
        - ID entero;
        - objeto con .id;
        - string username;
        - objeto con .username.
    """

    if usuario is None:
        return None

    if isinstance(usuario, int):
        return usuario

    if hasattr(usuario, "id"):
        return getattr(usuario, "id")

    username = (
        usuario
        if isinstance(usuario, str)
        else getattr(usuario, "username", None)
    )

    if not username:
        return None

    fila = conexion_bd.execute(
        """
        SELECT id
        FROM usuarios
        WHERE username = ?
        LIMIT 1
        """,
        (username,),
    ).fetchone()

    return fila[0] if fila else None


def _fecha_hora_actual() -> tuple[str, str]:
    ahora = datetime.now()

    return (
        ahora.date().isoformat(),
        ahora.strftime("%H:%M:%S"),
    )


# ============================================================================
# AUDITORÍA — FASE 14
# ============================================================================


def registrar_auditoria(
    evento: dict,
    conexion_bd,
) -> None:
    """
    Registra un evento en la tabla `auditoria`.

    IMPORTANTE:
        Esta función NO hace commit.

    Si la importación está dentro de una transacción y este INSERT
    falla, la excepción sube a confirmar_importacion_completa(),
    que ejecutará rollback de toda la operación.

    Eventos soportados:

        - CORRECCION_DURANTE_IMPORTACION
        - ALTA_DESDE_IMPORTACION
        - SOBRESCRITURA_DURANTE_IMPORTACION
        - IMPORTACION_COMPLETA
    """

    if conexion_bd is None:
        raise ValueError(
            "No se puede registrar auditoría sin conexión a BD."
        )

    fecha, hora = _fecha_hora_actual()

    usuario = evento.get("usuario")

    usuario_id = evento.get("usuario_id")

    if usuario_id is None:
        usuario_id = _usuario_id(
            conexion_bd,
            usuario,
        )

    tipo_operacion = evento.get(
        "tipo_operacion",
        "IMPORTACION",
    )

    tabla = evento.get("tabla")

    registro_id = evento.get("registro_id")

    valores_anteriores = evento.get(
        "valores_anteriores",
        {},
    )

    valores_nuevos = evento.get(
        "valores_nuevos",
        {},
    )

    detalles = evento.get(
        "detalles",
        "",
    )

    estado = evento.get(
        "estado",
        "EXITOSO",
    )

    conexion_bd.execute(
        """
        INSERT INTO auditoria (
            fecha,
            hora,
            usuario_id,
            tipo_operacion,
            tabla,
            registro_id,
            valores_anteriores,
            valores_nuevos,
            detalles,
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fecha,
            hora,
            usuario_id,
            tipo_operacion,
            tabla,
            registro_id,
            _serializar(valores_anteriores),
            _serializar(valores_nuevos),
            _serializar(detalles),
            estado,
        ),
    )


# ============================================================================
# RETENCIÓN DE HISTÓRICOS
# ============================================================================


def _fecha_purga_historico() -> str:
    """
    Devuelve la fecha a partir de la cual un histórico de sobrescritura
    puede ser purgado.

    Fase 14 NO realiza la purga.
    """

    fecha = datetime.now() + timedelta(
        days=DIAS_RETENCION_HISTORICO
    )

    return fecha.isoformat(
        sep=" ",
        timespec="seconds",
    )


def _detalles_historico(
    detalles: str | None = None,
) -> dict:
    """
    Construye metadatos de retención.

    La tabla auditoria no tiene una columna `fecha_purga`, por lo que
    se almacena dentro de `detalles`.

    Esto permite que una futura Fase de purga consulte ese valor.
    """

    return {
        "retencion": {
            "dias": DIAS_RETENCION_HISTORICO,
            "fecha_purga_disponible": _fecha_purga_historico(),
            "purga_automatica": False,
        },
        "detalle": detalles or "",
    }


# ============================================================================
# VALIDACIONES
# ============================================================================


def _validar_analisis(
    analisis: ResultadoAnalisis,
    resoluciones,
) -> None:
    """
    Defensa contra estados inconsistentes antes de escribir.
    """

    if analisis is None:
        raise ValueError(
            "No se recibió un ResultadoAnalisis."
        )

    if resoluciones is None:
        raise ValueError(
            "No se recibió el estado de resoluciones."
        )

    problemas = analisis.problemas or []

    errores_criticos = [
        (i, p)
        for i, p in enumerate(problemas)
        if p.tipo == "error_critico"
    ]

    if errores_criticos:
        detalles = "; ".join(
            f"[{i}] {p.descripcion}"
            for i, p in errores_criticos[:5]
        )

        raise ValueError(
            "No se puede importar porque quedan errores críticos "
            f"sin resolver: {detalles}"
        )

    problemas_bloqueantes = [
        i
        for i, p in enumerate(problemas)
        if p.tipo == "para_revisar"
    ]

    pendientes = resoluciones.pendientes_bloqueantes(
        problemas_bloqueantes
    )

    if pendientes:
        detalles = "; ".join(
            f"[{i}] {problemas[i].descripcion}"
            for i in pendientes[:5]
        )

        raise ValueError(
            "No se puede importar porque quedan problemas de "
            f"matching sin resolver: {detalles}"
        )


# ============================================================================
# BÚSQUEDA DE OBJETIVOS
# ============================================================================


def _buscar_objetivo_por_nombre(
    conexion_bd,
    nombre: str,
):
    return conexion_bd.execute(
        """
        SELECT id, nombre
        FROM objetivos
        WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
        """,
        (nombre,),
    ).fetchone()


def _buscar_supervisor_por_nombre(
    conexion_bd,
    nombre: str,
):
    return conexion_bd.execute(
        """
        SELECT id, nombre
        FROM supervisores
        WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
        """,
        (nombre,),
    ).fetchone()


# ============================================================================
# CREACIÓN DE OBJETIVO
# ============================================================================


def _crear_objetivo(
    conexion_bd,
    nombre: str,
    usuario,
    fecha_inicio: date | None = None,
) -> int:

    nombre = (nombre or "").strip()

    if not nombre:
        raise ValueError(
            "No se puede crear un objetivo sin nombre."
        )

    existente = _buscar_objetivo_por_nombre(
        conexion_bd,
        nombre,
    )

    if existente:
        return existente[0]

    fecha_inicio_sql = (
        fecha_inicio.isoformat()
        if isinstance(fecha_inicio, date)
        else None
    )

    cursor = conexion_bd.execute(
        """
        INSERT INTO objetivos (
            nombre,
            descripcion,
            fecha_inicio,
            fecha_fin,
            dias_semana,
            activo
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            "",
            fecha_inicio_sql,
            None,
            None,
            1,
        ),
    )

    objetivo_id = cursor.lastrowid

    # --------------------------------------------------------------
    # FASE 14 — Alta desde importación
    # --------------------------------------------------------------

    registrar_auditoria(
        {
            "usuario": usuario,
            "tipo_operacion": "ALTA_DESDE_IMPORTACION",
            "tabla": "objetivos",
            "registro_id": objetivo_id,
            "valores_anteriores": None,
            "valores_nuevos": {
                "id": objetivo_id,
                "nombre": nombre,
                "descripcion": "",
                "fecha_inicio": fecha_inicio_sql,
                "fecha_fin": None,
                "dias_semana": None,
                "activo": 1,
            },
            "detalles": {
                "accion": "Alta desde importación",
                "entidad": "objetivo",
            },
        },
        conexion_bd,
    )

    return objetivo_id


def _crear_alias_objetivo(conexion_bd, nombre_alias: str, objetivo_id: int) -> None:
    alias_limpio = " ".join((nombre_alias or "").strip().split())
    clave = normalizar_nombre(alias_limpio)
    if not clave:
        raise ValueError("No se puede crear un alias de objetivo vacío.")
    existente = conexion_bd.execute(
        "SELECT objetivo_id FROM objetivos_aliases WHERE nombre_alias_normalizado = ?",
        (clave,),
    ).fetchone()
    if existente:
        if existente[0] != objetivo_id:
            raise ValueError(f"El alias '{alias_limpio}' ya pertenece a otro objetivo.")
        return
    conexion_bd.execute(
        "INSERT INTO objetivos_aliases (objetivo_id, nombre_alias, nombre_alias_normalizado) VALUES (?, ?, ?)",
        (objetivo_id, alias_limpio, clave),
    )


# ============================================================================
# CREACIÓN DE SUPERVISOR
# ============================================================================


def _crear_supervisor(
    conexion_bd,
    nombre: str,
    usuario,
) -> int:

    nombre = (nombre or "").strip()

    if not nombre:
        raise ValueError(
            "No se puede crear un supervisor sin nombre."
        )

    existente = _buscar_supervisor_por_nombre(
        conexion_bd,
        nombre,
    )

    if existente:
        return existente[0]

    fecha_alta, _ = _fecha_hora_actual()

    cursor = conexion_bd.execute(
        """
        INSERT INTO supervisores (
            nombre,
            fecha_alta,
            fecha_baja
        )
        VALUES (?, ?, ?)
        """,
        (
            nombre,
            fecha_alta,
            None,
        ),
    )

    supervisor_id = cursor.lastrowid

    # --------------------------------------------------------------
    # FASE 14 — Alta desde importación
    # --------------------------------------------------------------

    registrar_auditoria(
        {
            "usuario": usuario,
            "tipo_operacion": "ALTA_DESDE_IMPORTACION",
            "tabla": "supervisores",
            "registro_id": supervisor_id,
            "valores_anteriores": None,
            "valores_nuevos": {
                "id": supervisor_id,
                "nombre": nombre,
                "fecha_alta": fecha_alta,
                "fecha_baja": None,
            },
            "detalles": {
                "accion": "Alta desde importación",
                "entidad": "supervisor",
            },
        },
        conexion_bd,
    )

    return supervisor_id


# ============================================================================
# MATCHING
# ============================================================================


def _es_matching_objetivo(
    problema: Problema,
) -> bool:

    return isinstance(
        problema.valor_problema,
        ResultadoMatchObjetivo,
    )


def _es_matching_supervisor(
    problema: Problema,
) -> bool:

    return isinstance(
        problema.valor_problema,
        ResultadoMatchSupervisor,
    )


def _resolver_nombre_match(
    conexion_bd,
    problema: Problema,
    registro,
    usuario,
) -> tuple[str, int]:

    nombre_elegido = (
        registro.valor_despues or ""
    ).strip()

    if nombre_elegido.startswith("(nuevo)"):
        nombre_elegido = (
            nombre_elegido[len("(nuevo)"):]
            .strip()
        )

    if not nombre_elegido:
        raise ValueError(
            "La resolución de matching no contiene "
            "un nombre válido."
        )

    # --------------------------------------------------------------
    # OBJETIVO
    # --------------------------------------------------------------

    if _es_matching_objetivo(problema):

        existente = _buscar_objetivo_por_nombre(
            conexion_bd,
            nombre_elegido,
        )

        if existente:
            if registro.tipo == "crear_alias":
                _crear_alias_objetivo(conexion_bd, problema.objetivo or "", existente[0])
            return (
                existente[1],
                existente[0],
            )

        if registro.tipo != "crear_nuevo":
            if registro.tipo == "crear_alias":
                raise ValueError("El objetivo elegido para alias no existe en la base de datos.")
            raise ValueError(
                f"El objetivo '{nombre_elegido}' "
                "ya no existe en la base de datos."
            )

        resultado = problema.valor_problema

        objetivo_id = _crear_objetivo(
            conexion_bd,
            nombre_elegido,
            usuario,
            fecha_inicio=(
                resultado.fecha_inicio_sugerida
            ),
        )

        return (
            nombre_elegido,
            objetivo_id,
        )

    # --------------------------------------------------------------
    # SUPERVISOR
    # --------------------------------------------------------------

    if _es_matching_supervisor(problema):

        existente = _buscar_supervisor_por_nombre(
            conexion_bd,
            nombre_elegido,
        )

        if existente:
            return (
                existente[1],
                existente[0],
            )

        if registro.tipo != "crear_nuevo":
            raise ValueError(
                f"El supervisor '{nombre_elegido}' "
                "ya no existe en la base de datos."
            )

        supervisor_id = _crear_supervisor(
            conexion_bd,
            nombre_elegido,
            usuario,
        )

        return (
            nombre_elegido,
            supervisor_id,
        )

    raise ValueError(
        "La resolución de matching no corresponde "
        "a un objetivo ni a un supervisor."
    )


# ============================================================================
# APLICAR RESOLUCIONES
# ============================================================================


def _aplicar_resoluciones(
    analisis: ResultadoAnalisis,
    resoluciones,
    conexion_bd,
    usuario,
) -> dict[int, dict[str, Any]]:

    resultado = {}

    for id_problema, registro in (
        resoluciones._resoluciones.items()
    ):

        if (
            id_problema < 0
            or id_problema >= len(analisis.problemas)
        ):
            raise ValueError(
                f"Resolución inválida: problema "
                f"{id_problema} inexistente."
            )

        problema = analisis.problemas[
            id_problema
        ]

        if registro.tipo in (
            "match_existente",
            "crear_nuevo",
            "crear_alias",
        ):

            nombre, entidad_id = (
                _resolver_nombre_match(
                    conexion_bd,
                    problema,
                    registro,
                    usuario,
                )
            )

            resultado[id_problema] = {
                "tipo": registro.tipo,
                "campo": "matching",
                "valor": nombre,
                "id": entidad_id,
            }

        elif registro.tipo == "correccion":

            resultado[id_problema] = {
                "tipo": "correccion",
                "campo": registro.campo,
                "valor": registro.valor_despues,
                "id": None,
            }

        elif registro.tipo == "aceptado":

            resultado[id_problema] = {
                "tipo": "aceptado",
                "campo": registro.campo,
                "valor": registro.valor_despues,
                "id": None,
            }

        else:
            raise ValueError(
                f"Tipo de resolución desconocido: "
                f"{registro.tipo!r}"
            )

    return resultado


# ============================================================================
# TRAZABILIDAD PROBLEMA -> PASADA
# ============================================================================


def _buscar_indice_pasada_por_problema(
    analisis: ResultadoAnalisis,
    problema: Problema,
) -> int | None:

    candidatos = []

    for indice, pasada in enumerate(
        analisis.pasadas
    ):

        if problema.hoja is not None:
            if pasada.hoja != problema.hoja:
                continue

        if problema.fila_excel is not None:
            if (
                pasada.fila_excel
                != problema.fila_excel
            ):
                continue

        candidatos.append(indice)

    if len(candidatos) == 1:
        return candidatos[0]

    if (
        len(candidatos) > 1
        and problema.objetivo
    ):
        for indice in candidatos:

            pasada = analisis.pasadas[
                indice
            ]

            if (
                pasada.objetivo_nombre
                == problema.objetivo
            ):
                return indice

    return (
        candidatos[0]
        if candidatos
        else None
    )


# ============================================================================
# CORRECCIONES
# ============================================================================


def _parsear_hora(
    valor: str,
) -> time:

    valor = valor.strip()

    for formato in (
        "%H:%M",
        "%H:%M:%S",
    ):
        try:
            return datetime.strptime(
                valor,
                formato,
            ).time()
        except ValueError:
            continue

    raise ValueError(
        f"La hora '{valor}' no tiene un "
        "formato válido. Usá HH:MM o HH:MM:SS."
    )


def _aplicar_correccion_a_pasada(
    pasada: PasadaNormalizada,
    campo: str,
    valor: str,
) -> None:

    valor = valor.strip()

    if not valor:
        raise ValueError(
            "No se puede aplicar una "
            "corrección vacía."
        )

    campo = campo.strip().lower()

    if campo in {
        "hora",
        "hora_corregida",
    }:
        pasada.hora = _parsear_hora(
            valor
        )
        return

    if campo in {
        "movil",
        "móvil",
    }:
        pasada.movil = valor
        return

    if campo == "objetivo":
        pasada.objetivo_nombre = valor
        return

    if campo == "supervisor":
        pasada.supervisor_nombre = valor
        return

    if campo == "valor_corregido":

        try:
            pasada.hora = _parsear_hora(
                valor
            )
            return
        except ValueError:
            pass

        pasada.movil = valor
        return

    raise ValueError(
        f"Campo de corrección no soportado: "
        f"{campo!r}"
    )


def _aplicar_resoluciones_a_pasadas(
    analisis: ResultadoAnalisis,
    resoluciones_aplicadas: dict[int, dict[str, Any]],
) -> None:

    for (
        id_problema,
        resolucion,
    ) in resoluciones_aplicadas.items():

        problema = analisis.problemas[
            id_problema
        ]

        indice_pasada = (
            _buscar_indice_pasada_por_problema(
                analisis,
                problema,
            )
        )

        if indice_pasada is None:
            logger.warning(
                "Resolución sin pasada asociada: hoja=%s fila=%s bloque=- motivo=no se encontró coincidencia única",
                problema.hoja, problema.fila_excel,
            )
            continue

        pasada = analisis.pasadas[
            indice_pasada
        ]

        tipo = resolucion["tipo"]

        if tipo in (
            "match_existente",
            "crear_nuevo",
            "crear_alias",
        ):

            entidad_id = resolucion["id"]
            nombre = resolucion["valor"]

            if _es_matching_objetivo(
                problema
            ):
                pasada.objetivo_id = (
                    entidad_id
                )
                pasada.objetivo_nombre = (
                    nombre
                )

            elif _es_matching_supervisor(
                problema
            ):
                pasada.supervisor_id = (
                    entidad_id
                )
                pasada.supervisor_nombre = (
                    nombre
                )

        elif tipo == "correccion":

            _aplicar_correccion_a_pasada(
                pasada,
                resolucion["campo"],
                str(resolucion["valor"]),
            )


# ============================================================================
# BÚSQUEDA DE PASADA EXISTENTE
# ============================================================================


def _obtener_pasada_existente(
    conexion_bd,
    pasada: PasadaNormalizada,
):

    return conexion_bd.execute(
        """
        SELECT
            id,
            fecha,
            hora,
            turno,
            objetivo_id,
            supervisor_id,
            notas,
            fecha_operativa
        FROM pasadas
        WHERE fecha = ?
          AND hora = ?
          AND turno = ?
          AND objetivo_id = ?
        ORDER BY id
        LIMIT 1
        """,
        (
            _valor_sql(
                pasada.fecha_calendario
            ),
            _valor_sql(
                pasada.hora
            ),
            pasada.turno,
            pasada.objetivo_id,
        ),
    ).fetchone()


# ============================================================================
# INSERTAR PASADA
# ============================================================================


def _insertar_pasada(
    conexion_bd,
    pasada: PasadaNormalizada,
) -> int:

    if pasada.objetivo_id is None:
        raise ValueError(
            f"La pasada de "
            f"{pasada.fecha_calendario} "
            f"{pasada.hora} no tiene "
            "objetivo_id."
        )

    cursor = conexion_bd.execute(
        """
        INSERT INTO pasadas (
            fecha,
            hora,
            turno,
            objetivo_id,
            supervisor_id,
            notas,
            fecha_operativa
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _valor_sql(
                pasada.fecha_calendario
            ),
            _valor_sql(
                pasada.hora
            ),
            pasada.turno,
            pasada.objetivo_id,
            pasada.supervisor_id,
            "",
            _valor_sql(
                pasada.fecha_operativa
            ),
        ),
    )

    return cursor.lastrowid


# ============================================================================
# ACTUALIZAR PASADA
# ============================================================================


def _actualizar_pasada(
    conexion_bd,
    id_pasada: int,
    pasada: PasadaNormalizada,
) -> None:

    conexion_bd.execute(
        """
        UPDATE pasadas
        SET
            fecha = ?,
            hora = ?,
            turno = ?,
            objetivo_id = ?,
            supervisor_id = ?,
            notas = ?,
            fecha_operativa = ?
        WHERE id = ?
        """,
        (
            _valor_sql(
                pasada.fecha_calendario
            ),
            _valor_sql(
                pasada.hora
            ),
            pasada.turno,
            pasada.objetivo_id,
            pasada.supervisor_id,
            "",
            _valor_sql(
                pasada.fecha_operativa
            ),
            id_pasada,
        ),
    )


# ============================================================================
# PERSISTENCIA DE PASADAS + AUDITORÍA
# ============================================================================


def _persistir_pasadas(
    conexion_bd,
    analisis: ResultadoAnalisis,
    usuario,
) -> tuple[int, int, int]:

    nuevas = 0
    actualizadas = 0
    omitidas = 0

    for pasada in analisis.pasadas:

        accion = pasada.accion

        # --------------------------------------------------------------
        # OMITIR
        # --------------------------------------------------------------

        if accion == "omitir":

            omitidas += 1
            logger.info(
                "Pasada omitida: hoja=%s fila=%d bloque=%d objetivo=%r motivo=acción omitir",
                pasada.hoja, pasada.fila_excel, pasada.bloque_tabla, pasada.objetivo_nombre,
            )
            continue

        # Una pasada sin objetivo resuelto queda sin acción y se omite sin
        # interrumpir la importación del resto del archivo.
        if accion is None:
            omitidas += 1
            logger.warning(
                "Pasada omitida: hoja=%s fila=%d bloque=%d objetivo=%r motivo=objetivo sin matching resuelto",
                pasada.hoja, pasada.fila_excel, pasada.bloque_tabla, pasada.objetivo_nombre,
            )
            continue

        # --------------------------------------------------------------
        # NUEVA
        # --------------------------------------------------------------

        if accion == "nueva":

            existente = (
                _obtener_pasada_existente(
                    conexion_bd,
                    pasada,
                )
            )

            if existente:
                omitidas += 1
                logger.info(
                    "Pasada omitida: hoja=%s fila=%d bloque=%d objetivo=%r motivo=ya existe en BD",
                    pasada.hoja, pasada.fila_excel, pasada.bloque_tabla, pasada.objetivo_nombre,
                )
                continue

            id_nueva = _insertar_pasada(
                conexion_bd,
                pasada,
            )

            nuevas += 1

            registrar_auditoria(
                {
                    "usuario": usuario,
                    "tipo_operacion": "INSERT",
                    "tabla": "pasadas",
                    "registro_id": id_nueva,
                    "valores_anteriores": None,
                    "valores_nuevos": {
                        "id": id_nueva,
                        "fecha": _valor_sql(
                            pasada.fecha_calendario
                        ),
                        "hora": _valor_sql(
                            pasada.hora
                        ),
                        "turno": pasada.turno,
                        "objetivo_id": (
                            pasada.objetivo_id
                        ),
                        "supervisor_id": (
                            pasada.supervisor_id
                        ),
                        "notas": "",
                        "fecha_operativa": (
                            _valor_sql(
                                pasada.fecha_operativa
                            )
                        ),
                    },
                    "detalles": {
                        "accion": (
                            "Nueva pasada desde "
                            "importación"
                        ),
                        "hoja": pasada.hoja,
                        "fila_excel": (
                            pasada.fila_excel
                        ),
                    },
                },
                conexion_bd,
            )

            continue

        # --------------------------------------------------------------
        # ACTUALIZAR / SOBRESCRITURA
        # --------------------------------------------------------------

        if accion == "actualizar":

            existente = (
                _obtener_pasada_existente(
                    conexion_bd,
                    pasada,
                )
            )

            if not existente:
                raise ValueError(
                    "Una pasada marcada para "
                    "actualizar ya no existe "
                    "en la base de datos. "
                    "La importación fue cancelada."
                )

            id_pasada = existente[0]

            valores_anteriores = {
                "id": existente[0],
                "fecha": existente[1],
                "hora": existente[2],
                "turno": existente[3],
                "objetivo_id": existente[4],
                "supervisor_id": existente[5],
                "notas": existente[6],
                "fecha_operativa": existente[7],
            }

            valores_nuevos = {
                "id": id_pasada,
                "fecha": _valor_sql(
                    pasada.fecha_calendario
                ),
                "hora": _valor_sql(
                    pasada.hora
                ),
                "turno": pasada.turno,
                "objetivo_id": (
                    pasada.objetivo_id
                ),
                "supervisor_id": (
                    pasada.supervisor_id
                ),
                "notas": "",
                "fecha_operativa": (
                    _valor_sql(
                        pasada.fecha_operativa
                    )
                ),
            }

            # ----------------------------------------------------------
            # IMPORTANTE:
            # El histórico se registra ANTES del UPDATE.
            # ----------------------------------------------------------

            registrar_auditoria(
                {
                    "usuario": usuario,
                    "tipo_operacion": (
                        "SOBRESCRITURA_DURANTE_IMPORTACION"
                    ),
                    "tabla": "pasadas",
                    "registro_id": id_pasada,
                    "valores_anteriores": (
                        valores_anteriores
                    ),
                    "valores_nuevos": (
                        valores_nuevos
                    ),
                    "detalles": _detalles_historico(
                        "Sobrescritura de pasada "
                        "por reimportación forzada."
                    ),
                },
                conexion_bd,
            )

            # ----------------------------------------------------------
            # Recién después de auditar el valor anterior,
            # hacemos el UPDATE.
            # ----------------------------------------------------------

            _actualizar_pasada(
                conexion_bd,
                id_pasada,
                pasada,
            )

            actualizadas += 1

            continue

        raise ValueError(
            f"Acción de pasada desconocida: "
            f"{accion!r}. "
            f"Hoja={pasada.hoja}, "
            f"fila={pasada.fila_excel}"
        )

    return (
        nuevas,
        actualizadas,
        omitidas,
    )


# ============================================================================
# AUDITORÍA DE RESOLUCIONES
# ============================================================================


def _registrar_resoluciones_auditoria(
    resoluciones,
    conexion_bd,
) -> int:
    """
    Registra las correcciones manuales realizadas durante la revisión.

    Matching y altas tienen auditorías propias.

    Devuelve cantidad de correcciones.
    """

    correcciones = 0

    for registro in (
        resoluciones.todos_los_registros()
    ):

        if registro.tipo != "correccion":
            continue

        correcciones += 1

        registrar_auditoria(
            {
                "usuario": registro.usuario,
                "tipo_operacion": (
                    "CORRECCION_DURANTE_IMPORTACION"
                ),
                "tabla": None,
                "registro_id": None,
                "valores_anteriores": {
                    "hoja": registro.hoja,
                    "objetivo": registro.objetivo,
                    "campo": registro.campo,
                    "valor": registro.valor_antes,
                },
                "valores_nuevos": {
                    "hoja": registro.hoja,
                    "objetivo": registro.objetivo,
                    "campo": registro.campo,
                    "valor": registro.valor_despues,
                },
                "detalles": {
                    "accion": (
                        "Corrección durante importación"
                    ),
                },
            },
            conexion_bd,
        )

    return correcciones


# ============================================================================
# IMPORTACIÓN COMPLETA
# ============================================================================


def confirmar_importacion_completa(
    analisis: ResultadoAnalisis,
    resoluciones,
    usuario,
    conexion_bd,
) -> dict:
    """
    Ejecuta la importación completa.

    TODO se realiza dentro de una única transacción.

    Si cualquier INSERT, UPDATE o auditoría falla:

        rollback()

    y no queda ninguna parte de la importación persistida.
    """

    # ------------------------------------------------------------------
    # 1. Defensa contra estados inconsistentes
    # ------------------------------------------------------------------

    _validar_analisis(
        analisis,
        resoluciones,
    )

    if conexion_bd is None:
        raise ValueError(
            "Se necesita una conexión a la "
            "base de datos."
        )

    if getattr(
        conexion_bd,
        "in_transaction",
        False,
    ):
        raise RuntimeError(
            "La conexión ya tiene una "
            "transacción activa."
        )

    # ------------------------------------------------------------------
    # 2. Cantidades iniciales
    # ------------------------------------------------------------------

    cantidad_nuevas = sum(
        1
        for pasada in analisis.pasadas
        if pasada.accion == "nueva"
    )

    cantidad_actualizar = sum(
        1
        for pasada in analisis.pasadas
        if pasada.accion == "actualizar"
    )

    cantidad_omitir = sum(
        1
        for pasada in analisis.pasadas
        if pasada.accion in ("omitir", None)
    )

    # ------------------------------------------------------------------
    # 3. Archivo completamente procesado
    # ------------------------------------------------------------------

    if (
        cantidad_nuevas == 0
        and cantidad_actualizar == 0
    ):

        return {
            "pasadas_importadas": 0,
            "pasadas_nuevas": 0,
            "pasadas_actualizadas": 0,
            "pasadas_omitidas": cantidad_omitir,
            "objetivos_creados": 0,
            "supervisores_creados": 0,
            "correcciones": 0,
            "total": len(
                analisis.pasadas
            ),
            "mensaje": (
                "Este archivo ya fue procesado. "
                "No hay nuevas pasadas para importar."
            ),
        }

    # ------------------------------------------------------------------
    # 4. Cantidad de entidades antes de la transacción
    # ------------------------------------------------------------------

    objetivos_antes = conexion_bd.execute(
        "SELECT COUNT(*) FROM objetivos"
    ).fetchone()[0]

    supervisores_antes = conexion_bd.execute(
        "SELECT COUNT(*) FROM supervisores"
    ).fetchone()[0]

    try:

        # ==============================================================
        # UNA ÚNICA TRANSACCIÓN
        # ==============================================================

        conexion_bd.execute("BEGIN")

        # --------------------------------------------------------------
        # 5. Matching / altas
        # --------------------------------------------------------------

        resoluciones_aplicadas = (
            _aplicar_resoluciones(
                analisis,
                resoluciones,
                conexion_bd,
                usuario,
            )
        )

        # --------------------------------------------------------------
        # 6. Aplicar correcciones a las pasadas
        # --------------------------------------------------------------

        _aplicar_resoluciones_a_pasadas(
            analisis,
            resoluciones_aplicadas,
        )

        # --------------------------------------------------------------
        # 7. Persistir pasadas
        # --------------------------------------------------------------

        (
            nuevas,
            actualizadas,
            omitidas,
        ) = _persistir_pasadas(
            conexion_bd,
            analisis,
            usuario,
        )

        # --------------------------------------------------------------
        # 8. Auditoría de correcciones
        # --------------------------------------------------------------

        correcciones = (
            _registrar_resoluciones_auditoria(
                resoluciones,
                conexion_bd,
            )
        )

        # --------------------------------------------------------------
        # 9. Cantidad de objetivos/supervisores creados
        # --------------------------------------------------------------

        objetivos_despues = conexion_bd.execute(
            "SELECT COUNT(*) FROM objetivos"
        ).fetchone()[0]

        supervisores_despues = conexion_bd.execute(
            "SELECT COUNT(*) FROM supervisores"
        ).fetchone()[0]

        objetivos_creados = max(
            0,
            objetivos_despues
            - objetivos_antes,
        )

        supervisores_creados = max(
            0,
            supervisores_despues
            - supervisores_antes,
        )

        # --------------------------------------------------------------
        # 10. Resumen
        # --------------------------------------------------------------

        resumen = {
            "pasadas_importadas": nuevas,
            "pasadas_nuevas": nuevas,
            "pasadas_actualizadas": actualizadas,
            "pasadas_omitidas": omitidas,
            "objetivos_creados": (
                objetivos_creados
            ),
            "supervisores_creados": (
                supervisores_creados
            ),
            "correcciones": correcciones,
            "total": len(
                analisis.pasadas
            ),
        }

        # --------------------------------------------------------------
        # 11. UN registro por importación completa
        # --------------------------------------------------------------

        registrar_auditoria(
            {
                "usuario": usuario,
                "tipo_operacion": (
                    "IMPORTACION_COMPLETA"
                ),
                "tabla": None,
                "registro_id": None,
                "valores_anteriores": None,
                "valores_nuevos": resumen,
                "detalles": {
                    "accion": (
                        "Importación completa"
                    ),
                    "cantidad_pasadas_importadas": (
                        nuevas
                    ),
                    "cantidad_pasadas_omitidas": (
                        omitidas
                    ),
                    "cantidad_correcciones": (
                        correcciones
                    ),
                    "cantidad_pasadas_actualizadas": (
                        actualizadas
                    ),
                    "archivo_original_guardado": (
                        False
                    ),
                },
            },
            conexion_bd,
        )

        # --------------------------------------------------------------
        # 12. COMMIT
        # --------------------------------------------------------------

        conexion_bd.commit()

        # --------------------------------------------------------------
        # 13. Mensaje final
        # --------------------------------------------------------------

        resumen["mensaje"] = (
            f"Se importaron {nuevas} pasadas, "
            f"se actualizaron {actualizadas} y "
            f"se omitieron {omitidas} ya existentes."
        )

        return resumen

    except Exception:

        # ==============================================================
        # CUALQUIER ERROR => ROLLBACK COMPLETO
        # ==============================================================

        try:
            conexion_bd.rollback()
        except Exception:
            pass

        raise


# ============================================================================
# API PÚBLICA INTERNA
# ============================================================================


def confirmar_importacion(
    analisis: ResultadoAnalisis,
    resoluciones,
    usuario,
    conexion_bd,
) -> dict:
    """
    Alias de confirmar_importacion_completa().
    """

    return confirmar_importacion_completa(
        analisis=analisis,
        resoluciones=resoluciones,
        usuario=usuario,
        conexion_bd=conexion_bd,
    )