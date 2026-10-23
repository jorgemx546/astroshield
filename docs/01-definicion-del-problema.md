# Entregable 1 — Definición del problema

**Proyecto:** AstroShield — evolucionar una constelación inteligente
**Equipo:** Ríos Astudillo Daniel Eduardo · Itza Santizo Jarett Osiel · Salinas Beatriz Erick · Navarrete Tzuc Jorge
**Materia:** Fundamentos de Inteligencia Artificial — Ing. Carlos André Castro Rodríguez

Este documento fija las decisiones que convierten el escenario en un problema que una computadora puede resolver. Se escribió antes de programar el algoritmo; los valores numéricos que aparecen aquí son los que usa el código (`astroshield/escenario.py`).

---

## 0. El planeta: Veguitto

 Usamos **Veguitto**, un planeta ficticio definido por el equipo.

| Dato | Valor | Por qué |
|---|---|---|
| Forma | Esfera perfecta | El enunciado permite un modelo simplificado |
| Radio | **5,200 km** | Un planeta rocoso algo más chico que la Tierra (6,371 km). Que no sea la Tierra obliga a que todas las cuentas dependan del radio y no de constantes terrestres |
| Coordenadas | Latitud −90° a 90°, longitud −180° a 180° | Igual que en la Tierra, para usar los mismos datos del enunciado |

**Las coordenadas, prioridades, zonas restringidas, objetos ocupados y el radio de observación de 300 km son exactamente los del enunciado.** Solo cambian el planeta y los nombres. Así los resultados siguen siendo comparables con los de otros equipos.

### Regiones de interés

| Región en Veguitto | Equivale a | Centro (lat, lon) | Prioridad |
|---|---|---|---|
| Meseta Saiyan | Península de Yucatán | 20.5°, −89.0° | Alta |
| Selva Namek | Amazonía brasileña | −3.5°, −62.0° | Alta |
| Valle Capsule | California | 36.8°, −119.4° | Media |
| Llanura Kaio | Sahel | 15.0°, 0.0° | Media |
| Archipiélago Zenkai | Japón | 36.0°, 138.0° | Media |
| Desierto Kami | Interior de Australia | −25.0°, 133.0° | Normal |

Cada región es un **disco de 300 km de radio** sobre la superficie. En Veguitto eso equivale a un ángulo central de 300 / 5,200 rad = **3.31°**.

### Restricciones espaciales (segunda etapa)

| Zona | Equivale a | Centro | Radio angular |
|---|---|---|---|
| Cinturón de escombros Norte | Atlántico Norte | 45°, −35° | 12° |
| Cinturón de escombros Sur | Pacífico Sur | −30°, −120° | 10° |
| Casquete de escombros polar | Región polar norte | 78°, 30° | 8° |
| Objeto A (ocupado) | Objeto A | 10°, 45° | 5° |
| Objeto B (ocupado) | Objeto B | −15°, 110° | 5° |

---

## 1. Cómo se representa una configuración

Una configuración (un **individuo** del algoritmo evolutivo) es una matriz de **8 filas × 2 columnas**:

```
[[lat_1, lon_1],
 [lat_2, lon_2],
 ...
 [lat_8, lon_8]]
```

Cada fila es un satélite y guarda su **punto subsatelital**: el punto de la superficie que queda justo debajo de él. Todos los satélites vuelan a la **misma altitud fija de 600 km**, así que con latitud y longitud basta para ubicarlos.

**Supuestos del modelo (simplificación educativa):**

- Los satélites se tratan como **puntos fijos** sobre la esfera de altitud 600 km. No se simula la órbita, la velocidad ni el paso del tiempo; la configuración es una "fotografía" de dónde está cada satélite.
- Por eso las zonas restringidas, que el enunciado da en grados angulares, se interpretan como **casquetes esféricos**: un satélite está dentro de una zona si el ángulo entre su punto subsatelital y el centro de la zona es menor que el radio de la zona.
- El orden de los satélites no importa: la misma constelación escrita en otro orden es la misma solución.

