# TP FINAL COM 2

Repositorio del **Trabajo Práctico Final** de Miguel Della Vecchia, **COMISION 2**.
Cada ejercicio se resuelve en su propia carpeta y documentado con docstrings estilo Google,
type hints y comentarios.

---

## Estructura del repositorio

```
TP_FINAL_COM_2/
├── README.md                          # Este archivo
├── .gitignore                         # Qué NO se versiona
├── ejercicio_01_sensores/             # Ejercicio 1 (completo)
│   ├── README.md                      # Conceptos, diseño y diagrama de flujo
│   ├── ejercicio_01_sensores.py       # Solución: Puntos A y B + demo completa
│   ├── test_ejercicio_01.py           # 19 tests unitarios (unittest)
│   └── guia_de_estudio.md             # 10 preguntas de repaso con respuestas
├── ejercicio_02_inventario/           # Ejercicio 2 (completo)
│   ├── README.md                      # Conceptos, diseño y diagrama de clases
│   ├── ejercicio_02_inventario.py     # Solución: Puntos A y B + demo completa
│   ├── test_ejercicio_02.py           # 24 tests unitarios (unittest)
│   └── guia_de_estudio.md             # 10 preguntas de repaso con respuestas
├── ejercicio_03_emisiones/            # Ejercicio 3 (completo)
│   ├── README.md                      # Conceptos, diseño y diagrama de flujo
│   ├── ejercicio_03_emisiones.py      # Algoritmo auditado + métricas + demo
│   ├── test_ejercicio_03.py           # 16 tests (TestCalculoEmisiones y más)
│   ├── vista_django.py                # Vista Django del panel (requiere Django)
│   ├── sustentabilidad/panel.html     # Plantilla del panel administrativo
│   └── guia_de_estudio.md             # 10 preguntas de repaso con respuestas
```

## Ejercicios

| # | Ejercicio | Contenido | Estado |
|---|---|---|---|
| 1 | [Sanitización y Análisis Estadístico de Sensores](./ejercicio_01_sensores/) | Normalización de registros crudos de EcoTech Solutions + reporte estadístico consolidado (alertas por umbral y promedio térmico). | ✅ Completo |
| 2 | [Modelo de Productos, Excepciones y Persistencia](./ejercicio_02_inventario/) | Jerarquía POO del catálogo (`DispositivoEcologico`, `PanelSolar`), excepción `StockInvalidoError` con stock encapsulado y persistencia en `catalogo_ecotech.json`. | ✅ Completo |
| 3 | [Auditoría con Tests Unitarios e Integración Web](./ejercicio_03_emisiones/) | Auditoría de `calcular_emisiones_carbono` con unittest, métricas por planta (`obtener_metricas_consumo`) y vista Django `vista_panel_sustentabilidad` con plantilla `sustentabilidad/panel.html`. | ✅ Completo |

## Requisitos

- **Python 3.10 o superior** (los ejercicios usan type hints modernos como
  `float | None` y `list[str]`).
- **Cero dependencias externas en los ejercicios 1 y 2**: todo se resuelve con la librería estándar.
- **Django (opcional)**: solo para la vista web del ejercicio 3 (`pip install django`); sin instalarlo, la auditoría y las métricas corren igual.

## Cómo ejecutar cada ejercicio

```bash
# Ejercicio 1 — demostración del flujo completo (pide el umbral por teclado):
cd ejercicio_01_sensores
python ejercicio_01_sensores.py

# Ejercicio 1 — tests unitarios:
python -m unittest test_ejercicio_01.py -v

# Ejercicio 2 — demostración (valida stock, muestra fichas y exporta el JSON):
cd ejercicio_02_inventario
python ejercicio_02_inventario.py

# Ejercicio 2 — tests unitarios:
python -m unittest test_ejercicio_02.py -v

# Ejercicio 3 — demostración (auditoría, métricas y render del panel):
cd ejercicio_03_emisiones
python ejercicio_03_emisiones.py

# Ejercicio 3 — tests unitarios (los de la vista piden Django instalado):
python -m unittest test_ejercicio_03.py -v
```

## Convenciones de documentación del repo

Para la legibilidad:

1. **Docstrings estilo Google** en cada función, clase y módulo: qué hace,
   argumentos, retorno, errores y ejemplos cuando aportan.
2. **Type hints en todo lo público**: las firmas se leen como documentación.
3. **Comentarios que explican el por qué, no el qué: el código dice *qué*
   hace; el comentario dice *por qué* se hace así y qué alternativa se
   descartó.
4. **Constantes de módulo con nombre** en vez de números y textos
   dispersos por el código.
5. **Tests por ejercicio**, con nombres que describen la conducta probada.


```bash
cd TP_FINAL_COM_2

# 1. Primer commit:
git commit -m "Ejercicio 1: sanitización y análisis estadístico de sensores"

# 2. Crear el repositorio vacío en github.com (TP-FINAL-COM-2)
git remote add origin https://github.com/huevosrotos/TP-FINAL-COM-2.git

# 3. Publicar:
git push -u origin main
```
