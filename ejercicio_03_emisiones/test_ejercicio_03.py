"""Tests unitarios del Ejercicio 3 — Auditoría e Integración Web.

TP Final COM 2 · EcoTech Solutions

Qué se testea
-------------
* **Punto A** (``TestCalculoEmisiones``): la clase de prueba que exige el
  enunciado — exactitud numérica con valores nominales y elevación de
  ``ValueError`` ante consumos fuera de rango.
* **Punto B** (``TestObtenerMetricasConsumo`` y ``TestContextoDelPanel``):
  el procesamiento del historial por planta y el armado del contexto.
* **Vista Django** (``TestVistaPanelSustentabilidad``): solo corre si
  Django está instalado (``skipUnless``); sin Django los tests se saltan
  solos y la suite sigue verde.

Cómo correrlos (desde esta carpeta)
-----------------------------------
::

    python -m unittest test_ejercicio_03.py -v
"""

import unittest
from pathlib import Path

from ejercicio_03_emisiones import (
    HISTORIAL_CONSUMOS,
    construir_contexto_panel,
    calcular_emisiones_carbono,
    obtener_metricas_consumo,
)

# -----------------------------------------------------------------------------
# Configuración mínima de Django (solo si está instalado): apunto el motor de
# plantillas a ESTA carpeta para que encuentre "sustentabilidad/panel.html".
# Todo va en un try/except ImportError: sin Django, la suite sigue corriendo.
# -----------------------------------------------------------------------------
try:
    import django
    from django.conf import settings
    from django.test import RequestFactory

    if not settings.configured:
        settings.configure(
            TEMPLATES=[{
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [Path(__file__).resolve().parent],
                "APP_DIRS": False,
                "OPTIONS": {},
            }],
            USE_TZ=True,
        )
        django.setup()
    DJANGO_DISPONIBLE = True
except ImportError:
    DJANGO_DISPONIBLE = False


# =============================================================================
# PUNTO A — auditoría del algoritmo de emisiones
# =============================================================================
class TestCalculoEmisiones(unittest.TestCase):
    """Casos de prueba exigidos por el enunciado para el algoritmo."""

    def test_consumo_nominal_con_factor_por_defecto(self) -> None:
        """100 kWh con el factor por defecto (0.4) emite 40 kg de CO2e."""
        self.assertAlmostEqual(calcular_emisiones_carbono(100), 40.0)

    def test_factor_por_defecto_es_0_4(self) -> None:
        """El contrato fija 0.4 como valor por defecto del factor."""
        import inspect
        firma = inspect.signature(calcular_emisiones_carbono)
        self.assertEqual(firma.parameters["factor_emision"].default, 0.4)

    def test_factor_personalizado(self) -> None:
        """100 kWh con factor 0.5 emiten 50 kg: el caller puede ajustarlo."""
        self.assertEqual(calcular_emisiones_carbono(100, 0.5), 50.0)

    def test_consumo_cero_es_valido(self) -> None:
        """Cero kWh significa planta apagada: 0 emisiones, sin excepción."""
        self.assertEqual(calcular_emisiones_carbono(0), 0.0)

    def test_valores_fraccionarios(self) -> None:
        """Comparo floats con assertAlmostEqual, NUNCA con == exacto.

        0.4 y 0.2 no tienen representación binaria exacta, así que el
        resultado puede traer colas de redondeo (ej: 6380.200000000001).
        assertAlmostEqual compara con tolerancia y evita falsos fallidos.
        """
        self.assertAlmostEqual(calcular_emisiones_carbono(10.5, 0.2), 2.1)

    def test_consumo_negativo_lanza_valueerror(self) -> None:
        """La regla del contrato: consumo negativo -> ValueError."""
        with self.assertRaises(ValueError):
            calcular_emisiones_carbono(-1)

    def test_el_error_menciona_el_valor_rechazado(self) -> None:
        """El mensaje del error informa el valor, para el log de auditoría."""
        with self.assertRaises(ValueError) as contexto:
            calcular_emisiones_carbono(-5)
        self.assertIn("negativo", str(contexto.exception))
        self.assertIn("-5", str(contexto.exception))