**Por qué esta representación:** es la mínima que contiene todo lo que el problema pregunta (dónde está cada satélite), cada combinación de números es una constelación posible y no hay que decodificar nada.

## 2. Qué significa que una región esté cubierta

### Huella de un satélite

Cada satélite lleva un sensor que mira hacia abajo con un **semiángulo de visión de 35°**. Con la geometría de la esfera, el ángulo central de la huella es:

```
λ = arcsen( (R + h) / R · sen η ) − η
  = arcsen( 5800 / 5200 · sen 35° ) − 35°
  ≈ 4.77°   (≈ 433 km sobre la superficie)
```

Un punto de la superficie **es visto** por un satélite si el ángulo central entre el punto y el punto subsatelital es **≤ λ**.

### Cobertura de una región

Cada región se representa con **37 puntos de muestra**: el centro y tres anillos a 100, 200 y 300 km con 6, 12 y 18 puntos. Para cada región se calcula:

- **Cobertura `c`**: fracción de sus 37 puntos que ve al menos un satélite (0 a 1).
- **Redundancia `r`**: fracción de sus puntos que ven **dos o más** satélites.

Una región se considera **cubierta** si `c ≥ 0.95` (como máximo falta un punto de los 37). Usamos 0.95 y no 1.0 porque la muestra es discreta: exigir el 100 % haría que un punto en el borde decidiera solo.

Consecuencia geométrica: un solo satélite cubre una región completa solo si queda a menos de 4.77° − 3.31° = **1.47°** de su centro. Más lejos, hacen falta dos satélites o la región queda parcial.

## 3. Cómo se evalúa la calidad (función de aptitud)

Las prioridades se traducen a pesos lineales:

| Prioridad | Peso |
|---|---|
| Alta | 3 |
| Media | 2 |
| Normal | 1 |

Una región alta vale tres veces una normal. Escogimos pesos lineales porque el enunciado solo da un orden (alta > media > normal), no proporciones; 3-2-1 es la forma más simple de respetar ese orden sin inventar diferencias extremas. Los pesos son parámetros y se pueden cambiar.

La aptitud de una configuración válida es:

```
F = Σ wᵢ · cᵢ / Σ wᵢ   +   0.10 · Σ wᵢ · rᵢ / Σ wᵢ
     └ cobertura ponderada ┘      └ redundancia ponderada ┘
```

- El primer término (0 a 1) es lo principal: **cuánto de cada región se ve, pesado por su prioridad**.
- El segundo término premia con poco peso (máximo 0.10) que una región la vean dos satélites. Sirve para decidir qué hacer con los satélites que sobran: si uno falla, la región no se queda ciega. Su peso es chico a propósito para que **nunca convenga sacrificar cobertura por redundancia** (perder una región media cuesta 2/13 ≈ 0.15, más que toda la redundancia posible).

### Cota superior conocida

Las regiones están separadas por más de 20°, y una huella mide 4.77°, así que **un satélite nunca ve dos regiones a la vez**. Con 8 satélites, lo mejor posible es: 6 satélites cubren las 6 regiones y los 2 que sobran duplican las dos regiones de prioridad alta.

```
F_max = 1 + 0.10 · (3 + 3) / 13 ≈ 1.0462
```

Tener esta cota permite medir qué tan cerca del óptimo queda el algoritmo, en vez de solo decir "dejó de mejorar".

## 4. Cuándo una configuración es inválida

Una configuración es **inválida** si al menos un satélite:

1. Queda dentro de una **zona de escombros** (ángulo al centro < radio de la zona).
2. Queda dentro de la **zona de exclusión** de un objeto ocupado.
3. Queda a menos de **1°** de otro satélite de la constelación (≈ 100 km a la altura de órbita). Esta regla la agregamos nosotros: dos satélites en el mismo punto serían un riesgo de choque y además no aportan nada.

