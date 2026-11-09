"""Ejercicio 2 — Modelo de Productos, Excepciones y Persistencia.

TP Final COM 2 · EcoTech Solutions — Equipamiento sustentable
==============================================================

Contexto
--------
La división de equipamiento sustentable necesita gestionar el catálogo de
productos: impedir inconsistencias de inventario (stock negativo) mediante
validaciones de negocio y garantizar la persistencia del stock en disco.

Resolví el ejercicio en dos capas:

* **Punto A — Dominio (POO):** la excepción ``StockInvalidoError``, la clase
  base ``DispositivoEcologico`` con el stock encapsulado (``@property``) y la
  especialización ``PanelSolar`` (herencia + polimorfismo en la ficha técnica).
* **Punto B — Persistencia:** ``GestorInventario``, que serializa el catálogo
  a ``catalogo_ecotech.json`` y también lo vuelve a cargar desde disco (extra).

Nota sobre el nombre de la clase base: el enunciado la llama
``DispositivoEcológico``, pero PEP 8 recomienda identificadores ASCII (sin
tildes) para que el código sea cómodo de tipear e importar desde cualquier
teclado. La clase es la misma.

Cómo ejecutar la demostración
-----------------------------
::

    python ejercicio_02_inventario.py

Cómo correr los tests
---------------------
::

    python -m unittest test_ejercicio_02.py -v
"""

import json
from pathlib import Path
from typing import Any

# =============================================================================
# PUNTO A — DOMINIO DEL CATÁLOGO Y REGLAS DE INVENTARIO
# =============================================================================
class StockInvalidoError(Exception):
    """Regla de negocio violada: el stock recibido no es válido.

    Attributes:
        valor_recibido: el valor que disparó el error.
    """

    def __init__(self, mensaje: str, valor_recibido: Any = None) -> None:
        # Le paso el mensaje a Exception para que print() y los tracebacks
        # lo muestren como cualquier excepción nativa.
        super().__init__(mensaje)
        self.valor_recibido = valor_recibido


class DispositivoEcologico:
    """Producto genérico del catálogo de equipamiento sustentable.

    El stock lo encapsulé con una ``@property`` para que la regla se valide en un único
    lugar, sin importar quién ni cómo asigne el valor.

    Attributes:
        nombre: nombre comercial del producto.
        precio: precio de lista.
        stock: unidades disponibles (siempre un ``int`` mayor o igual a 0).
    """

    def __init__(self, nombre: str, precio: float, stock: int) -> None:
        self.nombre = nombre
        self.precio = precio
        # Asigno a través de ``self.stock`` (la property) y NO directo a
        # ``self._stock``, así el constructor valida igual que cualquier otra
        # asignación: un solo punto de control (DRY).
        self.stock = stock

    # --- Encapsulamiento del stock -------------------------------------------
    @property
    def stock(self) -> int:
        """Devuelve las unidades disponibles (lectura libre)."""
        return self._stock

    @stock.setter
    def stock(self, nuevo_stock: int) -> None:
        """Valida y asigna el stock, o levanta ``StockInvalidoError``.

        Reglas de negocio:
            * debe ser un ``int``: rechazo ``float``, ``str`` y hasta ``bool``,
            * no puede ser negativo (cero es válido: producto sin stock).
        """
        if isinstance(nuevo_stock, bool) or not isinstance(nuevo_stock, int):
            raise StockInvalidoError(
                f"El stock debe ser un entero; recibí {type(nuevo_stock).__name__}",
                nuevo_stock,
            )
        if nuevo_stock < 0:
            raise StockInvalidoError(
                f"El stock no puede ser negativo (recibí {nuevo_stock})",
                nuevo_stock,
            )
        # El "_" inicial es la convención de atributo interno: nadie debería
        # tocarlo por fuera; siempre se pasa por la property.
        self._stock = nuevo_stock

    # --- Comportamiento del dominio --------------------------------------------
    def generar_ficha_tecnica(self) -> str:
        """Devuelve la ficha técnica comercial en texto.

        Este método es el punto de polimorfismo del TP.
        """
        return (
            f"FICHA TÉCNICA — {type(self).__name__}\n"
            f"  Producto: {self.nombre}\n"
            f"  Precio:   ${self.precio:.2f}\n"
            f"  Stock:    {self._stock} unidades"
        )

    def valor_inventario_en_stock(self) -> float:
        """Valor del stock actual: precio por unidades."""
        return self.precio * self._stock

    def a_dict(self) -> dict[str, Any]:
        """Serializa el dispositivo a un dict listo para JSON.

        Incluí la clave ``"tipo"`` con el nombre real de la clase: al leer el
        archivo voy a saber qué constructor usar para reconstruir el objeto.
        """
        return {
            "tipo": type(self).__name__,
            "nombre": self.nombre,
            "precio": self.precio,
            "stock": self._stock,
        }

    def __repr__(self) -> str:
        """Representación técnica (la que se ve en consola y tests)."""
        return (
            f"{type(self).__name__}(nombre={self.nombre!r}, "
            f"precio={self.precio!r}, stock={self._stock})"
        )


