"""Ejercicio 3 — Auditoría con Tests Unitarios e Integración Web.

TP Final COM 2 · EcoTech Solutions
===================================

Contexto
--------
Previo a la puesta en producción, hay que certificar la precisión del
algoritmo de cálculo de huella de carbono industrial y después integrarlo a
la tubería de datos que alimenta el panel web administrativo.

Resolví el ejercicio en dos capas:

* **Punto A — Auditoría (``test_ejercicio_03.py``):** la clase
  ``TestCalculoEmisiones`` valida la exactitud numérica de
  ``calcular_emisiones_carbono()`` y la elevación de ``ValueError`` ante
  consumos fuera de rango.
* **Punto B — Métricas y web:** ``obtener_metricas_consumo()`` procesa el
  historial de consumos por planta usando el algoritmo auditado, y
  ``vista_panel_sustentabilidad()`` (en ``vista_django.py``) arma el
  contexto y renderiza ``sustentabilidad/panel.html``.

Cómo está organizado el código
------------------------------
* ``ejercicio_03_emisiones.py`` (este archivo): algoritmo, métricas y demo.
  Solo librería estándar: corre sin Django instalado.
* ``vista_django.py``: la vista de Django (requiere ``pip install django``).
* ``sustentabilidad/panel.html``: la plantilla del panel.

Cómo ejecutar la demostración
-----------------------------
::

    python ejercicio_03_emisiones.py

Cómo correr los tests
---------------------
::

    python -m unittest test_ejercicio_03.py -v
"""

import json
from pathlib import Path
from typing import Any

# =============================================================================
# ALGORITMO BAJO AUDITORÍA (PUNTO A)
# =============================================================================
# Este es el algoritmo que EcoTech quiere certificar antes de producción.
# Su contrato: emisiones = consumo * factor, y ValueError si el consumo es
# negativo (un consumo negativo no tiene sentido físico ni contable).


def calcular_emisiones_carbono(
    consumo_kwh: float,
    factor_emision: float = 0.4,
) -> float:
    """Calcula las emisiones de CO2 equivalentes de un consumo eléctrico.

    Args:
        consumo_kwh: consumo eléctrico en kilovatios-hora. No puede ser
            negativo (cero es válido: planta apagada).
        factor_emision: kg de CO2e emitidos por kWh, según la matriz
            energética. Por defecto 0.4 (valor típico de red mixta).

    Returns:
        Las emisiones en kg de CO2e, redondeo flotante incluido.

    Raises:
        ValueError: si ``consumo_kwh`` es negativo.
    """
    if consumo_kwh < 0:
        raise ValueError(
            f"El consumo no puede ser negativo (recibí {consumo_kwh} kWh)"
        )
    return consumo_kwh * factor_emision


# =============================================================================
# PUNTO B — PROCESAMIENTO DE MÉTRICAS
# =============================================================================
def obtener_metricas_consumo(
    registros: list[dict[str, Any]],
) -> dict[str, Any]:
    """Procesa el historial de consumos y arma las métricas del panel.

    Cada registro de la tubería tiene la forma::

        {"planta": "Planta Norte", "consumo_kwh": 12500.0}

    Acumulo el consumo por planta y a cada subtotal le aplico el algoritmo
    ya auditado del Punto A. Los registros de una misma planta se suman, y
    el orden del detalle respeta la primera aparición de cada planta.

    Args:
        registros: historial de consumos por planta industrial.

    Returns:
        Un dict con las métricas listas para el panel::

            {
                "detalle_plantas": [
                    {"planta": ..., "consumo_kwh": ..., "emisiones_kg": ...},
                ],
                "total_consumo_kwh": ...,
                "total_emisiones_kg": ...,
                "planta_mayor_consumo": ...  # None si no hay registros
            }

    Raises:
        ValueError: si algún registro trae consumo negativo. NO capturo la
            excepción acá a propósito: el contrato del algoritmo auditado
            vale en toda la tubería, y un consumo inválido debe frenar el
            procesamiento (mejor un panel vacío que un panel con mentiras).
    """
    # Acumulador por planta: dict planta -> {"consumo_kwh", "emisiones_kg"}.
    acumulado: dict[str, dict[str, float]] = {}

    for registro in registros:
        planta = str(registro["planta"])
        consumo = float(registro["consumo_kwh"])
        # El algoritmo auditado valida y calcula: si el consumo es negativo,
        # el ValueError sube solo y corta todo el procesamiento.
        emision = calcular_emisiones_carbono(consumo)

        if planta not in acumulado:
            acumulado[planta] = {"consumo_kwh": 0.0, "emisiones_kg": 0.0}
        acumulado[planta]["consumo_kwh"] += consumo
        acumulado[planta]["emisiones_kg"] += emision

    detalle_plantas = [
        {"planta": planta, **totales} for planta, totales in acumulado.items()
    ]

    if detalle_plantas:
        # max() con key: si hay empate, se queda con la PRIMERA del detalle
        # (decisión documentada y testada).
        mayor = max(detalle_plantas, key=lambda fila: fila["consumo_kwh"])
        planta_mayor: str | None = mayor["planta"]
    else:
        planta_mayor = None

    return {
        "detalle_plantas": detalle_plantas,
        "total_consumo_kwh": sum(f["consumo_kwh"] for f in detalle_plantas),
        "total_emisiones_kg": sum(f["emisiones_kg"] for f in detalle_plantas),
        "planta_mayor_consumo": planta_mayor,
    }


