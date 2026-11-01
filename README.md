# TP FINAL COM 2

Repositorio de entregas del **Trabajo Práctico Final** de la materia **COM 2**.
Cada ejercicio se resuelve en su propia carpeta, con código extensamente
documentado con fines de **docencia y aprendizaje**: docstrings estilo Google,
type hints y comentarios que explican el *por qué* de cada decisión de diseño.

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
├── ejercicio_02_*/                    # Ejercicio 2 (próximamente)
└── ejercicio_03_*/                    # Ejercicio 3 (próximamente)
```

## Ejercicios

| # | Ejercicio | Contenido | Estado |
|---|---|---|---|
| 1 | [Sanitización y Análisis Estadístico de Sensores](./ejercicio_01_sensores/) | Normalización de registros crudos de EcoTech Solutions + reporte estadístico consolidado (alertas por umbral y promedio térmico). | ✅ Completo |
| 2 | *A definir* | — | ⬜ Pendiente |
| 3 | *A definir* | — | ⬜ Pendiente |

## Requisitos

- **Python 3.10 o superior** (los ejercicios usan type hints modernos como
  `float | None` y `list[str]`).
- **Cero dependencias externas**: todo se resuelve con la librería estándar,
  para que el TP funcione en cualquier máquina sin instalar nada.

## Cómo ejecutar cada ejercicio

```bash
# Ejercicio 1 — demostración del flujo completo (pide el umbral por teclado):
cd ejercicio_01_sensores
python ejercicio_01_sensores.py

# Ejercicio 1 — tests unitarios:
python -m unittest test_ejercicio_01.py -v
```

## Convenciones de documentación del repo

Para que los tres ejercicios se lean de la misma manera:

1. **Docstrings estilo Google** en cada función, clase y módulo: qué hace,
   argumentos, retorno, errores y ejemplos cuando aportan.
2. **Type hints en todo lo público**: las firmas se leen como documentación.
3. **Comentarios que explican el por qué**, no el qué: el código dice *qué*
   hace; el comentario dice *por qué* se hace así y qué alternativa se
   descartó.
4. **Constantes de módulo con nombre** en vez de números y textos mágicos
   dispersos por el código.
5. **Tests por ejercicio**, con nombres que describen la conducta probada.

## Cómo publicarlo en GitHub

La carpeta ya fue inicializada como repositorio Git local (rama `main`, con
todos los archivos preparados). Para publicarlo como repo **público**:

```bash
cd TP_FINAL_COM_2

# 1. Primer commit (configurá tu identidad si Git te lo pide):
git commit -m "Ejercicio 1: sanitización y análisis estadístico de sensores"

# 2. Crear el repositorio vacío en github.com (nombre sugerido: TP-FINAL-COM-2)
#    y conectarlo con tu URL real:
git remote add origin https://github.com/TU_USUARIO/TP-FINAL-COM-2.git

# 3. Publicar:
git push -u origin main
```

> Sugerencia: si el nombre del repo remoto no puede llevar guiones bajos,
> `TP-FINAL-COM-2` (con guiones) mantiene la lectura idéntica.
