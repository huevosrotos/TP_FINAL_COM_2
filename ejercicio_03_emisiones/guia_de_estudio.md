# Guía de estudio — Ejercicio 3 (Auditoría e Integración Web)

> **TP Final COM 2 · EcoTech Solutions**

Diez preguntas del TP. Pensá tu respuesta primero y después desplegá la
solución clickeando en **Ver respuesta**.

---

### 1. ¿Por qué se audita el algoritmo con tests ANTES de integrarlo a la web?

<details>
<summary>Ver respuesta</summary>

Porque la web es solo una capa de presentación: si el número de fondo está
mal, un panel lindo muestra mentiras con confianza. Certificar primero con
tests significa que el resto del pipeline (métricas, contexto, plantilla)
se construye sobre un cálculo con conducta garantizada y documentada. Además,
si mañana cambia el factor o aparece un bug, la suite detecta el impacto
antes de que llegue al panel. Es el orden del enunciado: auditar y DESPUÉS
integrar.
</details>

---

### 2. ¿Qué es el patrón AAA y cómo se ve en un test de la suite?

<details>
<summary>Ver respuesta</summary>

Arrange-Act-Assert: (1) *Arrange*, preparar el escenario; (2) *Act*,
ejecutar una sola acción; (3) *Assert*, verificar el resultado. En
`test_consumo_nominal_con_factor_por_defecto`: el arrange es trivial (no
hay estado que preparar), el act es `calcular_emisiones_carbono(100)` y el
assert es `assertAlmostEqual(..., 40.0)`. En los tests de la vista el
arrange es más visible: creo el `RequestFactory` y la petición GET antes de
invocar la vista. Un test por conducta, sin efectos entre tests.
</details>

---

### 3. ¿Por qué `assertAlmostEqual` y no `assertEqual` para comparar floats?

<details>
<summary>Ver respuesta</summary>

Porque los floats tienen representación binaria finita y números como 0.4 o
0.2 no se representan exactamente: los cálculos arrastran colas de
redondeo. En el propio historial del TP, la planta Sur acumula
6380.200000000001 kg en lugar de 6380.2. Con `assertEqual` ese resultado
"malo" haría fallar un test aunque el algoritmo esté correcto;
`assertAlmostEqual` compara con una tolerancia (por defecto 7 decimales) y
verifica lo que importa: que el cálculo sea numéricamente correcto.
</details>

---

### 4. ¿Cómo se verifica que se lanza un `ValueError` y que el mensaje informa el valor?

<details>
<summary>Ver respuesta</summary>

Con el context manager de `assertRaises`, que entrega la excepción capturada:

```python
with self.assertRaises(ValueError) as contexto:
    calcular_emisiones_carbono(-5)
self.assertIn("-5", str(contexto.exception))
```

El `with` garantiza que la excepción OCURRA (si no se lanza, el test falla)
y `contexto.exception` permite inspeccionarla: en auditoría importa no solo
QUE falle, sino que el mensaje diga qué valor fue rechazado, porque eso es
lo que va a leer quien investigue un incidente de datos.
</details>

---

### 5. ¿Por qué `factor_emision` tiene valor por defecto y cómo se testea ese default?

<details>
<summary>Ver respuesta</summary>

Porque el caso más común (red eléctrica mixta, 0.4 kg CO2e/kWh) no debería
obligar a pasarlo en cada llamada: `calcular_emisiones_carbono(100)` es más
legible que `calcular_emisiones_carbono(100, 0.4)`. El default es parte del
contrato, así que se testea: la suite inspecciona la firma con
`inspect.signature` y verifica que el default sea 0.4, y además hay tests
que cubren la llamada con y sin factor explícito. Si mañana la cátedra
cambia el default, un test avisa.
</details>

---

### 6. ¿Qué forma tiene la entrada de `obtener_metricas_consumo` y qué devuelve?

<details>
<summary>Ver respuesta</summary>

