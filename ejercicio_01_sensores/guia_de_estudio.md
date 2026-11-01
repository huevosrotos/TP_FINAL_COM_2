# Guía de estudio — Ejercicio 1 (Sensores)

> **TP Final COM 2 · EcoTech Solutions**

Diez preguntas de repaso estilo parcial. Pensá tu respuesta primero y después
desplegá la solución clickeando en **Ver respuesta**.

---

### 1. ¿Por qué `limpiar_registro_sensor()` devuelve un diccionario nuevo en vez de modificar el que recibe?

<details>
<summary>Ver respuesta</summary>

Porque modificar el parámetro recibido sería un **efecto secundario**
(side effect): el dato original del microcontrolador cambiaría sin que el
llamador lo sepa. Devolver un dict nuevo hace que la función sea más fácil
de razonar, de reutilizar y de testear (hay un test específico,
`test_no_muta_el_registro_original`, que garantiza esta conducta). En
general: preferir funciones "puras" que reciben datos y devuelven datos,
sin tocar nada por fuera.
</details>

---

### 2. ¿Qué hace exactamente `str.strip()` y por qué no alcanza solo con él para limpiar `" 24.5 C "`?

<details>
<summary>Ver respuesta</summary>

`strip()` elimina los espacios **solo de los extremos** de la cadena: los
espacios del medio quedan intactos. Con `" 24.5 C "` obtendríamos
`"24.5 C"`, que todavía no es convertible a float. Por eso el módulo hace
un pipeline de limpieza: recortar espacios → unificar coma decimal → quitar
`°` → quitar el sufijo de unidad → volver a recortar (por si la unidad
estaba separada por un espacio). Solo después se intenta la conversión.
</details>

---

### 3. ¿Por qué la temperatura se guarda como `float` y no como `str`? ¿Qué se rompería si la dejamos como texto?

<details>
<summary>Ver respuesta</summary>

Porque el objetivo final es **hacer matemática**: promediar y comparar con
un umbral. Con strings no existen esas operaciones (`"24.5" > "30"` compara
alfabéticamente y `sum(["24.5", "31.8"])` lanza `TypeError`). Además,
guardar el tipo correcto en la capa de limpieza hace que el contrato entre
el Punto A y el Punto B sea explícito: quien recibe la lista limpia ya sabe
que puede operar numéricamente sin volver a convertir nada.
</details>

---

### 4. ¿Qué es un "valor por defecto seguro" y por qué no se usa `None` como ubicación por defecto?

<details>
<summary>Ver respuesta</summary>

Es un valor de reemplazo que: (a) mantiene el tipo esperado por el resto
del sistema (aquí, texto), y (b) comunica el motivo de la ausencia de forma
legible. El reporte lo leen personas que toman decisiones: ver
`"Ubicación no registrada"` es inmediatamente comprensible, mientras que un
`null` exige que cada lector (humano o programa) decida qué significa.
Además, con un texto garantizamos que cualquier código que espere un `str`
puede usar el campo sin chequear si es `None` primero.
</details>

---

### 5. ¿Por qué `generar_resumen_sensores()` devuelve una tupla y no un diccionario? ¿Cuándo convendría cada uno?

<details>
<summary>Ver respuesta</summary>

Una tupla de dos posiciones comunica "un registro fijo de dos valores con
significados por posición": `(alertas, promedio)`. Es exactamente lo que
pide el enunciado, es inmutable y es liviana. Un diccionario convendría si
el resultado tuviera muchas claves, si las claves pudieran crecer con el
tiempo (por ejemplo `{"alertas": ..., "promedio": ..., "maximo": ...}`) o
si quisiéramos acceder por nombre (`resumen["promedio"]`) para no depender
del orden. Regla práctica: pocos valores fijos y conocidos → tupla;
colección de resultados con nombre → dict.
</details>

---

### 6. ¿Por qué la comparación contra el umbral usa `>` y no `>=`? ¿Qué cambiaría con `>=`?