class PanelSolar(DispositivoEcologico):
    """Panel fotovoltaico: especializa el dispositivo genérico.

    Hereda todo el comportamiento de ``DispositivoEcologico`` (incluida la
    validación de stock) y agrega sus atributos técnicos.
    """

    def __init__(
        self,
        nombre: str,
        precio: float,
        stock: int,
        potencia_maxima_watts: float,
        eficiencia_porcentaje: float,
    ) -> None:
        # ``super().__init__`` ejecuta el constructor de la base: el stock
        # queda validado exactamente igual que en cualquier dispositivo.
        super().__init__(nombre, precio, stock)
        self.potencia_maxima_watts = potencia_maxima_watts
        self.eficiencia_porcentaje = eficiencia_porcentaje

    def generar_ficha_tecnica(self) -> str:
        """Ficha especializada: reutilizo la base y agrego lo propio.

        POLIMORFISMO: misma firma que en la base, otro comportamiento.
        """
        ficha = super().generar_ficha_tecnica()
        return (
            ficha
            + f"\n  Potencia máxima: {self.potencia_maxima_watts} W"
            + f"\n  Eficiencia:      {self.eficiencia_porcentaje} %"
        )

    def energia_diaria_estimada_kwh(self, horas_sol: float) -> float:
        """Estimación simple de generación diaria en kWh."""
        return (
            self.potencia_maxima_watts * horas_sol / 1000
            * (self.eficiencia_porcentaje / 100)
        )

    def a_dict(self) -> dict[str, Any]:
        """Extiendo la serialización de la base con los campos técnicos."""
        datos = super().a_dict()
        datos["potencia_maxima_watts"] = self.potencia_maxima_watts
        datos["eficiencia_porcentaje"] = self.eficiencia_porcentaje
        return datos


