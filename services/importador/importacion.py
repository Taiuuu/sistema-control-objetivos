"""
Confirmación e importación transaccional a la base de datos.

FASE 13:
    - valida que no queden bloqueantes;
    - resuelve altas de objetivos/supervisores;
    - inserta pasadas nuevas;
    - actualiza pasadas cuando corresponde;
    - omite las ya existentes;
    - registra auditoría;
    - ejecuta todo dentro de una única transacción;
    - hace rollback completo ante cualquier error.

La capa de UI debe encargarse de pedir la confirmación al usuario
antes de llamar a confirmar_importacion_completa().
"""

from __future__ import annotations

import json
from datetime import date, datetime, time
from typing import Any

from .modelos import (
    PasadaNormalizada,
    Problema,
    ResultadoAnalisis,
    ResultadoMatchObjetivo,
    ResultadoMatchSupervisor,
)


# ============================================================================
# UTILIDADES
# ============================================================================


def _valor_sql(valor: Any) -> Any:
    """
    Convierte valores Python utilizados por los modelos a valores
    compatibles con SQLite.
    """
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.isoformat(sep=" ")

    if isinstance(valor, date):
        return valor.isoformat()

    if isinstance(valor, time):
        return valor.strftime("%H:%M:%S")

    return valor


def _usuario_id(conexion_bd, usuario) -> int | None:
    """
    Obtiene el ID del usuario a partir de su nombre.

    `usuario` puede ser:
        - un string con el username;
        - un objeto que tenga `.username`;
        - un objeto que tenga `.id`.

    Si no puede resolverse, devuelve None.
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
        "SELECT id FROM usuarios WHERE username = ?",
        (username,),
    ).fetchone()

    return fila[0] if fila else None


def _nombre_usuario(usuario) -> str:
    """Obtiene una representación estable del usuario para auditoría."""
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


def _fecha_hora_actual() -> tuple[str, str]:
    ahora = datetime.now()
    return ahora.date().isoformat(), ahora.strftime("%H:%M:%S")


def _serializar(valor: Any) -> str:
    """
    Serializa valores para almacenarlos en las columnas TEXT de auditoria.
    """
    if valor is None:
        return ""

    if isinstance(valor, (dict, list, tuple)):
        try:
            return json.dumps(valor, ensure_ascii=False, default=str)
        except Exception:
            return str(valor)

    return str(valor)


# ============================================================================
# VALIDACIONES
# ============================================================================


def _validar_analisis(analisis: ResultadoAnalisis, resoluciones) -> None:
    """
    Defensa contra estados inconsistentes.

    No alcanza con confiar en ResultadoAnalisis.puede_continuar:
    también verificamos directamente los problemas y el EstadoResolucion.
    """

    if analisis is None:
        raise ValueError("No se recibió un ResultadoAnalisis.")

    if resoluciones is None:
        raise ValueError("No se recibió el estado de resoluciones.")

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

        if len(errores_criticos) > 5:
            detalles += f"; ... y {len(errores_criticos) - 5} más"

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

        if len(pendientes) > 5:
            detalles += f"; ... y {len(pendientes) - 5} más"

        raise ValueError(
            "No se puede importar porque quedan problemas de "
            f"matching sin resolver: {detalles}"
        )


# ============================================================================
# RESOLUCIÓN DE ENTIDADES
# ============================================================================


def _es_matching_objetivo(problema: Problema) -> bool:
    return isinstance(
        problema.valor_problema,
        ResultadoMatchObjetivo,
    )


def _es_matching_supervisor(problema: Problema) -> bool:
    return isinstance(
        problema.valor_problema,
        ResultadoMatchSupervisor,
    )


def _buscar_objetivo_por_nombre(conexion_bd, nombre: str):
    fila = conexion_bd.execute(
        """
        SELECT id, nombre
        FROM objetivos
        WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
        """,
        (nombre,),
    ).fetchone()

    return fila


def _buscar_supervisor_por_nombre(conexion_bd, nombre: str):
    fila = conexion_bd.execute(
        """
        SELECT id, nombre
        FROM supervisores
        WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))
        ORDER BY id
        LIMIT 1
        """,
        (nombre,),
    ).fetchone()

    return fila


def _crear_objetivo(
    conexion_bd,
    nombre: str,
    fecha_inicio: date | None = None,
) -> int:
    """
    Crea un objetivo y devuelve su ID.

    El esquema actual solamente exige nombre.
    """
    if not nombre or not nombre.strip():
        raise ValueError("No se puede crear un objetivo sin nombre.")

    nombre = nombre.strip()

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

    return cursor.lastrowid


def _crear_supervisor(conexion_bd, nombre: str) -> int:
    """Crea un supervisor y devuelve su ID."""
    if not nombre or not nombre.strip():
        raise ValueError("No se puede crear un supervisor sin nombre.")

    nombre = nombre.strip()

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

    return cursor.lastrowid


def _resolver_nombre_match(
    conexion_bd,
    problema: Problema,
    registro,
) -> tuple[str, int]:
    """
    Convierte una resolución de matching en (nombre, id).

    Para:
        match_existente -> busca el nombre elegido en BD.

        crear_nuevo -> crea la entidad si todavía no existe.
    """

    nombre_elegido = registro.valor_despues.strip()

    if registro.tipo == "crear_nuevo":
        if nombre_elegido.startswith("(nuevo)"):
            nombre_elegido = nombre_elegido[len("(nuevo)") :].strip()

    if not nombre_elegido:
        raise ValueError(
            "La resolución de matching no contiene un nombre válido."
        )

    if _es_matching_objetivo(problema):
        existente = _buscar_objetivo_por_nombre(
            conexion_bd,
            nombre_elegido,
        )

        if existente:
            return existente[1], existente[0]

        if registro.tipo != "crear_nuevo":
            raise ValueError(
                f"El objetivo '{nombre_elegido}' elegido para matching "
                "ya no existe en la base de datos."
            )

        resultado = problema.valor_problema

        objetivo_id = _crear_objetivo(
            conexion_bd,
            nombre_elegido,
            fecha_inicio=resultado.fecha_inicio_sugerida,
        )

        return nombre_elegido, objetivo_id

    if _es_matching_supervisor(problema):
        existente = _buscar_supervisor_por_nombre(
            conexion_bd,
            nombre_elegido,
        )

        if existente:
            return existente[1], existente[0]

        if registro.tipo != "crear_nuevo":
            raise ValueError(
                f"El supervisor '{nombre_elegido}' elegido para matching "
                "ya no existe en la base de datos."
            )

        supervisor_id = _crear_supervisor(
            conexion_bd,
            nombre_elegido,
        )

        return nombre_elegido, supervisor_id

    raise ValueError(
        "Se recibió una resolución de matching para un problema "
        "que no contiene ResultadoMatchObjetivo ni "
        "ResultadoMatchSupervisor."
    )


# ============================================================================
# APLICACIÓN DE RESOLUCIONES
# ============================================================================


def _aplicar_resoluciones(
    analisis: ResultadoAnalisis,
    resoluciones,
    conexion_bd,
) -> dict[int, dict[str, Any]]:
    """
    Traduce las decisiones de EstadoResolucion a información que luego
    utilizará la persistencia de pasadas.

    Devuelve:

        {
            indice_problema: {
                "tipo": ...,
                "valor": ...,
                "id": ...
            }
        }
    """

    resultado: dict[int, dict[str, Any]] = {}

    for id_problema, registro in resoluciones._resoluciones.items():

        if id_problema < 0 or id_problema >= len(analisis.problemas):
            raise ValueError(
                f"Resolución inválida: el problema {id_problema} "
                "no existe en ResultadoAnalisis."
            )

        problema = analisis.problemas[id_problema]

        if registro.tipo in ("match_existente", "crear_nuevo"):
            nombre, entidad_id = _resolver_nombre_match(
                conexion_bd,
                problema,
                registro,
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
                f"Tipo de resolución desconocido: {registro.tipo!r}"
            )

    return resultado


# ============================================================================
# IDENTIFICACIÓN DE PASADAS AFECTADAS
# ============================================================================


def _buscar_indice_pasada_por_problema(
    analisis: ResultadoAnalisis,
    problema: Problema,
) -> int | None:
    """
    Busca la pasada normalizada correspondiente al problema.

    La trazabilidad disponible en los modelos es:
        hoja + fila_excel.

    Si el problema no tiene fila, intenta usar objetivo + hoja.
    """

    candidatos = []

    for indice, pasada in enumerate(analisis.pasadas):

        if problema.hoja is not None:
            if pasada.hoja != problema.hoja:
                continue

        if problema.fila_excel is not None:
            if pasada.fila_excel != problema.fila_excel:
                continue

        candidatos.append(indice)

    if len(candidatos) == 1:
        return candidatos[0]

    if len(candidatos) > 1 and problema.objetivo:
        for indice in candidatos:
            pasada = analisis.pasadas[indice]

            if (
                pasada.objetivo_nombre
                and pasada.objetivo_nombre == problema.objetivo
            ):
                return indice

    return candidatos[0] if candidatos else None


def _parsear_hora(valor: str) -> time:
    """
    Convierte una corrección de hora a datetime.time.

    Acepta:
        HH:MM
        HH:MM:SS
    """
    valor = valor.strip()

    formatos = (
        "%H:%M",
        "%H:%M:%S",
    )

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato).time()
        except ValueError:
            continue

    raise ValueError(
        f"La hora corregida '{valor}' no tiene un formato válido. "
        "Usá HH:MM o HH:MM:SS."
    )


def _aplicar_correccion_a_pasada(
    pasada: PasadaNormalizada,
    campo: str,
    valor: str,
) -> None:
    """
    Aplica una corrección manual a la pasada en memoria.

    Actualmente la resolución de la UI utiliza:
        campo="valor_corregido"

    En ese caso se intenta determinar qué valor corresponde corregir
    utilizando el valor original del problema.
    """

    valor = valor.strip()

    if not valor:
        raise ValueError(
            "No se puede aplicar una corrección vacía."
        )

    campo_normalizado = campo.strip().lower()

    if campo_normalizado in {
        "hora",
        "hora_corregida",
    }:
        pasada.hora = _parsear_hora(valor)
        return

    if campo_normalizado in {
        "movil",
        "móvil",
    }:
        pasada.movil = valor
        return

    if campo_normalizado == "objetivo":
        pasada.objetivo_nombre = valor
        return

    if campo_normalizado == "supervisor":
        pasada.supervisor_nombre = valor
        return

    if campo_normalizado == "valor_corregido":
        """
        La UI actual utiliza este campo genérico.

        Primero intentamos interpretar el valor como una hora. Si no
        es una hora válida, lo tratamos como móvil. Esto mantiene
        compatibilidad con la Fase 12 sin agregar todavía `categoria`
        a Problema.
        """
        try:
            pasada.hora = _parsear_hora(valor)
            return
        except ValueError:
            pass

        pasada.movil = valor
        return

    raise ValueError(
        f"Campo de corrección no soportado: {campo!r}"
    )


def _aplicar_resoluciones_a_pasadas(
    analisis: ResultadoAnalisis,
    resoluciones,
    resoluciones_aplicadas: dict[int, dict[str, Any]],
) -> None:
    """
    Aplica las correcciones/matches sobre las PasadaNormalizada antes
    de persistirlas.
    """

    for id_problema, resolucion in resoluciones_aplicadas.items():

        problema = analisis.problemas[id_problema]

        indice_pasada = _buscar_indice_pasada_por_problema(
            analisis,
            problema,
        )

        if indice_pasada is None:
            # Una resolución puede corresponder a un problema que no
            # tenga una pasada persistible, por ejemplo un problema
            # global del archivo. En ese caso la resolución queda
            # auditada pero no modifica una pasada.
            continue

        pasada = analisis.pasadas[indice_pasada]

        tipo = resolucion["tipo"]

        if tipo in ("match_existente", "crear_nuevo"):

            entidad_id = resolucion["id"]
            nombre = resolucion["valor"]

            if _es_matching_objetivo(problema):
                pasada.objetivo_id = entidad_id
                pasada.objetivo_nombre = nombre

            elif _es_matching_supervisor(problema):
                pasada.supervisor_id = entidad_id
                pasada.supervisor_nombre = nombre

        elif tipo == "correccion":

            _aplicar_correccion_a_pasada(
                pasada,
                resolucion["campo"],
                str(resolucion["valor"]),
            )

        elif tipo == "aceptado":
            # No se modifica la pasada.
            continue


# ============================================================================
# PERSISTENCIA DE PASADAS
# ============================================================================


def _obtener_pasada_existente(
    conexion_bd,
    pasada: PasadaNormalizada,
):
    """
    Busca una pasada existente utilizando la identidad lógica definida
    por fecha + hora + turno + objetivo.

    La tabla actual no tiene una columna de móvil ni de fila Excel.
    """

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
            _valor_sql(pasada.fecha_calendario),
            _valor_sql(pasada.hora),
            pasada.turno,
            pasada.objetivo_id,
        ),
    ).fetchone()


def _insertar_pasada(
    conexion_bd,
    pasada: PasadaNormalizada,
) -> int:
    """
    Inserta una pasada nueva.
    """

    if pasada.objetivo_id is None:
        raise ValueError(
            f"La pasada de {pasada.fecha_calendario} "
            f"{pasada.hora} no tiene objetivo_id."
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
            _valor_sql(pasada.fecha_calendario),
            _valor_sql(pasada.hora),
            pasada.turno,
            pasada.objetivo_id,
            pasada.supervisor_id,
            "",
            _valor_sql(pasada.fecha_operativa),
        ),
    )

    return cursor.lastrowid


def _actualizar_pasada(
    conexion_bd,
    id_pasada: int,
    pasada: PasadaNormalizada,
) -> None:
    """
    Actualiza una pasada existente.
    """

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
            _valor_sql(pasada.fecha_calendario),
            _valor_sql(pasada.hora),
            pasada.turno,
            pasada.objetivo_id,
            pasada.supervisor_id,
            "",
            _valor_sql(pasada.fecha_operativa),
            id_pasada,
        ),
    )


def _persistir_pasadas(
    conexion_bd,
    analisis: ResultadoAnalisis,
    usuario,
) -> tuple[int, int, int]:
    """
    Persiste las pasadas según su acción.

    Devuelve:
        (nuevas, actualizadas, omitidas)

    La decisión `accion` viene del pipeline de fases anteriores.
    Como defensa adicional se vuelve a comprobar la existencia en BD.
    """

    nuevas = 0
    actualizadas = 0
    omitidas = 0

    for pasada in analisis.pasadas:

        accion = pasada.accion

        if accion == "omitir":
            omitidas += 1
            continue

        if accion == "nueva":
            existente = _obtener_pasada_existente(
                conexion_bd,
                pasada,
            )

            if existente:
                """
                Defensa contra que la BD haya cambiado entre análisis
                y confirmación.
                """
                omitidas += 1
                continue

            id_nueva = _insertar_pasada(
                conexion_bd,
                pasada,
            )

            nuevas += 1

            registrar_auditoria(
                {
                    "usuario": _nombre_usuario(usuario),
                    "tipo_operacion": "INSERT",
                    "tabla": "pasadas",
                    "registro_id": id_nueva,
                    "valores_anteriores": {},
                    "valores_nuevos": {
                        "fecha": _valor_sql(pasada.fecha_calendario),
                        "hora": _valor_sql(pasada.hora),
                        "turno": pasada.turno,
                        "objetivo_id": pasada.objetivo_id,
                        "supervisor_id": pasada.supervisor_id,
                        "fecha_operativa": _valor_sql(
                            pasada.fecha_operativa
                        ),
                    },
                    "detalles": (
                        f"Importación desde hoja '{pasada.hoja}', "
                        f"fila {pasada.fila_excel}"
                    ),
                },
                conexion_bd,
            )

            continue

        if accion == "actualizar":

            existente = _obtener_pasada_existente(
                conexion_bd,
                pasada,
            )

            if not existente:
                """
                Si la pasada marcada como actualizar ya no existe,
                es más seguro abortar que insertar silenciosamente.
                """
                raise ValueError(
                    "Una pasada marcada para actualizar ya no existe "
                    "en la base de datos. La importación fue cancelada "
                    "para evitar un estado inconsistente."
                )

            id_pasada = existente[0]

            valores_anteriores = {
                "fecha": existente[1],
                "hora": existente[2],
                "turno": existente[3],
                "objetivo_id": existente[4],
                "supervisor_id": existente[5],
                "notas": existente[6],
                "fecha_operativa": existente[7],
            }

            _actualizar_pasada(
                conexion_bd,
                id_pasada,
                pasada,
            )

            actualizadas += 1

            registrar_auditoria(
                {
                    "usuario": _nombre_usuario(usuario),
                    "tipo_operacion": "UPDATE",
                    "tabla": "pasadas",
                    "registro_id": id_pasada,
                    "valores_anteriores": valores_anteriores,
                    "valores_nuevos": {
                        "fecha": _valor_sql(pasada.fecha_calendario),
                        "hora": _valor_sql(pasada.hora),
                        "turno": pasada.turno,
                        "objetivo_id": pasada.objetivo_id,
                        "supervisor_id": pasada.supervisor_id,
                        "fecha_operativa": _valor_sql(
                            pasada.fecha_operativa
                        ),
                    },
                    "detalles": (
                        f"Sobrescritura desde hoja '{pasada.hoja}', "
                        f"fila {pasada.fila_excel}"
                    ),
                },
                conexion_bd,
            )

            continue

        raise ValueError(
            f"Acción de pasada desconocida: {accion!r}. "
            f"Hoja={pasada.hoja}, fila={pasada.fila_excel}"
        )

    return nuevas, actualizadas, omitidas


# ============================================================================
# AUDITORÍA
# ============================================================================


def registrar_auditoria(evento: dict, conexion_bd) -> None:
    """
    Registra un evento en la tabla auditoria.

    Esta función NO hace commit.

    Es fundamental para la transacción: si la auditoría falla,
    confirmar_importacion_completa() captura la excepción y hace
    rollback de toda la importación.
    """

    fecha, hora = _fecha_hora_actual()

    usuario = evento.get("usuario")
    usuario_id = evento.get("usuario_id")

    if usuario_id is None:
        usuario_id = _usuario_id(
            conexion_bd,
            usuario,
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
            str(evento.get("tipo_operacion", "IMPORTACION")),
            evento.get("tabla"),
            evento.get("registro_id"),
            _serializar(evento.get("valores_anteriores")),
            _serializar(evento.get("valores_nuevos")),
            str(evento.get("detalles", "")),
            str(evento.get("estado", "EXITOSO")),
        ),
    )


def _registrar_resoluciones_auditoria(
    resoluciones,
    conexion_bd,
) -> None:
    """
    Registra las decisiones tomadas en la pantalla de revisión.

    Las resoluciones ya tienen toda la información necesaria:
        usuario
        hoja
        objetivo
        campo
        valor_antes
        valor_despues
        tipo
    """

    for registro in resoluciones.todos_los_registros():

        registrar_auditoria(
            {
                "usuario": registro.usuario,
                "tipo_operacion": registro.tipo,
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
                "detalles": (
                    "Resolución tomada durante la revisión "
                    "previa a la importación."
                ),
            },
            conexion_bd,
        )


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
    Ejecuta la importación real dentro de una única transacción.

    IMPORTANTE:
        La confirmación visual del usuario debe realizarse en la UI
        ANTES de llamar a esta función.

    La función:

        1. valida errores críticos;
        2. valida matching pendiente;
        3. resuelve altas/matches;
        4. aplica correcciones;
        5. inserta pasadas nuevas;
        6. actualiza pasadas a sobrescribir;
        7. omite las existentes;
        8. registra auditoría;
        9. hace COMMIT;
       10. hace ROLLBACK ante cualquier excepción.

    Devuelve un dict compatible con el resumen esperado por la UI.
    """

    _validar_analisis(
        analisis,
        resoluciones,
    )

    if conexion_bd is None:
        raise ValueError(
            "Se necesita una conexión a la base de datos."
        )

    # ------------------------------------------------------------------
    # Defensa: no iniciar una transacción dentro de otra.
    # ------------------------------------------------------------------

    if getattr(conexion_bd, "in_transaction", False):
        raise RuntimeError(
            "La conexión de base de datos ya tiene una transacción "
            "activa. La importación debe ejecutarse sobre una conexión "
            "sin una transacción previa."
        )

    # ------------------------------------------------------------------
    # Determinación previa de cantidades.
    # ------------------------------------------------------------------

    cantidad_omitir = sum(
        1
        for pasada in analisis.pasadas
        if pasada.accion == "omitir"
    )

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

    # ------------------------------------------------------------------
    # Archivo ya procesado.
    #
    # Si el análisis indica que todo está para omitir y no hay
    # sobrescrituras, no hacemos ninguna escritura.
    # ------------------------------------------------------------------

    if cantidad_nuevas == 0 and cantidad_actualizar == 0:
        return {
            "pasadas_importadas": 0,
            "pasadas_nuevas": 0,
            "pasadas_actualizadas": 0,
            "pasadas_omitidas": cantidad_omitir,
            "objetivos_creados": 0,
            "supervisores_creados": 0,
            "correcciones": 0,
            "total": len(analisis.pasadas),
            "mensaje": (
                "Este archivo ya fue procesado. "
                "No hay nuevas pasadas para importar."
            ),
        }

    # Guardamos cantidad de entidades antes de la operación para poder
    # calcular cuántas fueron creadas realmente.
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
        # 1. Resolver matching / crear entidades.
        # --------------------------------------------------------------

        resoluciones_aplicadas = _aplicar_resoluciones(
            analisis,
            resoluciones,
            conexion_bd,
        )

        # --------------------------------------------------------------
        # 2. Aplicar correcciones y matching a las pasadas en memoria.
        # --------------------------------------------------------------

        _aplicar_resoluciones_a_pasadas(
            analisis,
            resoluciones,
            resoluciones_aplicadas,
        )

        # --------------------------------------------------------------
        # 3. Persistir pasadas.
        # --------------------------------------------------------------

        nuevas, actualizadas, omitidas = _persistir_pasadas(
            conexion_bd,
            analisis,
            usuario,
        )

        # --------------------------------------------------------------
        # 4. Registrar todas las resoluciones tomadas.
        # --------------------------------------------------------------

        _registrar_resoluciones_auditoria(
            resoluciones,
            conexion_bd,
        )

        # --------------------------------------------------------------
        # 5. Cantidad de entidades creadas.
        # --------------------------------------------------------------

        objetivos_despues = conexion_bd.execute(
            "SELECT COUNT(*) FROM objetivos"
        ).fetchone()[0]

        supervisores_despues = conexion_bd.execute(
            "SELECT COUNT(*) FROM supervisores"
        ).fetchone()[0]

        objetivos_creados = max(
            0,
            objetivos_despues - objetivos_antes,
        )

        supervisores_creados = max(
            0,
            supervisores_despues - supervisores_antes,
        )

        correcciones = sum(
            1
            for registro in resoluciones.todos_los_registros()
            if registro.tipo == "correccion"
        )

        # --------------------------------------------------------------
        # 6. Auditoría del resumen completo.
        # --------------------------------------------------------------

        resumen = {
            "pasadas_importadas": nuevas,
            "pasadas_nuevas": nuevas,
            "pasadas_actualizadas": actualizadas,
            "pasadas_omitidas": omitidas,
            "objetivos_creados": objetivos_creados,
            "supervisores_creados": supervisores_creados,
            "correcciones": correcciones,
            "total": len(analisis.pasadas),
        }

        registrar_auditoria(
            {
                "usuario": usuario,
                "tipo_operacion": "IMPORTACION_COMPLETA",
                "tabla": None,
                "registro_id": None,
                "valores_anteriores": None,
                "valores_nuevos": resumen,
                "detalles": (
                    "Importación transaccional completada "
                    "antes del COMMIT."
                ),
            },
            conexion_bd,
        )

        # --------------------------------------------------------------
        # 7. COMMIT ÚNICO.
        # --------------------------------------------------------------

        conexion_bd.commit()

        # --------------------------------------------------------------
        # 8. Resumen final.
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
            # Si incluso rollback falla, mantenemos la excepción
            # original porque es la que explica el fallo de importación.
            pass

        raise


# ============================================================================
# ALIAS PÚBLICO
# ============================================================================


def confirmar_importacion(
    analisis: ResultadoAnalisis,
    resoluciones,
    usuario,
    conexion_bd,
) -> dict:
    """
    Alias interno para mantener una API clara dentro del módulo.
    """
    return confirmar_importacion_completa(
        analisis=analisis,
        resoluciones=resoluciones,
        usuario=usuario,
        conexion_bd=conexion_bd,
    )