Además, toda configuración tiene exactamente 8 satélites: la representación no permite otra cantidad.

Para cada configuración se calcula la **violación total `V`** en grados: cuánto se mete cada satélite en cada zona prohibida, sumado. `V = 0` significa válida.

**Qué pasa con una configuración inválida:** no se descarta de inmediato, porque puede tener partes buenas. Se compara con las reglas de factibilidad de Deb:

1. Una válida siempre le gana a una inválida, sin importar su aptitud.
2. Entre dos válidas gana la de mayor aptitud `F`.
3. Entre dos inválidas gana la que viola menos (`V` menor).

Así una configuración inválida nunca puede ser "la mejor" mientras exista una válida, que es lo que pide el enunciado (una puntuación alta no sirve si incumple restricciones). Y como no hay que inventar un castigo con un número arbitrario, no hay que calibrarlo.

## 5. Estrategia del algoritmo evolutivo

Algoritmo genético generacional con elitismo:

1. **Población inicial:** 80 configuraciones al azar, con los satélites repartidos de forma uniforme sobre la esfera (sin amontonarse en los polos).
2. **Evaluación:** cobertura, redundancia, aptitud y violación de cada una.
3. **Selección por torneo** de 3 con las reglas de Deb.
4. **Cruza por fondo común** (probabilidad 0.9): se juntan los 16 satélites de los dos padres y el hijo toma 8 al azar. Como el orden de los satélites no importa, cruzar "el satélite 3 del padre A con el satélite 3 del padre B" no tendría sentido; el fondo común sí respeta eso.
5. **Mutación** (cada satélite con probabilidad 0.2):
   - 90 % de las veces, **desplazamiento** en una dirección al azar sobre la esfera, con una distancia que empieza grande (σ = 8°) y se reduce en cada generación hasta σ = 0.3°. Al principio explora; al final afina.
   - 20 % de las veces, **reubicación**: el satélite salta a otro lugar, para no quedarse atorado. La mitad de las reubicaciones son **al azar** en todo el planeta y la otra mitad son **informadas**: caen cerca de una región elegida al azar (a menos de huella + radio de la región, ≈ 8.1°, que es lo más lejos que un satélite puede estar para tocarla).

   La reubicación informada usa conocimiento del problema: solo cerca de una región un satélite puede sumar cobertura. La agregamos después de ver que, sin ella, el algoritmo dejaba regiones sin cubrir porque un salto al azar cae cerca de una región apenas el 0.5 % de las veces (ver la calibración en la sección 6 y la prueba P7).
6. **Elitismo:** las 2 mejores configuraciones pasan intactas a la siguiente generación, así la mejor solución encontrada nunca se pierde.
7. **Historial:** en cada generación se guarda la mejor aptitud, la aptitud promedio, el porcentaje de individuos válidos, la menor violación y cuántas regiones cubre la mejor.
8. Se repite durante un número **configurable** de generaciones.

## 6. Parámetros y valores iniciales

| Parámetro | Valor inicial | De dónde sale |
|---|---|---|
| Radio de Veguitto | 5,200 km | Definido por el equipo |
| Altitud de los satélites | 600 km | Órbita baja típica de observación |
| Semiángulo del sensor | 35° | Da una huella (≈ 433 km) un poco mayor que una región (300 km); así cubrir no es trivial |
| Radio de observación | 300 km | Enunciado |
| Puntos de muestra por región | 37 | Suficiente para estimar la cobertura sin hacer lenta la evaluación; se revisa en una prueba propia |
| Umbral de "cubierta" | 0.95 | Tolerancia de un punto de muestra |
| Pesos alta / media / normal | 3 / 2 / 1 | Orden del enunciado, pesos lineales |
| Peso de la redundancia | 0.10 | Menor que lo que vale cualquier región |
| Separación mínima entre satélites | 1° | Definida por el equipo (evitar choques) |
| Tamaño de población | 80 | Calibración (abajo): con 60 salían 15/20 corridas buenas, con 80 salen 18/20 |
| Generaciones | 150 | Configurable; la curva de evolución muestra si alcanza |
| Torneo | 3 | Presión de selección moderada |
| Probabilidad de cruza | 0.9 | Valor común en algoritmos genéticos |
| Probabilidad de mutación por satélite | 0.2 | ≈ 1.6 satélites mutados por hijo |
| σ de la mutación | 8° → 0.3° | Exploración al inicio, ajuste fino al final |
| Probabilidad de reubicación | 0.2 | Escape de óptimos locales |
| Reubicaciones informadas | 50 % | Calibración: 0 % → 5/20, 50 % → 15/20, 100 % → 14/20 (con población 60) |
| Élite | 2 | Conservar lo mejor sin frenar la diversidad |
| Semilla aleatoria | Configurable | Para repetir una ejecución exacta |

