import sqlite3
import shutil
import csv
import datetime as dt
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.instancia import adquirir_bloqueo_instancia
from database import db as db_module
from services.backups import backup
from services.operaciones_seguras import (
    eliminar_pasadas_mes,
    obtener_vista_previa_borrado_mes,
)


def _crear_base(path: Path, valor: str = "original") -> None:
    conexion = sqlite3.connect(path)
    conexion.executescript(
        """
        CREATE TABLE pasadas (
            id INTEGER PRIMARY KEY, fecha TEXT, fecha_operativa TEXT,
            hora TEXT, objetivo_id INTEGER, supervisor_id INTEGER, dato TEXT
        );
        CREATE TABLE objetivos (id INTEGER PRIMARY KEY, nombre TEXT);
        CREATE TABLE supervisores (id INTEGER PRIMARY KEY, nombre TEXT);
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, username TEXT);
        """
    )
    conexion.execute(
        "INSERT INTO pasadas (fecha, fecha_operativa, dato) "
        "VALUES ('2026-07-01', '2026-07-01', ?)", (valor,)
    )
    conexion.execute("INSERT INTO objetivos (nombre) VALUES ('objetivo')")
    conexion.execute("INSERT INTO supervisores (nombre) VALUES ('supervisor')")
    conexion.execute("INSERT INTO usuarios (username) VALUES ('usuario')")
    conexion.commit()
    conexion.close()


@pytest.fixture
def base_segura(tmp_path, monkeypatch):
    db_path = tmp_path / "seguridad.db"
    backup_dir = tmp_path / "backups"
    _crear_base(db_path)
    monkeypatch.setattr(backup, "DB_PATH", db_path)
    monkeypatch.setattr(backup, "BACKUP_DIR", backup_dir)
    return db_path


def test_backup_creado_verificado_y_mismas_filas(base_segura):
    ruta = backup.crear_backup("manual")

    assert ruta.exists()
    assert backup.verificar_backup(ruta)
    with sqlite3.connect(base_segura) as original, sqlite3.connect(ruta) as copia:
        for tabla in backup.TABLAS_PRINCIPALES:
            assert original.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone() == (
                copia.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()
            )


def test_backup_truncado_se_detecta_y_descarta(base_segura):
    ruta = backup.crear_backup("manual")
    ruta.write_bytes(ruta.read_bytes()[:80])

    assert not backup.verificar_backup(ruta)
    assert not ruta.exists()


def test_restauracion_restaura_estado_y_guarda_pre_restauracion(base_segura):
    copia_objetivo = backup.crear_backup("manual")
    with sqlite3.connect(base_segura) as conexion:
        conexion.execute("UPDATE pasadas SET dato='nuevo'")

    backup.restaurar_backup(copia_objetivo)

    with sqlite3.connect(base_segura) as conexion:
        assert conexion.execute("SELECT dato FROM pasadas").fetchone() == ("original",)
    assert any(item["motivo"] == "pre_restauracion" for item in backup.listar_backups())


def test_fallo_a_mitad_restauracion_deja_base_actual_intacta(base_segura, monkeypatch):
    copia_objetivo = backup.crear_backup("manual")
    with sqlite3.connect(base_segura) as conexion:
        conexion.execute("UPDATE pasadas SET dato='estado actual'")
    real_replace = backup.os.replace
    fallo_emitido = False

    def reemplazo_controlado(origen, destino):
        nonlocal fallo_emitido
        if str(origen).endswith(".restaurando") and not fallo_emitido:
            fallo_emitido = True
            raise OSError("fallo inducido")
        return real_replace(origen, destino)

    monkeypatch.setattr(backup.os, "replace", reemplazo_controlado)
    with pytest.raises(backup.BackupError):
        backup.restaurar_backup(copia_objetivo)

    with sqlite3.connect(base_segura) as conexion:
        assert conexion.execute("SELECT dato FROM pasadas").fetchone() == (
            "estado actual",
        )


