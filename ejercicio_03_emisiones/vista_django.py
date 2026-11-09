"""Vista de Django para el panel de sustentabilidad (Punto B).

TP Final COM 2 · EcoTech Solutions
===================================

Este archivo es el único del ejercicio que necesita Django instalado
(``pip install django``). Lo mantuve separado a propósito: así la auditoría
y las métricas del Punto A corren con librería estándar pura, y Django
entra solo en la capa web.

La vista es "delgada": no calcula nada, solo toma el contexto ya testeado
(``construir_contexto_panel``) y lo entrega a la plantilla
``sustentabilidad/panel.html``.
"""

from typing import Any

from ejercicio_03_emisiones import construir_contexto_panel, HISTORIAL_CONSUMOS

try:
    # Si Django no está instalado, la vista sigue existiendo pero al
    # invocarla avisa con un error claro en lugar de romper el import.
    from django.shortcuts import render
    DJANGO_DISPONIBLE = True
except ImportError:  # pragma: no cover
    render = None
    DJANGO_DISPONIBLE = False


def vista_panel_sustentabilidad(request: Any) -> Any:
    """Vista del panel administrativo de sustentabilidad.

    Invoque el procesamiento del historial de consumos (vía
    ``construir_contexto_panel`` -> ``obtener_metricas_consumo`` ->
    ``calcular_emisiones_carbono``) y devuelve la respuesta renderizada con
    la plantilla ``sustentabilidad/panel.html``.

    Args:
        request: el ``HttpRequest`` de Django (no lo uso directo, pero es
            el contrato de toda vista).

    Returns:
        La ``HttpResponse`` con el HTML del panel.
    """
    if not DJANGO_DISPONIBLE:
        raise RuntimeError(
            "Django no está instalado. Ejecutá 'pip install django' para "
            "usar la vista web."
        )
    contexto = construir_contexto_panel(HISTORIAL_CONSUMOS)
    return render(request, "sustentabilidad/panel.html", contexto)