### Calibración

Los valores de arriba salieron de comparar combinaciones con **20 semillas cada una** (100 a 119) en la etapa 2. Se cuenta en cuántas corridas la solución final es "suficientemente buena" (sección 7). Se reproduce con `python calibrar.py` (resultado en `resultados/calibracion.json`).

| Población | Generaciones | Reubicación | Informadas | Mutación | σ final | F media | F mínima | Buenas |
|---|---|---|---|---|---|---|---|---|
| 60 | 150 | 0.1 | 0 % | 0.2 | 0.3 | 0.9615 | 0.8073 | 5/20 |
| 60 | 150 | 0.1 | 50 % | 0.2 | 0.3 | 1.0369 | 1.0119 | 15/20 |
| 60 | 150 | 0.2 | 50 % | 0.2 | 0.3 | 1.0368 | 1.0210 | 15/20 |
| 60 | 150 | 0.2 | 100 % | 0.2 | 0.3 | 1.0336 | 1.0106 | 14/20 |
| 60 | 200 | 0.2 | 50 % | 0.2 | 0.3 | 1.0362 | 1.0162 | 14/20 |
| **80** | **150** | **0.2** | **50 %** | **0.2** | **0.3** | **1.0390** | **1.0191** | **18/20** |
| 100 | 150 | 0.2 | 50 % | 0.2 | 0.3 | 1.0394 | 1.0272 | 17/20 |
| 80 | 250 | 0.2 | 50 % | 0.2 | 0.3 | 1.0406 | 1.0260 | 17/20 |
| 80 | 150 | 0.2 | 50 % | 0.15 | 0.3 | 1.0357 | 1.0185 | 17/20 |
| 80 | 150 | 0.2 | 50 % | 0.2 | 0.1 | 1.0367 | 1.0058 | 15/20 |

Lo que más cambió el resultado fue la reubicación informada (de 5/20 a 15/20). Más población o más generaciones mejoraron poco y cuestan más evaluaciones. Escogimos la fila en negritas: es la de más corridas buenas con 12,000 evaluaciones. Las diferencias de 1 o 2 corridas entre filas parecidas pueden ser azar; con 20 semillas no alcanza para separarlas.

## 7. Cuándo una solución es suficientemente buena

Para este escenario, una configuración es **suficientemente buena** si cumple las tres:

1. Es **válida** (`V = 0`).
2. Las **6 regiones están cubiertas** (`c ≥ 0.95` en cada una).
3. Su aptitud está a menos del 2 % de la cota superior: `F ≥ 0.98 · 1.0462 ≈ 1.025`.

Cuando las restricciones impiden cumplir la condición 2 (por ejemplo, una zona prohibida encima de una región), el sistema no lo esconde: reporta qué región no se puede cubrir y por qué, usando un análisis de alcanzabilidad que revisa, para cada punto de muestra, si existe alguna posición permitida desde donde se pueda ver.

Que el algoritmo deje de mejorar **no** demuestra que encontró el óptimo; por eso comparamos contra la cota superior y repetimos la ejecución con varias semillas.