def construir_contexto_panel(
    registros: list[dict[str, Any]],
) -> dict[str, Any]:
    """Arma el diccionario de contexto completo para la plantilla.

    Separé esta función de la vista por una razón práctica: así la lógica
    de armado del contexto se testea SIN Django, y la vista queda "delgada"
    (solo llama acá y renderiza).
    """
    contexto = obtener_metricas_consumo(registros)
    contexto["titulo"] = "Panel de Sustentabilidad — EcoTech Solutions"
    return contexto


# =============================================================================
# DATOS SIMULADOS DE LA TUBERÍA
# =============================================================================
# En producción esto vendría de la base de datos o de los medidores IoT.
# Para el TP lo simulo con una constante: el flujo es exactamente el mismo.
HISTORIAL_CONSUMOS: list[dict[str, Any]] = [
    {"planta": "Planta Norte", "consumo_kwh": 12500.0},
    {"planta": "Planta Sur", "consumo_kwh": 9800.5},
    {"planta": "Planta Norte", "consumo_kwh": 3200.0},
    {"planta": "Depósito Central", "consumo_kwh": 4100.0},
    {"planta": "Planta Sur", "consumo_kwh": 6150.0},
]


# =============================================================================
# BLOQUE DE DEMOSTRACIÓN
# =============================================================================
def _renderizar_con_django() -> str | None:
    """Intenta renderizar el panel con Django. Devuelve el HTML o None.

    Importo Django DENTRO de la función a propósito: así el módulo entero
    funciona sin Django instalado (la auditoría y las métricas no dependen
    de la web).
    """
    try:
        import django
        from django.conf import settings
        from django.test import RequestFactory

        from vista_django import vista_panel_sustentabilidad
    except ImportError:
        return None

    # Configuración mínima para que el motor de plantillas encuentre
    # "sustentabilidad/panel.html" en esta carpeta.
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

    respuesta = vista_panel_sustentabilidad(RequestFactory().get("/panel/"))
    return respuesta.content.decode("utf-8")


def demo_flujo_completo() -> None:
    """Auditoría express + métricas del panel + render web (si hay Django)."""
    print("=" * 66)
    print("TP FINAL COM 2 · Ejercicio 3 — Huella de carbono EcoTech")
    print("=" * 66)

    # ------------------------------------------------------------------
    # PASO 1: chequeo express del algoritmo antes de confiar en él.
    # ------------------------------------------------------------------
    print("\n[1] Auditoría express del algoritmo de emisiones:")
    print(f"  calcular_emisiones_carbono(100)      -> "
          f"{calcular_emisiones_carbono(100)} kg CO2e")
    print(f"  calcular_emisiones_carbono(100, 0.5) -> "
          f"{calcular_emisiones_carbono(100, 0.5)} kg CO2e")
    try:
        calcular_emisiones_carbono(-5)
    except ValueError as error:
        print(f"  calcular_emisiones_carbono(-5)       -> ValueError: {error}")
    print("  (la auditoría completa está en test_ejercicio_03.py)")

    # ------------------------------------------------------------------
    # PASO 2: proceso el historial de la tubería de datos.
    # ------------------------------------------------------------------
    metricas = obtener_metricas_consumo(HISTORIAL_CONSUMOS)
    print("\n[2] Métricas por planta:")
    for fila in metricas["detalle_plantas"]:
        print(f"  {fila['planta']:<16} {fila['consumo_kwh']:>10.1f} kWh"
              f"  ->  {fila['emisiones_kg']:>9.1f} kg CO2e")
    print(f"\n  Consumo total:        {metricas['total_consumo_kwh']:.1f} kWh")
    print(f"  Emisiones globales:   {metricas['total_emisiones_kg']:.1f} kg CO2e")
    print(f"  Mayor consumo:        {metricas['planta_mayor_consumo']}")

    # ------------------------------------------------------------------
    # PASO 3: el contexto que la vista le entrega a la plantilla.
    # ------------------------------------------------------------------
    contexto = construir_contexto_panel(HISTORIAL_CONSUMOS)
    print("\n[3] Contexto listo para 'sustentabilidad/panel.html':")
    print(json.dumps(contexto, indent=4, ensure_ascii=False))

    # ------------------------------------------------------------------
    # PASO 4: render real si Django está instalado; si no, aviso claro.
    # ------------------------------------------------------------------
    print("\n[4] Render web:")
    html = _renderizar_con_django()
    if html is not None:
        print(f"  vista_panel_sustentabilidad(request) -> HTTP 200 "
              f"({len(html)} caracteres de HTML)")
        print("  Primeras líneas del panel renderizado:")
        for linea in html.splitlines()[:8]:
            print(f"    {linea}")
    else:
        print("  Django no está instalado en esta máquina.")
        print("  Con 'pip install django' la vista renderiza "
              "sustentabilidad/panel.html con este mismo contexto.")
        print("  La plantilla vive en: sustentabilidad/panel.html")


if __name__ == "__main__":
    # Mismo guard que en los ejercicios anteriores: la demo solo corre al
    # ejecutar el archivo directo; los tests importan sin efectos de I/O.
    demo_flujo_completo()
