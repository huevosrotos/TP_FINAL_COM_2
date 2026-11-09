# Guía de estudio — Ejercicio 2 (Productos, Excepciones y Persistencia)

> **TP Final COM 2 · EcoTech Solutions**

Diez preguntas del TP. Pensá tu respuesta primero y después desplegá la
solución clickeando en **Ver respuesta**.

---

### 1. ¿Qué significa que el stock esté "encapsulado" y qué ganamos con `@property`?

<details>
<summary>Ver respuesta</summary>

Que el atributo real (`self._stock`) no se toca directamente: toda lectura y
escritura pasa por la property `stock`, cuyo setter valida las reglas de
negocio (entero y no negativo). La ganancia es que el invariante
"stock válido" se garantiza en UN único lugar: no importa quién asigne ni
desde dónde, es imposible dejar el objeto en un estado inválido. Si mañana
la regla cambia (ej: máximo 999), se edita un solo método.
</details>

---

### 2. ¿Por qué en el `__init__` asigno `self.stock = stock` y no `self._stock = stock`?

<details>
<summary>Ver respuesta</summary>

Porque `self.stock = stock` pasa por el setter de la property y ejecuta la
validación también durante la construcción. Si asignara directo a
`self._stock`, un `DispositivoEcologico("X", 100, -5)` se crearía con stock
negativo y la regla de negocio quedaría rota desde el primer día. Con la
property hay un solo punto de control (DRY) que protege al objeto durante
toda su vida.
</details>

---

### 3. ¿Por qué una excepción propia (`StockInvalidoError`) en lugar de `ValueError`?

<details>
<summary>Ver respuesta</summary>

Por el nombre y por la captura selectiva. El nombre comunica el dominio
("el stock es inválido") y permite escribir `except StockInvalidoError:`
en el punto exacto donde quiero manejar ese problema de inventario, sin
atrapar de yapa otros `ValueError` que puedan surgir en el mismo bloque y
que significan otra cosa. Además la clase guarda `valor_recibido`, así el
programa puede informar qué valor exacto fue rechazado.
</details>

---

### 4. ¿Por qué se rechaza `True` como stock si `isinstance(True, int)` es `True`?

<details>
<summary>Ver respuesta</summary>

Porque en Python `bool` es subclase de `int`: `True` pasaría el chequeo
`isinstance(nuevo_stock, int)` y quedaría guardado como stock 1. Un booleano
no es una cantidad de unidades: es casi seguro un error de tipeo o de
construcción del dato. Por eso el setter chequea primero
`isinstance(nuevo_stock, bool)` y lo rechaza explícitamente. Es la trampa
clásica de tipado en Python y hay un test que la fija
(`test_rechaza_booleano_como_stock`).
</details>

---

### 5. ¿Qué hereda `PanelSolar` y qué agrega? ¿Qué hace `super()`?

<details>
<summary>Ver respuesta</summary>

Hereda de `DispositivoEcologico` los atributos comunes (nombre, precio,
stock), la validación del stock, la serialización base y el método de ficha.
Agrega `potencia_maxima_watts` y `eficiencia_porcentaje`, su propia ficha
técnica, el cálculo de energía diaria y extiende `a_dict()`.
`super().__init__(...)` ejecuta el constructor de la clase base antes de
seguir con lo propio: así la parte "común" se inicializa una sola vez y en
un solo lugar, y la validación heredada aplica a toda la familia de clases.
</details>

---

### 6. ¿Dónde está el polimorfismo en este TP y qué pasaría sin él?

<details>
<summary>Ver respuesta</summary>

En `generar_ficha_tecnica()` y en `a_dict()`: la base y `PanelSolar`
comparten firma pero ejecutan comportamientos distintos. Cuando
`GestorInventario` hace `[d.a_dict() for d in lista]`, no sabe (ni le
importa) de qué clase es cada elemento: Python despacha la versión correcta.
Sin polimorfismo, el gestor tendría que preguntar `if isinstance(d,
PanelSolar): ... else: ...` por cada tipo conocido y tocar ese código cada
vez que se agrega una clase; con polimorfismo, agregar `TurbinaEolica` no
requiere cambiar el gestor (principio abierto/cerrado).
</details>

---

### 7. ¿Para qué sirve la clave `"tipo"` en `a_dict()`?

<details>
<summary>Ver respuesta</summary>

Para poder deserializar. El JSON no guarda información de clases: si no
anoto el tipo, al releer el archivo tengo diccionarios indistinguibles y no
sé si reconstruir un `DispositivoEcologico` o un `PanelSolar`. Con `"tipo"`
y el registro `CLASES` (un dict que mapea nombre → constructor), el gestor
elige la clase correcta y re-crea los objetos. El costo es mantener ese
registro al día; agregar una clase nueva es una línea.
</details>

---

### 8. ¿Por qué `json.dumps` no puede serializar los objetos directamente?

<details>
<summary>Ver respuesta</summary>

Porque JSON es un formato de texto que solo entiende tipos básicos: dict,
list, str, int, float, bool y None. Un objeto `PanelSolar` no es nada de eso
y `json.dumps` levanta `TypeError: Object of type PanelSolar is not JSON
serializable`. La solución del TP es la conversión manual: cada clase sabe
transformarse a dict (`a_dict()`) y ese dict sí es serializable. (La
alternativa estándar es un `default=` custom o una librería como
`dataclasses.asdict`/`pydantic`, pero a mano se entiende mejor el problema.)
</details>

---

### 9. ¿Qué pasa si guardo el JSON sin `encoding="utf-8"` en Windows?

<details>
<summary>Ver respuesta</summary>

Python usa la codificación local del sistema, que en Windows suele ser
cp1252. Los caracteres como "ó", "í" o "°" se guardan mal: el archivo puede
verse bien en esa PC pero mostrar símbolos raros (o lanzar
`UnicodeDecodeError`) al leerlo en Linux/Mac o al subirlo a GitHub. Fijando
`encoding="utf-8"` al escribir Y al leer, el archivo es idéntico en
cualquier plataforma y las tildes del catálogo sobreviven. Hay un motivo
extra: GitHub y la mayoría de las herramientas asumen UTF-8.
</details>

---

### 10. ¿Por qué los tests escriben el JSON en un directorio temporal y no en la carpeta del repo?

<details>
<summary>Ver respuesta</summary>

Por tres razones: (1) los tests deben poder correrse desde cualquier
directorio sin fallar por rutas relativas; (2) no deben ensuciar el repo con
archivos generados (un `catalogo_ecotech.json` viejo o parcial); y (3) cada
test debe ser independiente: `tempfile.TemporaryDirectory()` con
`addCleanup` crea un directorio nuevo por test y lo borra solo al
terminar, sin importar si el test pasó o falló. Es la práctica estándar
cuando el código bajo prueba toca el disco.
</details>

---

## ¿Cómo seguir estudiando?

1. Corré los tests y rompé algo a propósito: cambiá la validación del
   setter (permití negativos) y mirá cuántos tests se caen.
2. Agregá la subclase `TurbinaEolica` con sus atributos, su ficha y su línea
   en `CLASES`; después escribile un test de round-trip.
3. Probá qué pasa si leés un JSON editado a mano con un `"tipo"` inventado:
   el `ValueError` del gestor es lo que protege el catálogo.
