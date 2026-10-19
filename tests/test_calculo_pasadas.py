from datetime import date, datetime, time, timedelta

from services.pasadas.calculo_pasadas import (
    contar_pasadas_por_objetivo,
    fecha_calendario_de_turno,
    fecha_de_turno,
    indexar_pasadas_por_objetivo,
    mes_de_pasada,
    rango_datetime_de_mes,
    resumen_mensual_objetivo,
)


def test_fecha_de_turno_y_mes_en_fechas_normales_y_bordes():
    casos = [
        (datetime(2026, 10, 13, 9), "DIA", date(2026, 10, 13), (2026, 10)),
        (datetime(2026, 10, 14, 3), "NOCHE", date(2026, 10, 13), (2026, 10)),
        (
            datetime(2026, 10, 14, 6, 59, 59),
            "N",
            date(2026, 10, 13),
            (2026, 10),
        ),
        (
            datetime(2026, 10, 14, 7),
            "nocturno",
            date(2026, 10, 13),
            (2026, 10),
        ),
        (
            datetime(2026, 10, 14, 7, 59, 59),
            "N",
            date(2026, 10, 13),
            (2026, 10),
        ),
        (
            datetime(2026, 10, 14, 8),
            "N",
            date(2026, 10, 14),
            (2026, 10),
        ),
        (
            datetime(2026, 10, 31, 23),
            "NOCHE",
            date(2026, 10, 31),
            (2026, 10),
        ),
        (
            datetime(2026, 11, 1, 2),
            "NOCHE",
            date(2026, 10, 31),
            (2026, 10),
        ),
        (
            datetime(2027, 1, 1, 2),
            "N",
            date(2026, 12, 31),
            (2026, 12),
        ),
        (
            datetime(2024, 2, 29, 22),
            "N",
            date(2024, 2, 29),
            (2024, 2),
        ),
        (
            datetime(2024, 3, 1, 2),
            "N",
            date(2024, 2, 29),
            (2024, 2),
        ),
        (
            datetime(2025, 3, 1, 2),
            "N",
            date(2025, 2, 28),
            (2025, 2),
        ),
    ]

    for fecha_hora, turno, fecha_esperada, mes_esperado in casos:
        assert fecha_de_turno(fecha_hora, turno) == fecha_esperada
        assert mes_de_pasada(fecha_hora, turno) == mes_esperado


def test_pasadas_a_ambos_lados_de_medianoche_comparten_turno_noche():
    fechas_turno = {
        fecha_de_turno(datetime(2026, 10, 14, 23, 50), "NOCHE"),
        fecha_de_turno(datetime(2026, 10, 15, 2, 10), "NOCHE"),
    }

    assert fechas_turno == {date(2026, 10, 14)}


def test_rango_de_mes_particiona_tres_meses_sin_omisiones_ni_solapamientos():
    inicio, fin = rango_datetime_de_mes(2026, 8, turno_noche_cruza=True)[0], (
        rango_datetime_de_mes(2026, 10, turno_noche_cruza=True)[1]
    )
    ventanas = [
        rango_datetime_de_mes(anio, mes, turno_noche_cruza=True)
        for anio, mes in ((2026, 8), (2026, 9), (2026, 10))
    ]
    total = 0
    instante = inicio
    while instante < fin:
        turno = (
            "nocturno"
            if instante.time() >= time(19) or instante.time() < time(8)
            else "diurno"
        )
        mes_calculado = mes_de_pasada(instante, turno)
        coincidencias = sum(
            desde <= instante < hasta for desde, hasta in ventanas
        )
        assert coincidencias == 1
        assert mes_calculado in {(2026, 8), (2026, 9), (2026, 10)}
        total += 1
        instante += timedelta(hours=1)

    assert total == int((fin - inicio).total_seconds() / 3600)


def test_fechas_de_turno_de_excel_conservan_el_dia_de_la_hoja():
    assert fecha_calendario_de_turno(
        date(2026, 10, 31), time(2), "N"
    ) == date(2026, 11, 1)
    assert fecha_calendario_de_turno(
        date(2026, 10, 31), time(23), "N"
    ) == date(2026, 10, 31)
    assert fecha_calendario_de_turno(
        date(2026, 10, 31), time(7, 40), "N"
    ) == date(2026, 11, 1)


def test_ciclos_dia_noche_admiten_solapamientos_sin_inferir_turno():
    from services.pasadas.calculo_pasadas import hora_corresponde_a_turno
    from services.gestor_turnos import GestorTurnos

    assert hora_corresponde_a_turno(time(7, 40), "D")
    assert hora_corresponde_a_turno(time(7, 40), "N")
    assert hora_corresponde_a_turno(time(19, 30), "D")
    assert hora_corresponde_a_turno(time(19, 30), "N")
    assert hora_corresponde_a_turno(time(20, 30), "N")
    for hora in (time(7, 40), time(19, 30)):
        try:
            GestorTurnos.obtener_turno_en_hora(hora)
        except ValueError:
            pass
        else:
            raise AssertionError("No debe inferir el turno en horas superpuestas")


def test_conteo_por_objetivo_omite_duplicados_naturales_y_filtra_turno_mes():
    pasadas = [
        {
            "objetivo_id": 4,
            "fecha_hora": datetime(2026, 10, 31, 23, 15),
            "turno": "N",
            "supervisor_id": 2,
        },
        {
            "objetivo_id": 4,
            "fecha_hora": datetime(2026, 10, 31, 23, 15),
            "turno": "nocturno",
            "supervisor_id": 2,
        },
        {
            "objetivo_id": 4,
            "fecha_hora": datetime(2026, 11, 1, 2),
            "turno": "N",
            "supervisor_id": 2,
        },
        {
            "objetivo_id": 4,
            "fecha_hora": datetime(2026, 11, 1, 2),
            "turno": "N",
            "supervisor_id": 3,
        },
        {
            "objetivo_id": 4,
            "fecha_hora": datetime(2026, 11, 1, 9),
            "turno": "D",
            "supervisor_id": 2,
        },
        {
            "objetivo_id": 4,
            "fecha_hora": datetime(2026, 11, 1, 2),
            "turno": "N",
            "supervisor_id": 2,
        },
    ]

    assert contar_pasadas_por_objetivo(pasadas, 4, 2026, 10) == 3
    assert contar_pasadas_por_objetivo(pasadas, 4, 2026, 10, "N") == 3
    assert contar_pasadas_por_objetivo(pasadas, 4, 2026, 11) == 1
    assert contar_pasadas_por_objetivo(pasadas, 99, 2026, 10) == 0
    indice = indexar_pasadas_por_objetivo(pasadas, 2026, 10)
    assert indice[4]["nocturno"] == {date(2026, 10, 31)}
    assert indice[4]["diurno"] == set()


def test_vigencia_y_dias_semana_determinan_dias_esperados():
    esperados, fechas = resumen_mensual_objetivo(
        2026, 8, "2026-08-16", "2026-08-31", "1,2,3,4,5"
    )

    assert esperados == 11
    assert all(fecha >= date(2026, 8, 16) for fecha in fechas)
    assert all(fecha.isoweekday() <= 5 for fecha in fechas)


def test_fecha_de_turno_rechaza_zona_horaria_para_evitar_conversion_utc():
    fecha_con_zona = datetime.fromisoformat("2026-10-14T03:00:00+00:00")

    try:
        fecha_de_turno(fecha_con_zona, "N")
    except ValueError as error:
        assert "Argentina" in str(error)
    else:
        raise AssertionError("No debe convertir silenciosamente una fecha con zona")
