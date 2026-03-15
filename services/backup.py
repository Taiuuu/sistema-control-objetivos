import shutil
import os
import datetime


def hacer_backup():
    if not os.path.exists("backups"):
        os.makedirs("backups")

    if not os.path.exists("seguridad.db"):
        return

    fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    nombre_backup = f"backups/seguridad_{fecha}.db"

    # Evitar duplicados si ya hay un backup de hoy
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    backups_hoy = [f for f in os.listdir("backups") if fecha_hoy in f]

    if backups_hoy:
        return

    shutil.copy2("seguridad.db", nombre_backup)
    print(f"Backup creado: {nombre_backup}")

    limpiar_backups_viejos()


def limpiar_backups_viejos(dias_a_mantener=30):
    if not os.path.exists("backups"):
        return

    ahora = datetime.datetime.now()
    for archivo in os.listdir("backups"):
        ruta = os.path.join("backups", archivo)
        fecha_modificacion = datetime.datetime.fromtimestamp(os.path.getmtime(ruta))
        dias_diferencia = (ahora - fecha_modificacion).days

        if dias_diferencia > dias_a_mantener:
            os.remove(ruta)
            print(f"Backup eliminado por antigüedad: {archivo}")