"""Ejercicio 1 — Sanitización y Análisis Estadístico de Sensores.

TP Final COM 2 · EcoTech Solutions
==================================

Contexto del problema
---------------------
Los microcontroladores de EcoTech Solutions transmiten lecturas térmicas en
formato heterogéneo: textos con espacios indeseados (``" SENSOR-001 "``),
valores mezclados con unidades de medida (``"24.5C"``) y atributos
incompletos (sensores que no reportan su ubicación).

Este módulo resuelve el problema en dos capas bien separadas:

* **Punto A — Normalización:** ``limpiar_registro_sensor()`` toma UN registro
  crudo y devuelve un diccionario NUEVO, estandarizado y confiable.
* **Punto B — Monitoreo estadístico:** ``generar_resumen_sensores()`` toma la
  colección ya sanitizada por encima de un umbral y devuelve la tupla
  ``(lista_sensores_alerta, promedio_temperatura)``.

Separé "limpiar" de "analizar": cada función hace UNA sola cosa
(principio de responsabilidad única) y puede
probarse de forma independiente con tests unitarios.

Cómo ejecutar la demostración
-----------------------------
::

    python ejercicio_01_sensores.py

El bloque de demostración pide el umbral por teclado (con validación de
entrada) y termina imprimiendo el reporte consolidado en formato JSON.

Cómo correr los tests
---------------------
::

    python -m unittest test_ejercicio_01.py -v
"""

# =============================================================================
# IMPORTS
# =============================================================================
# ``json`` se usa SOLO en la capa de presentación (reporte legible al final).
# ``Any`` permite tipar diccionarios cuyos valores pueden ser de cualquier
# tipo: exactamente lo que ocurre con datos crudos heterogéneos.
# ``TypedDict`` documenta la "forma" de un diccionario con tipado estático.
import json
from typing import Any, TypedDict

# =============================================================================
# CONSTANTES DE MÓDULO
# =============================================================================
# Definí estos valores como constantes, no están "hardcodeadas" dentro de las
# funciones.
#   1. Existe UN único lugar para cambiar la política de valores por defecto.
#   2. El propio nombre de la constante documenta la intención del valor.

#: Ubicación que se asigna cuando el sensor no reporta ninguna.
UBICACION_POR_DEFECTO: str = "Ubicación no registrada"

#: Identificador de reserva cuando el registro crudo no trae ``sensor_id``.
ID_POR_DEFECTO: str = "SENSOR-DESCONOCIDO"

#: Sufijos de unidad que puede traer "pegada" una lectura (``"24.5C"``,
#: ``"98F"``). NO convertimos unidades (Fahrenheit a Celsius, por ejemplo);
# solo removemos el sufijo. Hacer la conversión sería
#: una extensión natural de este TP (ver README y guía de estudio).
SUFIJOS_UNIDAD: tuple[str, ...] = ("C", "F", "K")


# =============================================================================
# TIPOS PERSONALIZADOS
# =============================================================================
class RegistroLimpio(TypedDict):
    """Forma del diccionario que devuelve el Punto A.

    ``TypedDict`` describe la estructura esperada de un diccionario sin
    agregar costo en tiempo de ejecución: es tipado estático puro, lo que
    permite que el editor o ``mypy`` avisen si guardamos/leemos una clave
    con el tipo equivocado.

    Anotar los returns como ``dict[str, Any]`` también es correcto:
    la lógica no cambia.
    """

    sensor_id: str
    temperatura: float | None  # ``None`` significa "lectura irrecuperable".
    ubicacion: str


# =============================================================================
# FUNCIONES AUXILIARES PRIVADAS (HELPERS)
# =============================================================================
# El guion bajo inicial (``_``) es una convención de Python para señalar que
# una función es "interna" del módulo.