# =============================================================================
# PUNTO B — PERSISTENCIA Y GESTIÓN DEL CATÁLOGO
# =============================================================================
class GestorInventario:
    """Serializa y recupera el catálogo en disco.
    """

    # Registro de clases conocidas: mapea el valor de la clave "tipo" con el
    # constructor a usar. Agregar una clase nueva al catálogo = una línea acá.
    CLASES: dict[str, type[DispositivoEcologico]] = {
        "DispositivoEcologico": DispositivoEcologico,
        "PanelSolar": PanelSolar,
    }

    def crear_desde_dict(self, registro: dict[str, Any]) -> DispositivoEcologico:
        """Fábrica: reconstruye una instancia desde su versión en dict."""
        clase = self.CLASES.get(registro.get("tipo"))
        if clase is None:
            raise ValueError(
                f"Tipo de producto desconocido: {registro.get('tipo')!r}"
            )
        # "**campos" desempaqueta el dict como argumentos nombrados del
        # constructor; la clave "tipo" no es parámetro, así que la saco.
        campos = {clave: valor for clave, valor in registro.items() if clave != "tipo"}
        return clase(**campos)

    def guardar_catalogo_json(
        self,
        lista_dispositivos: list[DispositivoEcologico],
        ruta_archivo: str | Path,
    ) -> int:
        """Serializa el catálogo y lo guarda en un archivo JSON.

        Args:
            lista_dispositivos: instancias ya validadas del Punto A.
            ruta_archivo: destino del archivo (acepta str o Path).

        Returns:
            La cantidad de dispositivos guardados (útil para el reporte).

        Raises:
            TypeError: si lo que llega no es una lista.
        """
        if not isinstance(lista_dispositivos, list):
            raise TypeError("guardar_catalogo_json espera una lista de dispositivos")
        # El polimorfismo hace el trabajo: a cada objeto le pido a_dict() y
        # Python ejecuta solo la versión correcta (base o PanelSolar).
        datos = [dispositivo.a_dict() for dispositivo in lista_dispositivos]
        # encoding="utf-8" explícito: sin eso Windows guarda en otra
        # codificación y las tildes se rompen al leer en otra máquina.
        Path(ruta_archivo).write_text(
            json.dumps(datos, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        return len(datos)

    def cargar_catalogo_json(
        self, ruta_archivo: str | Path
    ) -> list[DispositivoEcologico]:
        """(Extra) Lee el JSON y reconstruye las instancias (round-trip)."""
        datos = json.loads(Path(ruta_archivo).read_text(encoding="utf-8"))
        return [self.crear_desde_dict(registro) for registro in datos]


# =============================================================================
# BLOQUE DE PRUEBA — FLUJO COMPLETO
# =============================================================================
RUTA_CATALOGO = Path("catalogo_ecotech.json")


def demo_flujo_completo() -> None:
    """Demuestra validación de stock, polimorfismo y persistencia."""
    gestor = GestorInventario()

    print("=" * 66)
    print("TP FINAL COM 2 · Ejercicio 2 — Catálogo EcoTech Solutions")
    print("=" * 66)

    # ------------------------------------------------------------------
    # PASO 1: alta del catálogo. El producto con stock negativo NO entra:
    # la validación del constructor lo rechaza y lo capturo controladamente.
    # ------------------------------------------------------------------
    catalogo_crudo: list[dict[str, Any]] = [
        {"tipo": "PanelSolar", "nombre": "Panel Solar EcoTech 450W",
         "precio": 289900.0, "stock": 12,
         "potencia_maxima_watts": 450.0, "eficiencia_porcentaje": 21.5},
        {"tipo": "DispositivoEcologico", "nombre": "Cargador solar portátil 20W",
         "precio": 45500.0, "stock": 30},
        {"tipo": "DispositivoEcologico", "nombre": "Kit de iluminación LED solar",
         "precio": 31200.0, "stock": 8},
        {"tipo": "PanelSolar", "nombre": "Panel bifacial 550W",
         "precio": 412000.0, "stock": 5,
         "potencia_maxima_watts": 550.0, "eficiencia_porcentaje": 22.8},
        {"tipo": "PanelSolar", "nombre": "Panel con falla de fábrica",
         "precio": 199000.0, "stock": -3,
         "potencia_maxima_watts": 300.0, "eficiencia_porcentaje": 15.0},
    ]

    catalogo: list[DispositivoEcologico] = []
    print("\n[1] Alta del catálogo con validación de negocio:")
    for datos in catalogo_crudo:
        try:
            producto = gestor.crear_desde_dict(datos)
            catalogo.append(producto)
            print(f"  [OK]        {producto.nombre} (stock: {producto.stock})")
        except StockInvalidoError as error:
            print(f"  [RECHAZADO] {datos['nombre']}: {error}")

    # ------------------------------------------------------------------
    # PASO 2: intento de asignación errónea sobre un producto VÁLIDO.
    # El encapsulamiento impide que el stock se corrompa.
    # ------------------------------------------------------------------
    panel = catalogo[0]
    print(f"\n[2] Intento de asignar stock = -5 a '{panel.nombre}':")
    try:
        panel.stock = -5
    except StockInvalidoError as error:
        print(f"  StockInvalidoError capturada: {error}")
        print(f"  Valor rechazado: {error.valor_recibido}")
        print(f"  El stock quedó intacto: {panel.stock} unidades")

    # ------------------------------------------------------------------
    # PASO 3: polimorfismo en acción — misma llamada, ficha distinta.
    # ------------------------------------------------------------------
    print("\n[3] Fichas técnicas (misma llamada, respuesta según la clase):")
    print(catalogo[1].generar_ficha_tecnica())
    print()
    print(panel.generar_ficha_tecnica())

    # ------------------------------------------------------------------
    # PASO 4: exportación de los productos válidos al archivo JSON.
    # ------------------------------------------------------------------
    cantidad = gestor.guardar_catalogo_json(catalogo, RUTA_CATALOGO)
    valor_total = sum(d.valor_inventario_en_stock() for d in catalogo)
    print(f"\n[4] Exportación: {cantidad} productos válidos guardados en "
          f"{RUTA_CATALOGO.resolve()}")
    print(f"    Valor total del inventario: ${valor_total:.2f}")
    print("\nContenido del archivo:")
    print(RUTA_CATALOGO.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # PASO 5 (extra): releo el archivo y reconstruyo los objetos.
    # ------------------------------------------------------------------
    recuperados = gestor.cargar_catalogo_json(RUTA_CATALOGO)
    print("[5] Catálogo recargado desde el disco (round-trip):")
    for producto in recuperados:
        print(f"  {producto!r}")


if __name__ == "__main__":
    # Mismo guard que en el Ejercicio 1: la demo corre solo si ejecuto el
    # archivo directamente; los tests importan el módulo sin efectos de I/O.
    demo_flujo_completo()
