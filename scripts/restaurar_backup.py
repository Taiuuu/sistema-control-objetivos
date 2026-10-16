"""Utilidad CLI de emergencia para listar y restaurar copias sin Qt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.logging_config import configurar_logging
from core.configuracion import DB_PATH
from core.instancia import adquirir_bloqueo_instancia
from services.backup import listar_backups, restaurar_backup


def main() -> int:
    configurar_logging()
    parser = argparse.ArgumentParser(
        description="Lista y restaura copias SQLite verificadas de VESP."
    )
    parser.add_argument(
        "--restaurar",
        help="Índice mostrado (empezando en 1) o ruta al archivo de backup.",
    )
    argumentos = parser.parse_args()
    backups = listar_backups()
    if not backups:
        print("No hay copias disponibles.")
        return 1
    for indice, copia in enumerate(backups, 1):
        estado = "verificado" if copia["verificado"] else "NO verificado"
        print(
            f"{indice}. {copia['fecha']:%d-%m-%Y %H:%M:%S} "
            f"{copia['motivo']} {copia['tamaño']} bytes {estado} - {copia['path']}"
        )
    seleccion = argumentos.restaurar
    if not seleccion:
        seleccion = input("Índice de copia a restaurar (Enter para salir): ").strip()
        if not seleccion:
            return 0
    path = Path(seleccion)
    if path.is_file():
        elegido = path.resolve()
    else:
        try:
            copia = backups[int(seleccion) - 1]
        except (ValueError, IndexError):
            print("Selección inválida.", file=sys.stderr)
            return 2
        elegido = copia["path"]
        if not copia["verificado"]:
            print("La copia seleccionada no está verificada.", file=sys.stderr)
            return 2
    confirmacion = input(
        f"Esto reemplaza la base actual con {elegido.name}. "
        "Escribí RESTAURAR para continuar: "
    )
    if confirmacion != "RESTAURAR":
        print("Restauración cancelada.")
        return 0
    bloqueo = adquirir_bloqueo_instancia(str(DB_PATH))
    if bloqueo is None:
        print(
            "No se puede restaurar mientras otra instancia de VESP usa la base.",
            file=sys.stderr,
        )
        return 1
    try:
        resultado = restaurar_backup(elegido)
    except Exception as error:
        print(f"No se pudo restaurar: {error}", file=sys.stderr)
        return 1
    finally:
        bloqueo.unlock()
    print(f"Base restaurada correctamente: {resultado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