<details>
<summary>Ver respuesta</summary>

El enunciado dice que alertan los sensores que "**superan**" el umbral:
superar es estar estrictamente por encima, por eso `>`. Con `>=` un sensor
exactamente en el valor límite (30.0 con umbral 30.0) también dispararía
alerta. Ninguna de las dos es "la correcta" en abstracto: lo importante es
elegir una convención, **documentarla en el docstring** y **testearla**
(existe `test_umbral_es_estricto` justamente para fijar esa decisión).
</details>

---

### 7. ¿Qué pasaría si `generar_resumen_sensores()` recibiera una lista vacía sin la guarda del final, y cómo lo resuelve el código?

<details>
<summary>Ver respuesta</summary>

`sum([])` es `0` y `len([])` es `0`, así que la división
`0 / 0` lanzaría `ZeroDivisionError` y el reporte completo se caería. El
código lo resuelve con una guarda: si `temperaturas_validas` está vacía,
el promedio se define como `0.0` y la función devuelve `([], 0.0)`. Es una
decisión documentada en el docstring y testada con
`test_lista_vacia_devuelve_valores_neutros`: el reporte debe poder
generarse siempre.
</details>

---

### 8. ¿Por qué las lecturas `None` se excluyen del promedio en lugar de contarlas como 0?

<details>
<summary>Ver respuesta</summary>

Porque `None` significa "no sé la temperatura", no "la temperatura es
cero". Contarlas como 0 introduciría un sesgo artificial: con un sensor
corrupto y tres a 30 °C, el promedio bajaría a 22.5 °C, un número que no
representa a ninguna planta real. Excluir las inválidas y promediar solo
las válidas es la convención estadística honesta; el costo es aceptable: la
cantidad de lecturas que integran el promedio puede ser menor a la cantidad
de sensores.
</details>

---

### 9. ¿Cuál es el rol de `if __name__ == "__main__":` al final del módulo?

<details>
<summary>Ver respuesta</summary>

Es el **guard de ejecución directa**: el bloque solo corre cuando el
archivo se ejecuta como programa principal (`python ejercicio_01_sensores.py`),
porque en ese caso Python le asigna a la variable `__name__` el valor
`"__main__"`. Si el módulo se importa (por ejemplo desde los tests),
`__name__` vale `"ejercicio_01_sensores"` y el bloque se ignora: los tests
corren sin pedir nada por teclado y sin imprimir la demo. Sin ese guard,
ejecutar la suite de tests dispararía el `input()` y se colgaría.
</details>

---

### 10. ¿Cómo modificarías el diseño para que las lecturas en Fahrenheit se conviertan a Celsius antes de promediar?

<details>
<summary>Ver respuesta</summary>

Hoy `_parsear_temperatura()` descarta el sufijo sin mirar cuál era. La
extensión natural es que el helper devuelva también la unidad detectada
(por ejemplo, un `tuple[float | None, str]` con el valor y `"C"`/`"F"`/`"K"`),
y que `limpiar_registro_sensor()` guarde esa unidad en el registro limpio.
Recién ahí, en la capa de análisis (Punto B) o en un paso intermedio de
conversión, se aplicaría la fórmula `c = (f - 32) * 5 / 9` a los registros
en Fahrenheit, para que el promedio compare manzanas con manzanas. La clave
del diseño: **detectar** la unidad pertenece a la sanitización, pero
**convertir** la unidad es una transformación de dominio que debe quedar
explícita (y testeada) aparte.
</details>

---

## ¿Cómo seguir estudiando?

1. Corré los tests con `python -m unittest test_ejercicio_01.py -v` y
   **rompé algo a propósito**: cambiá un `>` por `>=` y mirá qué test falla.
2. Agregá vos mismos un caso borde nuevo (¿qué pasa si la temperatura llega
   como `"24.5c"` minúscula?) y escribí primero el test que lo exige.
3. Leé los docstrings del código con `help()`: desde Python,
   `help(limpiar_registro_sensor)` muestra la documentación completa.