# =============================================================================
# PUNTO B — procesamiento de métricas
# =============================================================================
class TestObtenerMetricasConsumo(unittest.TestCase):
    """El pipeline que usa el algoritmo auditado."""

    def test_total_global_de_emisiones(self) -> None:
        metricas = obtener_metricas_consumo(HISTORIAL_CONSUMOS)
        # Norte: 15700 kWh, Sur: 15950.5, Depósito: 4100 -> 35750.5 kWh
        self.assertAlmostEqual(metricas["total_consumo_kwh"], 35750.5)
        self.assertAlmostEqual(metricas["total_emisiones_kg"], 35750.5 * 0.4)

    def test_planta_de_mayor_consumo(self) -> None:
        """Sur acumula 15950.5 kWh y supera a Norte por un margen chico."""
        metricas = obtener_metricas_consumo(HISTORIAL_CONSUMOS)
        self.assertEqual(metricas["planta_mayor_consumo"], "Planta Sur")

    def test_suma_registros_de_la_misma_planta(self) -> None:
        """Norte aparece dos veces en el historial: se acumulan."""
        metricas = obtener_metricas_consumo(HISTORIAL_CONSUMOS)
        norte = next(
            fila for fila in metricas["detalle_plantas"]
            if fila["planta"] == "Planta Norte"
        )
        self.assertAlmostEqual(norte["consumo_kwh"], 15700.0)
        self.assertAlmostEqual(norte["emisiones_kg"], 15700.0 * 0.4)

    def test_historial_vacio_devuelve_metricas_neutras(self) -> None:
        """Sin registros: totales en 0 y ninguna planta destacada."""
        metricas = obtener_metricas_consumo([])
        self.assertEqual(metricas["detalle_plantas"], [])
        self.assertEqual(metricas["total_consumo_kwh"], 0.0)
        self.assertIsNone(metricas["planta_mayor_consumo"])

    def test_consumo_negativo_propaga_el_valueerror(self) -> None:
        """El contrato del Punto A vale en toda la tubería: un registro
        inválido corta el procesamiento y sube la excepción."""
        registros = [
            {"planta": "Planta Norte", "consumo_kwh": 100.0},
            {"planta": "Planta Sur", "consumo_kwh": -50.0},
        ]
        with self.assertRaises(ValueError):
            obtener_metricas_consumo(registros)

    def test_empate_se_queda_con_la_primera_planta(self) -> None:
        """max() con empate devuelve la primera aparición (decisión
        documentada en el docstring)."""
        registros = [
            {"planta": "Planta A", "consumo_kwh": 100.0},
            {"planta": "Planta B", "consumo_kwh": 100.0},
        ]
        metricas = obtener_metricas_consumo(registros)
        self.assertEqual(metricas["planta_mayor_consumo"], "Planta A")


class TestContextoDelPanel(unittest.TestCase):
    """El armado del contexto corre SIN Django (por eso está separado)."""

    def test_contexto_incluye_metricas_y_titulo(self) -> None:
        contexto = construir_contexto_panel(HISTORIAL_CONSUMOS)
        self.assertIn("titulo", contexto)
        self.assertIn("Panel de Sustentabilidad", contexto["titulo"])
        self.assertIn("detalle_plantas", contexto)
        self.assertAlmostEqual(contexto["total_emisiones_kg"], 35750.5 * 0.4)


# =============================================================================
# VISTA DJANGO — solo corre con Django instalado
# =============================================================================
@unittest.skipUnless(
    DJANGO_DISPONIBLE,
    "requiere Django instalado (pip install django)",
)
class TestVistaPanelSustentabilidad(unittest.TestCase):
    """La vista renderiza la plantilla con el contexto procesado."""

    def setUp(self) -> None:
        # Importo acá adentro: si Django falta, la clase entera se saltea
        # antes de llegar a estos imports.
        from vista_django import vista_panel_sustentabilidad
        self.vista = vista_panel_sustentabilidad
        self.factory = RequestFactory()

    def test_responde_200_y_renderiza_el_panel(self) -> None:
        respuesta = self.vista(self.factory.get("/panel/"))
        self.assertEqual(respuesta.status_code, 200)

    def test_el_html_contiene_las_metricas_del_contexto(self) -> None:
        respuesta = self.vista(self.factory.get("/panel/"))
        html = respuesta.content.decode("utf-8")
        self.assertIn("Panel de Sustentabilidad", html)
        self.assertIn("Planta Sur", html)          # mayor consumo
        self.assertIn("14300.2", html)             # emisiones globales
        self.assertIn("35750.5", html)             # consumo total


if __name__ == "__main__":
    unittest.main()
