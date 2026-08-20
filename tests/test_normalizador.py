import datetime

from normalizador import (
    normalizar_hora,
    normalizar_turno,
    determinar_fecha_operativa_y_calendario,
    resolver_turno_con_prioridad,
)


def test_numero_1_2_digitos_hora_en_punto():
    hora, fue_normalizada, error = normalizar_hora(5)
    assert hora == datetime.time(5, 0)
    assert fue_normalizada is True
    assert error is None


def test_texto_numerico_con_cero_a_la_izquierda():
    hora, fue_normalizada, error = normalizar_hora("05")
    assert hora == datetime.time(5, 0)
    assert fue_normalizada is True
    assert error is None


def test_numero_3_digitos_ultimos_2_son_minutos():
    hora, fue_normalizada, error = normalizar_hora(205)
    assert hora == datetime.time(2, 5)
    assert fue_normalizada is True
    assert error is None


def test_numero_4_digitos():
    hora, fue_normalizada, error = normalizar_hora(2149)
    assert hora == datetime.time(21, 49)
    assert fue_normalizada is True
    assert error is None


def test_texto_con_punto_y_coma_en_vez_de_dos_puntos():
    hora, fue_normalizada, error = normalizar_hora("00;52")
    assert hora == datetime.time(0, 52)
    assert fue_normalizada is True
    assert error is None


def test_hora_fuera_de_rango_es_error_critico():
    hora, fue_normalizada, error = normalizar_hora(26)
    assert hora is None
    assert fue_normalizada is False
    assert error == "Hora '26' inválida (fuera de rango 00-23)"


def test_datetime_time_pasa_tal_cual():
    original = datetime.time(14, 30)
    hora, fue_normalizada, error = normalizar_hora(original)
    assert hora == original
    assert fue_normalizada is False
    assert error is None


def test_string_vacio_es_sin_pasada_no_error():
    hora, fue_normalizada, error = normalizar_hora("")
    assert hora is None
    assert fue_normalizada is False
    assert error is None


def test_string_solo_espacios_es_sin_pasada():
    hora, fue_normalizada, error = normalizar_hora("   ")
    assert hora is None
    assert fue_normalizada is False
    assert error is None


def test_none_es_sin_pasada():
    hora, fue_normalizada, error = normalizar_hora(None)
    assert hora is None
    assert fue_normalizada is False
    assert error is None


# --- casos extra, no pedidos explícitamente pero cubren bordes reales ---

def test_texto_hhmm_normal_con_dos_puntos():
    hora, fue_normalizada, error = normalizar_hora("14:30")
    assert hora == datetime.time(14, 30)
    assert fue_normalizada is True
    assert error is None


def test_minutos_fuera_de_rango_es_error():
    hora, fue_normalizada, error = normalizar_hora("0165")  # 01:65
    assert hora is None
    assert fue_normalizada is False
    assert "fuera de rango" in error


def test_float_entero_de_excel_se_trata_como_entero():
    hora, fue_normalizada, error = normalizar_hora(205.0)
    assert hora == datetime.time(2, 5)
    assert fue_normalizada is True
    assert error is None


def test_texto_no_numerico_no_reconocido_es_error():
    hora, fue_normalizada, error = normalizar_hora("mediodia")
    assert hora is None
    assert fue_normalizada is False
    assert "no reconocido" in error


# --- FASE 5: normalizar_turno ---

def test_turno_variantes_diurno():
    for v in ["D", "DIA", "DÍA", "Diurno", "dia"]:
        turno, problema = normalizar_turno(v)
        assert turno == "D"
        assert problema is None


def test_turno_variantes_nocturno():
    for v in ["N", "NOCHE", "Nocturno", "n"]:
        turno, problema = normalizar_turno(v)
        assert turno == "N"
        assert problema is None


def test_turno_invalido_genera_error_critico():
    turno, problema = normalizar_turno("MADRUGADA")
    assert turno is None
    assert problema.tipo == "error_critico"
    assert problema.descripcion == "turno inválido"


def test_turno_vacio_o_none_genera_error_critico():
    for v in (None, "", "   "):
        turno, problema = normalizar_turno(v)
        assert turno is None
        assert problema.tipo == "error_critico"


# --- FASE 5: determinar_fecha_operativa_y_calendario ---

def test_turno_dia_misma_fecha():
    fecha_hoja = datetime.date(2026, 7, 1)
    fecha_op, fecha_cal = determinar_fecha_operativa_y_calendario(
        fecha_hoja, "D", datetime.time(11, 30)
    )
    assert fecha_op == fecha_hoja
    assert fecha_cal == fecha_hoja


def test_caso_real_villa_de_mayo_noche_cruza_medianoche():
    # Hoja "1-7 (N)", objetivo "C.D.I. Villa de Mayo": pasada 1 a las
    # 23:52 y pasada 2 a las 05:17, ambas con fecha_operativa = 1/7.
    fecha_hoja = datetime.date(2026, 7, 1)

    fecha_op1, fecha_cal1 = determinar_fecha_operativa_y_calendario(
        fecha_hoja, "N", datetime.time(23, 52)
    )
    assert fecha_op1 == datetime.date(2026, 7, 1)
    assert fecha_cal1 == datetime.date(2026, 7, 1)

    fecha_op2, fecha_cal2 = determinar_fecha_operativa_y_calendario(
        fecha_hoja, "N", datetime.time(5, 17)
    )
    assert fecha_op2 == datetime.date(2026, 7, 1)
    assert fecha_cal2 == datetime.date(2026, 7, 2)


def test_turno_invalido_en_determinar_fecha_lanza_error():
    try:
        determinar_fecha_operativa_y_calendario(
            datetime.date(2026, 7, 1), "X", datetime.time(10, 0)
        )
        assert False, "debía lanzar ValueError"
    except ValueError:
        pass


# --- FASE 5: prioridad turno celda vs. turno hoja ---

def test_prioridad_sin_turno_en_celda_usa_turno_de_hoja():
    turno, problema = resolver_turno_con_prioridad(None, "N", hoja="1-7 (N)")
    assert turno == "N"
    assert problema is None


def test_prioridad_turno_coincide_sin_advertencia():
    turno, problema = resolver_turno_con_prioridad("N", "N", hoja="1-7 (N)")
    assert turno == "N"
    assert problema is None


def test_prioridad_turno_contradice_gana_celda_y_advierte():
    turno, problema = resolver_turno_con_prioridad(
        "D", "N", hoja="1-7 (N)", objetivo="BARRIO X", fila_excel=7
    )
    assert turno == "D"
    assert problema.tipo == "advertencia"
    assert "D" in problema.descripcion and "N" in problema.descripcion


if __name__ == "__main__":
    import sys

    tests = [(nombre, funcion) for nombre, funcion in globals().items() if nombre.startswith("test_")]
    fallidos = 0
    for nombre, funcion in tests:
        try:
            funcion()
            print(f"OK   {nombre}")
        except AssertionError as e:
            fallidos += 1
            print(f"FAIL {nombre}: {e}")
    print()
    print(f"{len(tests) - fallidos}/{len(tests)} tests pasaron")
    sys.exit(1 if fallidos else 0)