def _limpiar_texto(valor: Any) -> str:
    """Convierte cualquier valor a texto y le quita los espacios sobrantes.

    Args:
        valor: Valor crudo que llega del sensor (str, int, None, ...).

    Returns:
        El valor como ``str`` sin espacios al inicio ni al final.
        Si el valor es ``None`` devuelve una cadena vacía, lo que permite
        encadenar el resultado con ``or`` más adelante.
    """
    if valor is None:
        return ""
    # ``str()`` normaliza cualquier tipo a texto y ``.strip()`` recorta los
    # espacios de los extremos: "  hola  " -> "hola". Ojo: strip() NO quita
    # espacios del medio, ni tabulaciones internas: eso queda a propósito.
    return str(valor).strip()


def _parsear_temperatura(valor: Any) -> float | None:
    """Extrae el valor numérico de una lectura "sucia".

    Estrategia:

        1. Si el valor ya es numérico (``int``/``float``), se castea a
           ``float`` y listo.
        2. Si es texto, se recortan espacios, se unifica la coma decimal por punto,
           se quita el símbolo ``°`` y se descarta el sufijo de unidad (C/F/K).
        3. Si después de todo eso el texto no representa un número válido,
           se devuelve ``None`` en lugar de romper el programa: UNA lectura
           corrupta no debería arruinar el reporte de toda la planta
           (robustez ante datos sucios).

    Args:
        valor: Lectura cruda, por ejemplo ``" 24.5C "``, ``"29,9C"`` o ``22``.

    Returns:
        La temperatura como ``float``, o ``None`` si no se pudo interpretar.
    """
    # --- Caso 1: el valor ya es numérico -----------------------------------
    # ``bool`` es subclase de int en Python, pero un sensor nunca manda
    # True/False como temperatura, así que no necesitamos un caso especial.
    if isinstance(valor, (int, float)):
        return float(valor)

    # --- Caso 2: limpieza del texto -----------------------------------------
    texto = _limpiar_texto(valor)
    texto = texto.replace(",", ".").replace("°", "").upper()

    # Si el texto termina en un sufijo de unidad, lo removemos y volvemos a
    # recortar espacios por si la unidad venía separada: "24.5 C" -> "24.5".
    for sufijo in SUFIJOS_UNIDAD:
        if texto.endswith(sufijo):
            texto = texto[:-len(sufijo)].strip()
            break  # Solo puede terminar en UNA unidad; cortamos al primer hallazgo.

    # --- Caso 3: validación numérica controlada ------------------------------
    # Convertir texto a float lanza ``ValueError`` si el texto no es un
    # número. En lugar de dejar que la excepción rompa todo, la
    # "catcheamos" y la traducimos a un valor None que Python sabe interpretar.
    try:
        return float(texto)
    except ValueError:
        return None