def test_restauracion_funciona_si_la_base_actual_no_existe(base_segura, monkeypatch):
    copia = backup.crear_backup("manual")
    destino = base_segura.parent / "base-inexistente.db"
    monkeypatch.setattr(backup, "DB_PATH", destino)

    assert backup.restaurar_backup(copia) == destino.resolve()
    with sqlite3.connect(destino) as conexion:
        assert conexion.execute("SELECT dato FROM pasadas").fetchone() == ("original",)


def test_integrity_check_detecta_base_dañada(tmp_path):
    corrupta = tmp_path / "corrupta.db"
    corrupta.write_bytes(b"esto no es una base sqlite truncada")

    valida, errores = db_module.verificar_integridad(str(corrupta))

    assert not valida
    assert errores


def test_retencion_limpia_diarios_y_respeta_edades_y_ultimo(base_segura):
    carpeta = backup.BACKUP_DIR
    carpeta.mkdir(parents=True)
    for dia in range(1, 17):
        nombre = f"vesp_202601{dia:02d}_120000_diario.db"
        shutil.copy2(base_segura, carpeta / nombre)
    viejo_restauracion = carpeta / "vesp_20260801_120000_pre_restauracion.db"
    viejo_manual = carpeta / "vesp_20250101_120000_manual.db"
    actual_manual = carpeta / f"vesp_{datetime.now():%Y%m%d_%H%M%S}_manual.db"
    shutil.copy2(base_segura, viejo_restauracion)
    shutil.copy2(base_segura, viejo_manual)
    shutil.copy2(base_segura, actual_manual)

    backup.limpiar_backups(datetime.now())

    restantes_diarios = list(carpeta.glob("*_diario.db"))
    assert len(restantes_diarios) == 14
    assert not viejo_restauracion.exists()
    assert not viejo_manual.exists()

    solo = carpeta / "vesp_20200101_120000_manual.db"
    for item in carpeta.glob("vesp_*.db"):
        item.unlink()
    shutil.copy2(base_segura, solo)
    backup.limpiar_backups()
    assert solo.exists()


def test_retencion_90_dias_para_importacion_y_borrado(base_segura):
    carpeta = backup.BACKUP_DIR
    carpeta.mkdir(parents=True)
    ahora = dt.datetime(2026, 10, 1, 12)
    actuales = []
    vencidos = []
    for motivo in ("pre_importacion", "pre_borrado_mes"):
        reciente = carpeta / f"vesp_20260704_120000_{motivo}.db"
        vencido = carpeta / f"vesp_20260702_120000_{motivo}.db"
        shutil.copy2(base_segura, reciente)
        shutil.copy2(base_segura, vencido)
        actuales.append(reciente)
        vencidos.append(vencido)
    ultimo = carpeta / "vesp_20261001_120000_manual.db"
    shutil.copy2(base_segura, ultimo)

    backup.limpiar_backups(ahora)

    assert all(path.exists() for path in actuales)
    assert all(not path.exists() for path in vencidos)
    assert ultimo.exists()