Entra una lista de registros de la tubería, cada uno con `"planta"` (str) y
`"consumo_kwh"` (número). Devuelve un dict con: `detalle_plantas` (lista con
consumo y emisiones acumuladas por planta, en orden de primera aparición),
`total_consumo_kwh`, `total_emisiones_kg` y `planta_mayor_consumo` (None si
no hay registros). Devolver un dict y no una tupla fue deliberado: el
consumidor es la plantilla, que accede por NOMBRE de clave
(`{{ total_emisiones_kg }}`), no por posición.
</details>

---

### 7. Un registro trae consumo negativo: ¿qué pasa y por qué se eligió propagar el `ValueError`?

<details>
<summary>Ver respuesta</summary>

El `ValueError` que lanza el algoritmo auditado sube por
`obtener_metricas_consumo` y corta todo el procesamiento. Elegí propagarlo
porque un consumo negativo es un dato inválido cuyo
origen hay que investigar: capturarlo y seguir produciría un panel calculado
con datos truncados, que es peor que no tener panel. "Fallar ruidoso" es la
política correcta cuando la alternativa es mostrar números que nadie puede
confiar. (Contrastar con el Ejercicio 1, donde una lectura corrupta se
salteaba: acá el contrato del algoritmo es más estricto a propósito.)
</details>

---

### 8. ¿Por qué la vista es simple y qué gano separando `construir_contexto_panel()`?

<details>
<summary>Ver respuesta</summary>

Una vista liviana no calcula nada: toma el contexto y renderiza. La lógica
de armado vive en `construir_contexto_panel()`, que es una función pura de
librería estándar: se testea con unittest SIN arrancar Django, sin
configurar settings y sin motor de plantillas. La ganancia es que la
suite corre rápido y en cualquier máquina, y si mañana el panel se consume
desde otra interfaz (API, consola), el armado del contexto ya está probado
y reutilizado. La vista solo queda expuesta a los 2 tests que sí piden
Django.
</details>

---

### 9. ¿Qué es el "diccionario de contexto" de una vista Django y cómo lo usa la plantilla?

<details>
<summary>Ver respuesta</summary>

Es el dict que la vista le pasa a `render()` junto con la ruta de la
plantilla: sus claves se convierten en variables disponibles dentro del
HTML. Con `contexto["titulo"]`, la plantilla escribe `{{ titulo }}`; con la
lista `detalle_plantas`, hace `{% for fila in detalle_plantas %}` y accede
a `{{ fila.consumo_kwh }}`. Además se pueden usar filtros como
`floatformat:2` para formatear números. La plantilla también decide con
`{% if detalle_plantas %}...{% else %}...{% endif %}` qué mostrar cuando no
hay datos.
</details>

---

### 10. ¿Cómo encuentra Django la plantilla `sustentabilidad/panel.html` y qué hace `skipUnless` en los tests?

<details>
<summary>Ver respuesta</summary>

Django busca la plantilla en los directorios declarados en la configuración
de `TEMPLATES`. En el TP, tanto los tests como la demo configuran `DIRS`
apuntando a la carpeta del ejercicio, así el loader resuelve
`sustentabilidad/panel.html` dentro de ella; en un proyecto real, esa
carpeta vive dentro del `templates/` de una app (con `APP_DIRS: True`).
`skipUnless(DJANGO_DISPONIBLE, ...)` decora la clase de tests de la vista:
si Django no está instalado, esos tests se marcan `skipped` (ni pasan ni
fallan) y la suite sigue verde; con Django instalado, corren completos. Es
la forma estándar de manejar dependencias opcionales en tests.
</details>

---

## ¿Cómo seguir estudiando?

1. Correr `python -m unittest test_ejercicio_03.py -v` con y sin Django
   (`pip uninstall django`) y comparar la salida: 16 tests vs 14 + 2 skipped.
2. Romper el algoritmo a propósito (borrar el chequeo de negativos) y mirar
   qué tests de auditoría se caen primero.
3. Editar `sustentabilidad/panel.html` agregar una columna o un título y
   volver a correr la demo para ver el render actualizado.