# =============================================================================
# PUNTO A — NORMALIZACIÓN DE LECTURAS
# =============================================================================
def limpiar_registro_sensor(registro_raw: dict[str, Any]) -> RegistroLimpio:
    """Normaliza UN registro crudo de sensor al formato estandarizado.

    Transformaciones garantizadas sobre el diccionario de salida:

        * ``sensor_id``: texto sin espacios sobrantes (con identificador de
          reserva si el registro no lo trae o viene en blanco).
        * ``temperatura``: valor numérico ``float`` sin sufijos de unidad
          (``"24.5C"`` -> ``24.5``); ``None`` si la lectura es irrecuperable.
        * ``ubicacion``: texto recortado; si falta o está vacío se aplica un
          valor por defecto (``UBICACION_POR_DEFECTO``).
        * La función NO muta ``registro_raw``: construye y devuelve un
          diccionario NUEVO.
        * Si la entrada ni siquiera es un diccionario, se levanta un
          ``TypeError`` con mensaje claro: si algo va a fallar que falle rápido
          y explícito.
        * La ubicación faltante NO se completa con ``None`` sino con un
          texto legible: el reporte final lo van a leer personas que toman
          decisiones, y "Ubicación no registrada" es mejor que "null".

    Args:
        registro_raw: Diccionario crudo, por ejemplo::

            {"sensor_id": " SENSOR-001 ", "temperatura": "24.5C",
             "ubicacion": "Planta Norte"}

    Returns:
        Un diccionario NUEVO y estandarizado con las claves ``sensor_id``
        (str), ``temperatura`` (float | None) y ``ubicacion`` (str).

    Raises:
        TypeError: Si ``registro_raw`` no es un diccionario.

    Example:
        >>> limpiar_registro_sensor(
        ...     {"sensor_id": " SENSOR-001 ", "temperatura": "24.5C",
        ...      "ubicacion": "Planta Norte"})
        {'sensor_id': 'SENSOR-001', 'temperatura': 24.5,
         'ubicacion': 'Planta Norte'}
    """
    # --- Validación de entrada ----------------------------------------------
    # El enunciado promete diccionarios, pero "confiar y verificar" es más
    # barato que depurar un KeyError.
    if not isinstance(registro_raw, dict):
        raise TypeError(
            f"Se esperaba un dict y llegó {type(registro_raw).__name__}. "
            "Revisá cómo se construyen los registros crudos."
        )

    # --- sensor_id ------------------------------------------------------------
    # ``_limpiar_texto`` devuelve "" si falta la clave o viene en blanco; el
    # operador ``or`` aprovecha que "" es "falsy" para sustituirlo por el
    # identificador de reserva. Como si fuera un if/else.
    sensor_id = _limpiar_texto(registro_raw.get("sensor_id")) or ID_POR_DEFECTO

    # --- temperatura -----------------------------------------------------------
    # Toda la "suciedad" (espacios, sufijos, comas, símbolos) se resuelve
    # dentro del helper; acá solo decidimos dónde guardar el resultado.
    temperatura = _parsear_temperatura(registro_raw.get("temperatura"))

    # --- ubicacion ---------------------------------------------------------------
    # Mismo truco de ``or``: si la ubicación falta, es None, está vacía o
    # son solo espacios, aplicamos el valor por defecto seguro.
    ubicacion = _limpiar_texto(registro_raw.get("ubicacion")) or UBICACION_POR_DEFECTO

    # Devolvemos un diccionario NUEVO, el registro original queda intacto.
    return RegistroLimpio(
        sensor_id=sensor_id,
        temperatura=temperatura,
        ubicacion=ubicacion,
    )


# =============================================================================
# PUNTO B — MONITOREO Y MAPEO ESTADÍSTICO
# =============================================================================
def generar_resumen_sensores(
    lista_sensores_limpios: list[RegistroLimpio],
    umbral_temperatura: float,
) -> tuple[list[str], float]:
    """Calcula el resumen estadístico de la planta a partir de datos limpios.

    Recorre la colección de registros sanitizados por el Punto A y
    construye dos métricas para la toma de decisiones:

        1. Los ``sensor_id`` de los dispositivos cuya temperatura SUPERA el
           umbral (comparación ESTRICTA con ``>``: un valor exactamente igual
           al umbral no dispara alerta).
        2. El promedio térmico global de la planta, calculado solo con las
           lecturas válidas (las ``None`` se excluyen).

    Decisión sobre casos extremos:

        * Lista vacía (o con todas las lecturas inválidas): se devuelve
          ``([], 0.0)`` en lugar de lanzar ``ZeroDivisionError``. El reporte
          debe poder generarse siempre.

    Args:
        lista_sensores_limpios: Colección de diccionarios con la forma
            ``RegistroLimpio`` (salida del Punto A).
        umbral_temperatura: Valor límite en °C a partir del cual se
            considera que un sensor está en alerta.

    Returns:
        Una tupla ``(lista_sensores_alerta, promedio_temperatura)`` donde:

            * ``lista_sensores_alerta`` es una ``list[str]`` con los IDs de
              los sensores en alerta, en el orden en que llegaron.
            * ``promedio_temperatura`` es un ``float`` con el promedio
              térmico global. Se devuelve SIN redondear: redondear es una
              decisión de presentación y se hace al momento de imprimir.
              Los datos se deben toquetear lo menos posible mientras se procesan.

    Example:
        >>> sensores = [
        ...     {"sensor_id": "A", "temperatura": 20.0, "ubicacion": "X"},
        ...     {"sensor_id": "B", "temperatura": 30.0, "ubicacion": "Y"},
        ... ]
        >>> generar_resumen_sensores(sensores, 25.0)
        (['B'], 25.0)
    """
    # Acumuladores: listas que vamos llenando durante el recorrido.
    sensores_en_alerta: list[str] = []
    temperaturas_validas: list[float] = []

    for registro in lista_sensores_limpios:
        temperatura = registro.get("temperatura")

        # El Punto A garantiza temperatura float | None. Aun
        # así validamos: si alguien pasa datos que NO pasaron por la
        # sanitización, los salteamos en vez de romper el reporte.
        if temperatura is None:
            continue

        try:
            temperatura_num = float(temperatura)
        except (TypeError, ValueError):
            continue

        temperaturas_validas.append(temperatura_num)

        # ``>`` estricto: "superar el umbral" se interpreta como estar
        # ESTRICTAMENTE por encima. Esta convención podría haber sido
        # ``>=``.
        if temperatura_num > umbral_temperatura:
            sensores_en_alerta.append(
                str(registro.get("sensor_id", ID_POR_DEFECTO))
            )

    # Protección contra división por cero: ``sum([]) / len([])`` lanzaría
    # ZeroDivisionError. Si no hay lecturas válidas, el promedio es 0.0.
    if temperaturas_validas:
        promedio_temperatura = sum(temperaturas_validas) / len(temperaturas_validas)
    else:
        promedio_temperatura = 0.0

    # La función devuelve una TUPLA (y no una lista) porque representa un
    # registro fijo de dos valores con significados distintos: posición 0 =
    # alertas, posición 1 = promedio. La inmutabilidad de la tupla comunica
    # esa estructura.
    return sensores_en_alerta, promedio_temperatura


