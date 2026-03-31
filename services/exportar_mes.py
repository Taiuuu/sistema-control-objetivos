# =============================================================================
# VESP Organizations - Sistema de Control de Objetivos
# Módulo de exportación/importación de datos mensuales (.vesp)
# =============================================================================

import json
import sqlite3
import calendar
import datetime
from database.db import DB_PATH


def exportar_mes_json(anio: int, mes: int, ruta: str) -> None:
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    primer_dia = f"{anio}-{mes:02d}-01"
    ultimo_dia = f"{anio}-{mes:02d}-{calendar.monthrange(anio, mes)[1]:02d}"

    cursor.execute("""
        SELECT p.id, p.fecha, p.hora, p.turno, p.objetivo_id, p.supervisor_id,
               o.nombre, s.nombre
        FROM pasadas p
        JOIN objetivos o ON p.objetivo_id = o.id
        JOIN supervisores s ON p.supervisor_id = s.id
        WHERE p.fecha >= ? AND p.fecha <= ?
        ORDER BY p.fecha, p.hora
    """, (primer_dia, ultimo_dia))
    pasadas_raw = cursor.fetchall()

    cursor.execute("""
        SELECT e.fecha, e.turno, e.supervisor1_id, e.supervisor2_id,
               s1.nombre, s2.nombre
        FROM equipos e
        JOIN supervisores s1 ON e.supervisor1_id = s1.id
        JOIN supervisores s2 ON e.supervisor2_id = s2.id
        WHERE e.fecha >= ? AND e.fecha <= ?
    """, (primer_dia, ultimo_dia))
    equipos_raw = cursor.fetchall()

    cursor.execute("SELECT fecha, nota FROM notas WHERE fecha >= ? AND fecha <= ?", (primer_dia, ultimo_dia))
    notas_raw = cursor.fetchall()

    obj_ids = list({p[4] for p in pasadas_raw})
    sup_ids = list({p[5] for p in pasadas_raw} | {e[2] for e in equipos_raw} | {e[3] for e in equipos_raw})

    objetivos = {}
    for oid in obj_ids:
        cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin, dias_semana FROM objetivos WHERE id = ?", (oid,))
        row = cursor.fetchone()
        if row:
            objetivos[oid] = {"id": row[0], "nombre": row[1], "fecha_inicio": row[2],
                               "fecha_fin": row[3], "dias_semana": row[4]}

    supervisores = {}
    for sid in sup_ids:
        cursor.execute("SELECT id, nombre FROM supervisores WHERE id = ?", (sid,))
        row = cursor.fetchone()
        if row:
            supervisores[sid] = {"id": row[0], "nombre": row[1]}

    conexion.close()

    datos = {
        "version": "1.0",
        "exportado": datetime.datetime.now().isoformat(),
        "periodo": {"anio": anio, "mes": mes},
        "objetivos": list(objetivos.values()),
        "supervisores": list(supervisores.values()),
        "pasadas": [
            {"fecha": p[1], "hora": p[2], "turno": p[3],
             "objetivo_id": p[4], "supervisor_id": p[5],
             "objetivo_nombre": p[6], "supervisor_nombre": p[7]}
            for p in pasadas_raw
        ],
        "equipos": [
            {"fecha": e[0], "turno": e[1],
             "supervisor1_id": e[2], "supervisor2_id": e[3],
             "supervisor1_nombre": e[4], "supervisor2_nombre": e[5]}
            for e in equipos_raw
        ],
        "notas": [{"fecha": n[0], "nota": n[1]} for n in notas_raw],
    }

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def importar_mes_json(ruta: str) -> str:
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    anio = datos["periodo"]["anio"]
    mes  = datos["periodo"]["mes"]
    primer_dia = f"{anio}-{mes:02d}-01"
    ultimo_dia = f"{anio}-{mes:02d}-{calendar.monthrange(anio, mes)[1]:02d}"

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    obj_id_map = {}
    for o in datos.get("objetivos", []):
        cursor.execute("SELECT id FROM objetivos WHERE nombre = ?", (o["nombre"],))
        row = cursor.fetchone()
        if row:
            obj_id_map[o["id"]] = row[0]
        else:
            cursor.execute("""
                INSERT INTO objetivos (nombre, fecha_inicio, fecha_fin, dias_semana)
                VALUES (?, ?, ?, ?)
            """, (o["nombre"], o.get("fecha_inicio"), o.get("fecha_fin"), o.get("dias_semana", "1,2,3,4,5")))
            obj_id_map[o["id"]] = cursor.lastrowid

    sup_id_map = {}
    for s in datos.get("supervisores", []):
        cursor.execute("SELECT id FROM supervisores WHERE nombre = ?", (s["nombre"],))
        row = cursor.fetchone()
        if row:
            sup_id_map[s["id"]] = row[0]
        else:
            cursor.execute("INSERT INTO supervisores (nombre) VALUES (?)", (s["nombre"],))
            sup_id_map[s["id"]] = cursor.lastrowid

    cursor.execute("DELETE FROM pasadas WHERE fecha >= ? AND fecha <= ?", (primer_dia, ultimo_dia))
    pasadas_importadas = 0
    for p in datos.get("pasadas", []):
        obj_local = obj_id_map.get(p["objetivo_id"])
        sup_local = sup_id_map.get(p["supervisor_id"])
        if obj_local and sup_local:
            cursor.execute("""
                INSERT INTO pasadas (fecha, hora, turno, objetivo_id, supervisor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (p["fecha"], p.get("hora"), p["turno"], obj_local, sup_local))
            pasadas_importadas += 1

    cursor.execute("DELETE FROM equipos WHERE fecha >= ? AND fecha <= ?", (primer_dia, ultimo_dia))
    equipos_importados = 0
    for e in datos.get("equipos", []):
        sup1_local = sup_id_map.get(e["supervisor1_id"])
        sup2_local = sup_id_map.get(e["supervisor2_id"])
        if sup1_local and sup2_local:
            cursor.execute("""
                INSERT INTO equipos (fecha, turno, supervisor1_id, supervisor2_id)
                VALUES (?, ?, ?, ?)
            """, (e["fecha"], e["turno"], sup1_local, sup2_local))
            equipos_importados += 1

    cursor.execute("DELETE FROM notas WHERE fecha >= ? AND fecha <= ?", (primer_dia, ultimo_dia))
    notas_importadas = 0
    for n in datos.get("notas", []):
        cursor.execute("INSERT INTO notas (fecha, nota) VALUES (?, ?)", (n["fecha"], n["nota"]))
        notas_importadas += 1

    conexion.commit()
    conexion.close()

    periodo_str = datetime.date(anio, mes, 1).strftime("%B %Y")
    return (
        f"Período: {periodo_str}\n"
        f"Pasadas importadas: {pasadas_importadas}\n"
        f"Equipos importados: {equipos_importados}\n"
        f"Notas importadas: {notas_importadas}"
    )