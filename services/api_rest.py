# =============================================================================
# VESP Organizations - API REST para integración con sistemas externos
# =============================================================================

import json
import sqlite3
import datetime
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
from socketserver import ThreadingMixIn
from database.db import DB_PATH
from services.reportes import obtener_objetivos_del_dia


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def _json_response(start_response, status_code: int, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]
    status_map = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error",
    }
    start_response(f"{status_code} {status_map.get(status_code, 'Error')}", headers)
    return [body]


def _parse_request_body(env):
    try:
        length = int(env.get("CONTENT_LENGTH", "0") or 0)
    except ValueError:
        length = 0

    body_bytes = env["wsgi.input"].read(length) if length > 0 else b""
    if not body_bytes:
        return {}

    try:
        return json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def contar_pasadas(fecha: str, objetivo_id: int, turno: str = None, supervisor_id: int = None) -> int:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    query = "SELECT COUNT(*) FROM pasadas WHERE fecha = ? AND objetivo_id = ?"
    params = [fecha, objetivo_id]
    if turno:
        query += " AND turno = ?"
        params.append(turno)
    if supervisor_id:
        query += " AND supervisor_id = ?"
        params.append(supervisor_id)
    cursor.execute(query, params)
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado


def obtener_estado_detallado(fecha: str, objetivo_id: int) -> dict:
    dia = contar_pasadas(fecha, objetivo_id, turno="diurno")
    noche = contar_pasadas(fecha, objetivo_id, turno="nocturno")
    if dia > 0 and noche > 0:
        estado = "Pasaron los dos"
    elif dia > 0:
        estado = "No pasó noche"
    elif noche > 0:
        estado = "No pasó día"
    else:
        estado = "No pasó nadie"
    return {
        "estado": estado,
        "pasadas_dia": dia,
        "pasadas_noche": noche,
    }


def _insertar_pasada(data: dict) -> dict:
    required = ["fecha", "hora", "turno", "objetivo_id"]
    if not all(k in data for k in required):
        return {"error": "Campos requeridos: fecha, hora, turno, objetivo_id"}

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id) VALUES (?, ?, ?, ?, ?)",
        (
            data["fecha"],
            data["hora"],
            data["turno"],
            int(data["objetivo_id"]),
            int(data.get("supervisor_id")) if data.get("supervisor_id") is not None else None,
        )
    )
    conexion.commit()
    conexion.close()
    return {"success": True, "id": cursor.lastrowid}


def _listar_objetivos(fecha: str) -> list:
    objetivos = obtener_objetivos_del_dia(fecha)
    resultado = []
    for obj_id, nombre, dias in objetivos:
        detalle = obtener_estado_detallado(fecha, obj_id)
        resultado.append({
            "id": obj_id,
            "nombre": nombre,
            "dias_semana": dias,
            "estado": detalle["estado"],
            "pasadas_dia": detalle["pasadas_dia"],
            "pasadas_noche": detalle["pasadas_noche"],
        })
    return resultado


def _dashboard_data(fecha: str) -> dict:
    objetivos = obtener_objetivos_del_dia(fecha)
    total = len(objetivos)
    cumplidos = 0
    criticos = 0
    por_turno = {"diurno": 0, "nocturno": 0}

    for obj_id, _, _ in objetivos:
        detalle = obtener_estado_detallado(fecha, obj_id)
        if detalle["pasadas_dia"] > 0 or detalle["pasadas_noche"] > 0:
            cumplidos += 1
        if detalle["pasadas_dia"] == 0 and detalle["pasadas_noche"] == 0:
            criticos += 1
        if detalle["pasadas_dia"] > 0:
            por_turno["diurno"] += 1
        if detalle["pasadas_noche"] > 0:
            por_turno["nocturno"] += 1

    pendientes = total - cumplidos
    porcentaje = int((cumplidos / total * 100) if total > 0 else 0)

    return {
        "fecha": fecha,
        "total_objetivos": total,
        "cumplidos": cumplidos,
        "pendientes": pendientes,
        "criticos": criticos,
        "porcentaje": porcentaje,
        "cumplidos_diurno": por_turno["diurno"],
        "cumplidos_nocturno": por_turno["nocturno"],
    }


def app(env, start_response):
    path = env.get("PATH_INFO", "")
    method = env.get("REQUEST_METHOD", "GET")
    query = parse_qs(env.get("QUERY_STRING", ""))
    fecha = query.get("fecha", [datetime.date.today().strftime("%Y-%m-%d")])[0]

    if path == "/api/objetivos" and method == "GET":
        return _json_response(start_response, 200, {
            "fecha": fecha,
            "objetivos": _listar_objetivos(fecha),
        })

    if path == "/api/dashboard" and method == "GET":
        return _json_response(start_response, 200, _dashboard_data(fecha))

    if path == "/api/pasadas" and method == "POST":
        data = _parse_request_body(env)
        resultado = _insertar_pasada(data)
        if resultado.get("error"):
            return _json_response(start_response, 400, resultado)
        return _json_response(start_response, 201, resultado)

    if path == "/api/equipo" and method == "GET":
        turno = query.get("turno", [None])[0]
        if not turno:
            return _json_response(start_response, 400, {"error": "Parámetro turno requerido"})
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute(
            """
                SELECT s1.nombre, s2.nombre
                FROM equipos e
                JOIN supervisores s1 ON e.supervisor1_id = s1.id
                JOIN supervisores s2 ON e.supervisor2_id = s2.id
                WHERE e.fecha = ? AND e.turno = ?
            """,
            (fecha, turno)
        )
        equipo = cursor.fetchone()
        conexion.close()
        if not equipo:
            return _json_response(start_response, 404, {"error": "Equipo no encontrado"})
        return _json_response(start_response, 200, {
            "fecha": fecha,
            "turno": turno,
            "supervisor1": equipo[0],
            "supervisor2": equipo[1],
        })

    if method == "OPTIONS":
        start_response("200 OK", [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type"),
        ])
        return [b""]

    return _json_response(start_response, 404, {"error": "Recurso no encontrado"})


def iniciar_api_rest(host: str = "127.0.0.1", port: int = 5000):
    def servidor():
        with make_server(host, port, app, server_class=ThreadingWSGIServer, handler_class=WSGIRequestHandler) as httpd:
            print(f"API REST iniciada en http://{host}:{port}")
            httpd.serve_forever()

    from threading import Thread
    hilo = Thread(target=servidor, daemon=True)
    hilo.start()
    return hilo