# =============================================================================
# CAPA DE PRESENTACIÓN (I/O CON EL USUARIO)
# =============================================================================
# Estas funciones NO contienen lógica de negocio: piden datos y muestran
# resultados. Mantenerlas separadas del cálculo permite cambiar la interfaz
# (consola -> JSON -> web) sin tocar las funciones del enunciado.


def leer_umbral_desde_teclado() -> float:
    """Pide el umbral de temperatura por consola hasta recibir un número.

    Implementa un bucle de validación: mientras la entrada no sea
    convertible a ``float``, se informa el error y se vuelve a preguntar.
    Se acepta coma decimal (``30,5``) además de punto (``30.5``), por ser
    la convención habitual en teclados.

    Returns:
        El umbral ingresado por el usuario como ``float`` (puede ser
        negativo: Por ejemplo, si se mide temperatura relativa).
    """
    while True:
        respuesta = input("Ingresá el umbral de alerta en °C (ej: 30.5): ")
        respuesta_normalizada = respuesta.strip().replace(",", ".")

        try:
            return float(respuesta_normalizada)
        except ValueError:
            # Mensaje de error amable + reintento, en lugar de dejar que la
            # excepción corte el programa a mitad de la demostración.
            print(f"  [!] '{respuesta}' no es un número válido. Intentá de nuevo.")


def imprimir_reporte_json(
    sensores_limpios: list[RegistroLimpio],
    sensores_en_alerta: list[str],
    promedio_temperatura: float,
    umbral_temperatura: float,
) -> None:
    """Imprime el reporte consolidado de la planta en formato JSON legible.

    El enunciado pide un "reporte consolidado para la toma de decisiones":
    JSON indentado es un formato que una persona puede leer y que un
    sistema posterior (dashboard, planilla) puede consumir sin re-procesar
    texto libre.

    Args:
        sensores_limpios: Registros ya normalizados (Punto A).
        sensores_en_alerta: IDs en alerta (posición 0 de la tupla del Punto B).
        promedio_temperatura: Promedio global (posición 1 de la tupla).
        umbral_temperatura: Umbral aplicado, para dejar constancia en el
            reporte de con qué criterio se detectaron las alertas.
    """
    # Redondeamos SOLO al mostrar (y no dentro de las funciones de cálculo):
    reporte = {
        "titulo": "Estado térmico de la planta — EcoTech Solutions",
        "umbral_aplicado_celsius": round(umbral_temperatura, 2),
        "total_sensores_monitoreados": len(sensores_limpios),
        "cantidad_en_alerta": len(sensores_en_alerta),
        "sensores_en_alerta": sensores_en_alerta,
        "promedio_temperatura_celsius": round(promedio_temperatura, 2),
        "sensores_normalizados": sensores_limpios,
    }
    # ``ensure_ascii=False`` conserva tildes y el símbolo ° tal como son;
    # ``indent=4`` produce el formato multilínea legible en consola.
    print(json.dumps(reporte, indent=4, ensure_ascii=False))


