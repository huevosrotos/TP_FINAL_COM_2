"""Tests unitarios del Ejercicio 2 — Productos, Excepciones y Persistencia.

TP Final COM 2 · EcoTech Solutions

Qué se testea
-------------
* **Punto A**: validación de stock (constructor y setter), la excepción
  ``StockInvalidoError``, la herencia de ``PanelSolar`` y el polimorfismo
  de la ficha técnica.
* **Punto B**: ``GestorInventario`` — guardado en JSON (cantidad, contenido,
  rutas como str o Path) y la recarga del catálogo (round-trip).

Cómo correrlos (desde esta carpeta)
-----------------------------------
::

    python -m unittest test_ejercicio_02.py -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from ejercicio_02_inventario import (
    DispositivoEcologico,
    GestorInventario,
    PanelSolar,
    StockInvalidoError,
)


# =============================================================================
# PUNTO A — la excepción y el dominio
# =============================================================================
class TestStockInvalidoError(unittest.TestCase):
    """La excepción de negocio."""

    def test_es_subclase_de_exception(self) -> None:
        """Debe poder capturarse como cualquier excepción estándar."""
        self.assertTrue(issubclass(StockInvalidoError, Exception))

    def test_conserva_el_valor_recibido(self) -> None:
        """Guarda el valor que disparó el error, para informarlo después."""
        error = StockInvalidoError("stock mal", valor_recibido=-3)
        self.assertEqual(error.valor_recibido, -3)


class TestDispositivoEcologico(unittest.TestCase):
    """Validación de stock y comportamiento de la clase base."""

    def setUp(self) -> None:
        self.disp = DispositivoEcologico("Cargador solar portátil 20W", 45500.0, 30)

    def test_constructor_asigna_atributos(self) -> None:
        self.assertEqual(self.disp.nombre, "Cargador solar portátil 20W")
        self.assertEqual(self.disp.precio, 45500.0)
        self.assertEqual(self.disp.stock, 30)

    def test_stock_cero_es_valido(self) -> None:
        """Cero significa "sin stock": es un estado de inventario real."""
        disp = DispositivoEcologico("Producto agotado", 100.0, 0)
        self.assertEqual(disp.stock, 0)

    def test_stock_negativo_en_constructor_lanza_excepcion(self) -> None:
        with self.assertRaises(StockInvalidoError):
            DispositivoEcologico("Producto trampa", 100.0, -1)

    def test_asignacion_negativa_lanza_y_deja_el_stock_intacto(self) -> None:
        """El setter rechaza el valor y el stock previo NO se corrompe."""
        with self.assertRaises(StockInvalidoError):
            self.disp.stock = -5
        self.assertEqual(self.disp.stock, 30)

    def test_rechaza_stock_flotante_o_texto(self) -> None:
        """5.5 y "5" no son stock válido: la regla pide enteros."""
        for valor in (5.5, "5"):
            with self.subTest(valor=valor):
                with self.assertRaises(StockInvalidoError):
                    self.disp.stock = valor

    def test_rechaza_booleano_como_stock(self) -> None:
        """Trampa clásica: ``True`` es subclase de ``int`` y pasaría como 1."""
        with self.assertRaises(StockInvalidoError):
            self.disp.stock = True

    def test_ficha_tecnica_menciona_los_datos(self) -> None:
        ficha = self.disp.generar_ficha_tecnica()
        self.assertIn("Cargador solar portátil 20W", ficha)
        self.assertIn("30 unidades", ficha)

    def test_a_dict_incluye_el_tipo_de_clase(self) -> None:
        """La clave "tipo" permite reconstruir el objeto al leer el JSON."""
        datos = self.disp.a_dict()
        self.assertEqual(datos["tipo"], "DispositivoEcologico")
        self.assertEqual(datos["stock"], 30)

    def test_valor_inventario_en_stock(self) -> None:
        self.assertAlmostEqual(self.disp.valor_inventario_en_stock(), 45500.0 * 30)


class TestPanelSolar(unittest.TestCase):
    """Herencia, polimorfismo y atributos específicos."""

    def setUp(self) -> None:
        self.panel = PanelSolar(
            "Panel Solar EcoTech 450W", 289900.0, 12, 450.0, 21.5
        )

    def test_hereda_de_dispositivo_ecologico(self) -> None:
        self.assertTrue(issubclass(PanelSolar, DispositivoEcologico))
        self.assertIsInstance(self.panel, DispositivoEcologico)

    def test_guarda_los_atributos_especificos(self) -> None:
        self.assertEqual(self.panel.potencia_maxima_watts, 450.0)
        self.assertEqual(self.panel.eficiencia_porcentaje, 21.5)

    def test_la_validacion_de_stock_se_hereda(self) -> None:
        """La regla de negocio vive en la base y aplica a toda la familia."""
        with self.assertRaises(StockInvalidoError):
            PanelSolar("Panel trampa", 100.0, -1, 200.0, 15.0)

    def test_ficha_tecnica_es_polimorfica(self) -> None:
        """La ficha del panel incluye lo técnico y difiere de la de la base."""
        ficha = self.panel.generar_ficha_tecnica()
        self.assertIn("450.0 W", ficha)
        self.assertIn("21.5 %", ficha)
        base = DispositivoEcologico("Genérico", 1.0, 1).generar_ficha_tecnica()
        self.assertNotEqual(ficha, base)

    def test_a_dict_agrega_los_campos_tecnicos(self) -> None:
        datos = self.panel.a_dict()
        self.assertEqual(datos["tipo"], "PanelSolar")
        self.assertEqual(datos["potencia_maxima_watts"], 450.0)

    def test_energia_diaria_estimada(self) -> None:
        """450 W x 5 h x 21.5 % de eficiencia = 0.48375 kWh."""
        self.assertAlmostEqual(
            self.panel.energia_diaria_estimada_kwh(5.0), 0.48375, places=5
        )


# =============================================================================
# PUNTO B — persistencia
# =============================================================================
class TestGestorInventario(unittest.TestCase):
    """Serialización y recuperación del catálogo."""

    def setUp(self) -> None:
        self.gestor = GestorInventario()
        self.productos = [
            DispositivoEcologico("Cargador solar portátil 20W", 45500.0, 30),
            PanelSolar("Panel Solar EcoTech 450W", 289900.0, 12, 450.0, 21.5),
        ]
        # Escribo en un directorio temporal: los tests NUNCA ensucian la
        # carpeta del repo ni dependen de dónde se corran.
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / "catalogo_ecotech.json"

    def test_guardar_devuelve_la_cantidad_guardada(self) -> None:
        self.assertEqual(self.gestor.guardar_catalogo_json(self.productos, self.ruta), 2)

    def test_genera_un_json_valido_con_clave_tipo(self) -> None:
        self.gestor.guardar_catalogo_json(self.productos, self.ruta)
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.assertIsInstance(datos, list)
        self.assertEqual(datos[0]["tipo"], "DispositivoEcologico")
        self.assertEqual(datos[1]["tipo"], "PanelSolar")

    def test_acepta_ruta_como_string_o_como_path(self) -> None:
        """El método es flexible con el tipo de ruta que recibe."""
        n = self.gestor.guardar_catalogo_json(self.productos, str(self.ruta))
        self.assertEqual(n, 2)

    def test_lista_vacia_genera_json_vacio(self) -> None:
        n = self.gestor.guardar_catalogo_json([], self.ruta)
        self.assertEqual(n, 0)
        self.assertEqual(json.loads(self.ruta.read_text(encoding="utf-8")), [])

    def test_entrada_que_no_es_lista_lanza_typeerror(self) -> None:
        with self.assertRaises(TypeError):
            self.gestor.guardar_catalogo_json(self.productos[0], self.ruta)

    def test_cargar_reconstruye_las_instancias(self) -> None:
        """Round-trip: guardo, releo y recupero las clases y los valores."""
        self.gestor.guardar_catalogo_json(self.productos, self.ruta)
        recuperados = self.gestor.cargar_catalogo_json(self.ruta)
        self.assertEqual(len(recuperados), 2)
        self.assertIsInstance(recuperados[0], DispositivoEcologico)
        self.assertIsInstance(recuperados[1], PanelSolar)
        self.assertEqual(recuperados[1].stock, 12)
        self.assertEqual(recuperados[1].potencia_maxima_watts, 450.0)

    def test_crear_desde_dict_con_tipo_desconocido_lanza_valueerror(self) -> None:
        with self.assertRaises(ValueError):
            self.gestor.crear_desde_dict({"tipo": "TurbinasEolicas", "nombre": "X"})


if __name__ == "__main__":
    unittest.main()
