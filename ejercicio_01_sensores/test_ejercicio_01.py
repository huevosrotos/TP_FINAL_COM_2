"""Tests unitarios del Ejercicio 1 — Sanitización y Análisis de Sensores.

TP Final COM 2 · EcoTech Solutions
==================================

Qué se testea
-------------
* **Punto A** (``limpiar_registro_sensor``): el caso feliz del enunciado y
  los casos borde que motivan el ejercicio — espacios sobrantes, sufijos de
  unidad, coma decimal, atributos faltantes/vacíos, lecturas corruptas,
  no-mutación del registro original y validación del tipo de entrada.
* **Punto B** (``generar_resumen_sensores``): estructura de la tupla de
  retorno, detección de alertas, semántica estricta del umbral (``>``),
  promedio global, exclusión de lecturas inválidas y el caso de lista vacía.

Cómo correrlos (desde esta carpeta)
-----------------------------------
::

    python -m unittest test_ejercicio_01.py -v

Notas didácticas
----------------
* Cada test prueba UNA sola conducta y tiene un nombre que la describe:
  cuando un test falla, el nombre ya dice qué se rompió.
* Usamos la librería estándar (``unittest``) a propósito: no requiere
  instalar nada y enseña los conceptos de fixtures (``setUp``), aserciones
  específicas (``assertAlmostEqual``, ``assertIsNone``, ``assertRaises``)
  que se reutilizan en pytest y cualquier framework de testing.
"""

import unittest

from ejercicio_01_sensores import (
    ID_POR_DEFECTO,
    UBICACION_POR_DEFECTO,
    generar_resumen_sensores,
    limpiar_registro_sensor,
)


# =============================================================================
# PUNTO A — limpiar_registro_sensor
# =============================================================================
class TestLimpiarRegistroSensor(unittest.TestCase):
    """Conductas esperadas de la normalización de un registro crudo."""

    def test_ejemplo_del_enunciado(self) -> None:
        """El caso exacto que propone la consigna debe funcionar tal cual."""
        registro_raw = {
            "sensor_id": " SENSOR-001 ",
            "temperatura": "24.5C",
            "ubicacion": "Planta Norte",
        }
        esperado = {
            "sensor_id": "SENSOR-001",
            "temperatura": 24.5,
            "ubicacion": "Planta Norte",
        }
        self.assertEqual(limpiar_registro_sensor(registro_raw), esperado)

    def test_temperatura_con_espacios_y_unidad_separada(self) -> None:
        """' 30.1 C ' combina tres suciedades: espacios + unidad + espacios."""
        resultado = limpiar_registro_sensor({"temperatura": " 30.1 C "})
        self.assertEqual(resultado["temperatura"], 30.1)

    def test_temperatura_coma_decimal(self) -> None:
        """La coma decimal argentina ('29,9C') debe interpretarse bien."""
        resultado = limpiar_registro_sensor({"temperatura": "29,9C"})
        self.assertEqual(resultado["temperatura"], 29.9)

    def test_temperatura_con_simbolo_de_grado(self) -> None:
        """'26.4°C' trae el símbolo ° pegado: debe descartarse igual."""
        resultado = limpiar_registro_sensor({"temperatura": "26.4°C"})
        self.assertEqual(resultado["temperatura"], 26.4)

    def test_temperatura_ya_numerica_se_convierte_a_float(self) -> None:
        """Si el sensor manda un int, la salida igual debe ser float."""
        resultado = limpiar_registro_sensor({"temperatura": 22})
        self.assertEqual(resultado["temperatura"], 22.0)
        self.assertIsInstance(resultado["temperatura"], float)

    def test_temperatura_invalida_devuelve_none(self) -> None:
        """Una lectura corrupta ('n/d') no debe romper el programa."""
        resultado = limpiar_registro_sensor({"temperatura": "n/d"})
        self.assertIsNone(resultado["temperatura"])

    def test_temperatura_faltante_devuelve_none(self) -> None:
        """Un registro sin clave 'temperatura' tampoco debe romper nada."""
        resultado = limpiar_registro_sensor({"sensor_id": "SENSOR-002"})
        self.assertIsNone(resultado["temperatura"])

    def test_ubicacion_faltante_usa_valor_por_defecto(self) -> None:
        """Sin clave 'ubicacion' se aplica el valor por defecto seguro."""
        resultado = limpiar_registro_sensor(
            {"sensor_id": "S-1", "temperatura": "20C"}
        )
        self.assertEqual(resultado["ubicacion"], UBICACION_POR_DEFECTO)

    def test_ubicacion_vacia_o_en_blanco_usa_valor_por_defecto(self) -> None:
        """Vacío, solo espacios y None son equivalentes: falta la ubicación."""
        for cruda in ("", "   ", None):
            with self.subTest(ubicacion_recibida=cruda):
                resultado = limpiar_registro_sensor({"ubicacion": cruda})
                self.assertEqual(resultado["ubicacion"], UBICACION_POR_DEFECTO)

    def test_sensor_id_faltante_o_en_blanco_usa_valor_por_defecto(self) -> None:
        """Un identificador ausente o en blanco no debe dejar 'huérfanos'."""
        for crudo in (None, "   "):
            with self.subTest(sensor_id_recibido=crudo):
                resultado = limpiar_registro_sensor(
                    {"sensor_id": crudo, "temperatura": "20C"}
                )
                self.assertEqual(resultado["sensor_id"], ID_POR_DEFECTO)

    def test_no_muta_el_registro_original(self) -> None:
        """La función debe devolver un dict NUEVO, sin tocar el de entrada."""
        registro_raw = {
            "sensor_id": " SENSOR-001 ",
            "temperatura": "24.5C",
            "ubicacion": "Planta Norte",
        }
        copia_original = dict(registro_raw)
        limpiar_registro_sensor(registro_raw)
        self.assertEqual(registro_raw, copia_original)

    def test_entrada_que_no_es_diccionario_lanza_typeerror(self) -> None:
        """Pasar algo que no es un dict debe fallar rápido y con claridad."""
        with self.assertRaises(TypeError):
            limpiar_registro_sensor("SENSOR-001")  # type: ignore[arg-type]