# =============================================================================
# BLOQUE DE DEMOSTRACIÓN — FLUJO COMPLETO
# =============================================================================
def demo_flujo_completo() -> None:
    """Ejecuta el flujo pedido por el enunciado.

    Los cuatro pasos del pipeline quedan a la vista para poder pausar la
    demostración y examinar la salida de cada etapa:

        [1] Datos crudos heterogéneos (como llegarían del sensor).
        [2] Sanitización registro por registro (Punto A).
        [3] Umbral definido por el operador + estadística (Punto B).
        [4] Reporte consolidado en JSON.
    """
    # ------------------------------------------------------------------
    # PASO 1: registros crudos. Se incluyen A PROPÓSITO los casos borde
    # del enunciado: espacios sobrantes, sufijos de unidad, coma decimal,
    # ubicación faltante y hasta una lectura corrupta ("n/d").
    # ------------------------------------------------------------------
    registros_crudos: list[dict[str, Any]] = [
        {"sensor_id": " SENSOR-001 ", "temperatura": "24.5C", "ubicacion": "Planta Norte"},
        {"sensor_id": "SENSOR-002", "temperatura": "31.8 C", "ubicacion": " Planta Sur "},
        {"sensor_id": " SENSOR-003 ", "temperatura": "29,9C", "ubicacion": ""},
        {"sensor_id": " SENSOR-004", "temperatura": " 35.2F "},
        {"sensor_id": "SENSOR-005", "temperatura": "n/d"},
        {"sensor_id": " SENSOR-006 ", "temperatura": "22", "ubicacion": "Depósito"},
        {"sensor_id": "   ", "temperatura": "33.0C", "ubicacion": "Planta Este"},
        {"sensor_id": "SENSOR-007", "temperatura": "26.4°C", "ubicacion": "Oficinas"},
    ]

    print("=" * 66)
    print("TP FINAL COM 2 · Ejercicio 1 — Sensores EcoTech Solutions")
    print("=" * 66)
    print("\n[1] Registros crudos recibidos de los sensores:")
    print(json.dumps(registros_crudos, indent=4, ensure_ascii=False))

    # ------------------------------------------------------------------
    # PASO 2: sanitización. Aplica la función del
    # Punto A a cada registro crudo. Mapeamos en forma pythónica una
    # transformación sobre una colección.
    # ------------------------------------------------------------------
    sensores_limpios = [limpiar_registro_sensor(r) for r in registros_crudos]
    print("\n[2] Registros ya normalizados (salida del Punto A):")
    print(json.dumps(sensores_limpios, indent=4, ensure_ascii=False))

    # ------------------------------------------------------------------
    # PASO 3: el operador define el umbral (con validación) y se calcula
    # el resumen estadístico con la función del Punto B.
    # ------------------------------------------------------------------
    print()
    umbral = leer_umbral_desde_teclado()
    sensores_en_alerta, promedio = generar_resumen_sensores(sensores_limpios, umbral)

    # ------------------------------------------------------------------
    # PASO 4: reporte consolidado para la toma de decisiones.
    # ------------------------------------------------------------------
    print("\n[3] Reporte consolidado de la planta:")
    imprimir_reporte_json(sensores_limpios, sensores_en_alerta, promedio, umbral)


if __name__ == "__main__":
    # ``demo_flujo_completo()`` corre SOLO cuando el archivo se ejecuta directamente
    # (``python ejercicio_01_sensores.py``). Si el módulo se importa (por
    # ejemplo, desde los tests), el bloque se ignora y no se pide nada por
    # teclado: así los tests pueden ejecutarse de forma automática.
    demo_flujo_completo()
