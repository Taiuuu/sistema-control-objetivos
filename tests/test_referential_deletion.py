import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.exceptions import DatabaseError
from models.objetivos import (
    actualizar_objetivo,
    eliminar_objetivo,
    listar_objetivos,
)
from models.supervisores import eliminar_supervisor, listar_supervisores


def test_no_elimina_pasadas_al_borrar_objetivo(
    db_initialized, test_objetivo
):
    conexion = sqlite3.connect(db_initialized)
    try:
        conexion.execute(
            """
            INSERT INTO pasadas (fecha, objetivo_id)
            VALUES ('2026-01-01', ?)
            """,
            (test_objetivo["id"],),
        )
        conexion.commit()
    finally:
        conexion.close()

    with pytest.raises(DatabaseError, match="conservar el historial"):
        eliminar_objetivo(test_objetivo["id"])

    conexion = sqlite3.connect(db_initialized)
    try:
        assert conexion.execute(
            "SELECT COUNT(*) FROM pasadas WHERE objetivo_id = ?",
            (test_objetivo["id"],),
        ).fetchone()[0] == 1
        assert conexion.execute(
            "SELECT COUNT(*) FROM objetivos WHERE id = ?",
            (test_objetivo["id"],),
        ).fetchone()[0] == 1
    finally:
        conexion.close()

    conexion = sqlite3.connect(db_initialized)
    try:
        conexion.execute("PRAGMA foreign_keys=OFF")
        with pytest.raises(sqlite3.IntegrityError, match="pasadas asociadas"):
            conexion.execute(
                "DELETE FROM objetivos WHERE id = ?",
                (test_objetivo["id"],),
            )
        conexion.rollback()
    finally:
        conexion.close()


def test_no_elimina_supervisor_asociado_a_equipos(
    db_initialized, test_supervisor
):
    conexion = sqlite3.connect(db_initialized)
    try:
        conexion.execute(
            """
            INSERT INTO equipos (fecha, supervisor1_id)
            VALUES ('2026-01-01', ?)
            """,
            (test_supervisor["id"],),
        )
        conexion.commit()
    finally:
        conexion.close()

    with pytest.raises(DatabaseError, match="equipo"):
        eliminar_supervisor(test_supervisor["id"])

    conexion = sqlite3.connect(db_initialized)
    try:
        assert conexion.execute(
            "SELECT COUNT(*) FROM equipos WHERE supervisor1_id = ?",
            (test_supervisor["id"],),
        ).fetchone()[0] == 1
        assert conexion.execute(
            "SELECT COUNT(*) FROM supervisores WHERE id = ?",
            (test_supervisor["id"],),
        ).fetchone()[0] == 1
    finally:
        conexion.close()

    conexion = sqlite3.connect(db_initialized)
    try:
        conexion.execute("PRAGMA foreign_keys=OFF")
        with pytest.raises(sqlite3.IntegrityError, match="historial asociado"):
            conexion.execute(
                "DELETE FROM supervisores WHERE id = ?",
                (test_supervisor["id"],),
            )
        conexion.rollback()
    finally:
        conexion.close()


def test_registros_placeholder_no_aparecen_en_selectores_activos(db_initialized):
    conexion = sqlite3.connect(db_initialized)
    try:
        conexion.execute(
            """
            INSERT INTO supervisores (nombre, es_placeholder)
            VALUES ('Registro histórico incompleto - supervisor ID 900', 1)
            """
        )
        supervisor_id = conexion.execute(
            "SELECT id FROM supervisores WHERE es_placeholder = 1"
        ).fetchone()[0]
        conexion.execute(
            """
            INSERT INTO objetivos (
                nombre, activo, tipo_objetivo, pendiente_revision, es_placeholder
            ) VALUES ('Registro histórico incompleto - objetivo ID 900', 0, 'puntual', 1, 1)
            """
        )
        objetivo_id = conexion.execute(
            "SELECT id FROM objetivos WHERE pendiente_revision = 1"
        ).fetchone()[0]
        conexion.commit()
    finally:
        conexion.close()

    assert supervisor_id not in {
        supervisor.id for supervisor in listar_supervisores(solo_activos=True)
    }
    assert objetivo_id not in {
        objetivo.id for objetivo in listar_objetivos(solo_activos=True)
    }

    conexion = sqlite3.connect(db_initialized)
    try:
        with pytest.raises(
            sqlite3.IntegrityError,
            match="fichas históricas incompletas",
        ):
            conexion.execute(
                """
                INSERT INTO pasadas (fecha, objetivo_id, supervisor_id)
                VALUES ('2026-01-01', ?, ?)
                """,
                (objetivo_id, supervisor_id),
            )
    finally:
        conexion.close()


def test_editar_objetivo_incompleto_lo_convierte_en_ficha_activa(
    db_initialized,
):
    conexion = sqlite3.connect(db_initialized)
    try:
        cursor = conexion.execute(
            """
            INSERT INTO objetivos (
                nombre, activo, tipo_objetivo, pendiente_revision, es_placeholder
            ) VALUES ('Registro histórico incompleto - objetivo ID 901', 0, 'puntual', 1, 1)
            """
        )
        objetivo_id = cursor.lastrowid
        conexion.commit()
    finally:
        conexion.close()

    actualizar_objetivo(
        objetivo_id,
        "Objetivo recuperado",
        "2026-01-01",
        "1,2,3",
    )

    conexion = sqlite3.connect(db_initialized)
    try:
        assert conexion.execute(
            "SELECT activo, es_placeholder, pendiente_revision FROM objetivos WHERE id = ?",
            (objetivo_id,),
        ).fetchone() == (1, 0, 0)
    finally:
        conexion.close()