# =============================================================================
# PUNTO B — generar_resumen_sensores
# =============================================================================
class TestGenerarResumenSensores(unittest.TestCase):
    """Conductas esperadas del monitoreo estadístico de la planta."""

    def setUp(self) -> None:
        """Fixture: sensores YA sanitizados por el Punto A.

        ``setUp`` corre antes de cada test, así cada prueba parte de un
        estado fresco y ninguna depende del orden de ejecución.
        """
        self.sensores = [
            {"sensor_id": "SENSOR-001", "temperatura": 24.5, "ubicacion": "Planta Norte"},
            {"sensor_id": "SENSOR-002", "temperatura": 31.8, "ubicacion": "Planta Sur"},
            {"sensor_id": "SENSOR-003", "temperatura": 28.9, "ubicacion": "Depósito"},
        ]

    def test_retorna_una_tupla_de_dos_elementos(self) -> None:
        """El contrato del enunciado es devolver una tupla (alertas, promedio)."""
        resultado = generar_resumen_sensores(self.sensores, 30.0)
        self.assertIsInstance(resultado, tuple)
        self.assertEqual(len(resultado), 2)

    def test_ids_que_superan_el_umbral(self) -> None:
        """Solo los sensores estrictamente por encima del umbral van a alerta."""
        alertas, _ = generar_resumen_sensores(self.sensores, 30.0)
        self.assertEqual(alertas, ["SENSOR-002"])

    def test_umbral_es_estricto(self) -> None:
        """30.0 con umbral 30.0 NO es alerta: 'superar' significa > (y no >=)."""
        sensores = [{"sensor_id": "S", "temperatura": 30.0, "ubicacion": "X"}]
        alertas, _ = generar_resumen_sensores(sensores, 30.0)
        self.assertEqual(alertas, [])

    def test_promedio_global(self) -> None:
        """El promedio usa todas las lecturas válidas, alerten o no."""
        _, promedio = generar_resumen_sensores(self.sensores, 30.0)
        self.assertAlmostEqual(promedio, (24.5 + 31.8 + 28.9) / 3)

    def test_lista_vacia_devuelve_valores_neutros(self) -> None:
        """Sin sensores no debe haber ZeroDivisionError: ([], 0.0)."""
        alertas, promedio = generar_resumen_sensores([], 30.0)
        self.assertEqual(alertas, [])
        self.assertEqual(promedio, 0.0)

    def test_lecturas_none_se_excluyen_de_las_metricas(self) -> None:
        """None no dispara alerta y tampoco distorsiona el promedio."""
        sensores = [
            {"sensor_id": "A", "temperatura": 20.0, "ubicacion": "X"},
            {"sensor_id": "B", "temperatura": None, "ubicacion": "Y"},
        ]
        alertas, promedio = generar_resumen_sensores(sensores, 15.0)
        self.assertEqual(alertas, ["A"])
        self.assertAlmostEqual(promedio, 20.0)

    def test_ningun_sensor_supera_el_umbral(self) -> None:
        """Con un umbral altísimo la lista de alertas queda vacía, pero el
        promedio se calcula igual."""
        alertas, promedio = generar_resumen_sensores(self.sensores, 100.0)
        self.assertEqual(alertas, [])
        self.assertAlmostEqual(promedio, (24.5 + 31.8 + 28.9) / 3)


if __name__ == "__main__":
    # Permite correr el archivo directamente: python test_ejercicio_01.py -v
    unittest.main()