def test_backup_memoria_usa_su_tamano_y_no_el_de_db_path(tmp_path, monkeypatch):
    ruta_falsa_grande = tmp_path / "base-grande.db"
    ruta_falsa_grande.write_bytes(b"x" * 1_000_000)
    monkeypatch.setattr(backup, "DB_PATH", ruta_falsa_grande)
    monkeypatch.setattr(backup, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(
        backup.shutil, "disk_usage",
        lambda _: SimpleNamespace(total=100_000, used=0, free=100_000),
    )
    conexion = sqlite3.connect(":memory:")
    conexion.executescript(
        "CREATE TABLE pasadas (id INTEGER);"
        "CREATE TABLE objetivos (id INTEGER);"
        "CREATE TABLE supervisores (id INTEGER);"
        "CREATE TABLE usuarios (id INTEGER);"
    )

    try:
        copia = backup.crear_backup("manual", conexion)
        assert backup.verificar_backup(copia)
    finally:
        conexion.close()


def test_cerrar_conexiones_de_no_cierra_otras_bases(tmp_path):
    primera_ruta = tmp_path / "primera.db"
    segunda_ruta = tmp_path / "segunda.db"
    primera = db_module.sqlite3.connect(primera_ruta)
    segunda = db_module.sqlite3.connect(segunda_ruta)

    db_module.cerrar_conexiones_de(primera_ruta)

    with pytest.raises(sqlite3.ProgrammingError):
        primera.execute("SELECT 1")
    assert segunda.execute("SELECT 1").fetchone() == (1,)
    segunda.close()


def test_importacion_aborta_si_falla_backup(monkeypatch):
    from services.importador import importacion

    analisis = SimpleNamespace(pasadas=[SimpleNamespace(accion="nueva")])
    conexion = MagicMock()
    conexion.in_transaction = False
    monkeypatch.setattr(importacion, "_validar_analisis", lambda *_: None)
    monkeypatch.setattr(
        importacion, "crear_backup", lambda *_, **__: (_ for _ in ()).throw(
            OSError("sin espacio")
        )
    )

    with pytest.raises(OSError, match="sin espacio"):
        importacion.confirmar_importacion_completa(
            analisis, object(), None, conexion
        )
    conexion.execute.assert_not_called()


def test_borrado_mes_requiere_confirmacion_y_backup(base_segura, monkeypatch):
    conexion = sqlite3.connect(base_segura)
    import services.operaciones_seguras as operaciones
    backup_previo = MagicMock(side_effect=OSError("backup fallido"))
    monkeypatch.setattr(operaciones, "crear_backup", backup_previo)
    vista = obtener_vista_previa_borrado_mes(conexion, 2026, 7)
    assert vista["cantidad"] == 1

    with pytest.raises(ValueError):
        eliminar_pasadas_mes(conexion, 2026, 7, "07-2025")
    backup_previo.assert_not_called()

    with pytest.raises(OSError, match="backup fallido"):
        eliminar_pasadas_mes(conexion, 2026, 7, "07-2026")
    assert conexion.execute("SELECT COUNT(*) FROM pasadas").fetchone()[0] == 1
    conexion.close()


def test_instancia_unica_bloquea_segundo_proceso(tmp_path):
    ruta = str(tmp_path / "seguridad.db")
    primero = adquirir_bloqueo_instancia(ruta)
    assert primero is not None
    try:
        assert adquirir_bloqueo_instancia(ruta) is None
    finally:
        primero.unlock()


def test_schema_version_se_crea_una_sola_vez(tmp_path, monkeypatch):
    ruta = tmp_path / "schema.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(ruta))

    db_module.crear_base_datos()
    with sqlite3.connect(ruta) as conexion:
        fecha_original = conexion.execute(
            "SELECT fecha_aplicacion FROM schema_version WHERE version = 2"
        ).fetchone()[0]
    db_module.crear_base_datos()

    with sqlite3.connect(ruta) as conexion:
        filas = conexion.execute("SELECT version, fecha_aplicacion FROM schema_version").fetchall()
    assert filas == [(2, fecha_original)]


def test_conexion_aplica_pragmas_y_exporta_csv_con_bom(base_segura, tmp_path, monkeypatch):
    ruta_original = db_module.DB_PATH
    db_module.DB_PATH = str(base_segura)
    conexion = db_module.conectar()
    try:
        assert conexion.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conexion.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conexion.execute("PRAGMA synchronous").fetchone()[0] == 1
        assert conexion.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        from services.importador import importacion
        monkeypatch.setattr(importacion, "EXPORTS_DIR", tmp_path / "exports")

        importacion._exportar_pasadas_seguridad(
            conexion, [{"fecha": "2026-07-01"}]
        )
    finally:
        conexion.close()
        db_module.DB_PATH = ruta_original

    archivo = tmp_path / "exports" / "pasadas_2026-07.csv"
    assert archivo.read_bytes().startswith(b"\xef\xbb\xbf")
    with archivo.open(encoding="utf-8-sig", newline="") as csv_file:
        assert next(csv.reader(csv_file))[0] == "id"
