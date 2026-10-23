# Entregable 3 — Pruebas y validación

Todas las pruebas están en `astroshield/experimentos.py` y se ejecutan en el notebook `AstroShield.ipynb` o con `python correr_experimentos.py`. Los números de este documento salen de esa ejecución (archivo `resultados/resumen.json`). Las semillas aleatorias están fijas: 42 para las corridas individuales y 100 a 119 para la prueba de variación.

Además hay **29 pruebas unitarias** (`pytest`) que revisan la geometría, la evaluación y el algoritmo por separado (ver al final).

**Configuración usada en todas las corridas:** población 80, 150 generaciones (12,000 evaluaciones), torneo 3, cruza 0.9, mutación 0.2 por satélite, σ de 8° a 0.3°, reubicación 0.2 (la mitad informada), élite 2.

---

## P1 — Escenario inicial

| | |
|---|---|
| **Condiciones** | Etapa 1 (sin restricciones) y etapa 2 (con las 3 zonas de escombros y los 2 objetos), semilla 42 |
| **Resultado etapa 1** | F = 1.0291 (98.4 % de la cota), 6/6 regiones cubiertas, válida, suficientemente buena. Duplica Llanura Kaio y en parte Archipiélago Zenkai |
| **Resultado etapa 2** | F = 1.0462 (**100 % de la cota**), 6/6 cubiertas, válida. Un satélite por región y los dos sobrantes en Meseta Saiyan y Selva Namek (las dos de prioridad alta) |
| **Población inicial** | La mejor configuración al azar tenía F = 0.3867 y **0/6** regiones cubiertas |
| **Tiempo** | ≈ 1 s por corrida |

| Región | Cobertura | Redundancia | Satélites que la ven (etapa 2) |
|---|---|---|---|
| Meseta Saiyan (alta) | 100 % | 100 % | 3, 6 |
| Selva Namek (alta) | 100 % | 100 % | 0, 5 |
| Valle Capsule (media) | 100 % | 0 % | 4 |
| Llanura Kaio (media) | 100 % | 0 % | 7 |
| Archipiélago Zenkai (media) | 100 % | 0 % | 2 |
| Desierto Kami (normal) | 100 % | 0 % | 1 |

**Interpretación.** El algoritmo cumple el objetivo en las dos etapas. Con la misma semilla, la etapa 1 queda un poco abajo de la etapa 2 aunque tiene menos restricciones. La causa es el azar de la búsqueda, no las restricciones; la prueba P7 lo confirma con 20 semillas.

Evidencia visual: `resultados/globo_etapa1.html`, `resultados/globo_etapa2.html`, `resultados/mapa_etapa2.png`.

## P2 — Evolución

| Generación | Mejor F | F promedio (válidas) | % válidas | Regiones cubiertas | σ |
|---|---|---|---|---|---|
| 0 | 0.3867 | 0.0197 | 81.2 | 0 | 8.00 |
| 5 | 0.6590 | 0.2680 | 91.2 | 1 | 7.17 |
| 10 | 0.7751 | 0.4825 | 83.8 | 1 | 6.42 |
| 25 | 0.9179 | 0.5956 | 75.0 | 4 | 4.61 |
| 50 | 0.9578 | 0.6885 | 72.5 | 4 | 2.66 |
| 75 | 1.0297 | 0.7465 | 66.2 | 6 | 1.53 |
| 100 | 1.0437 | 0.8052 | 63.7 | 6 | 0.88 |
| 149 | 1.0462 | 0.7638 | 58.8 | 6 | 0.30 |

Alcanza el 95 % de la cota en la generación 64, el 98 % en la 73 y la cota exacta en la 130. Gráfica: `resultados/evolucion_etapa2.png`.

**Interpretación.** Primero sube rápido (se encuentran regiones) y luego por escalones; cada escalón es una región que entra en una huella. Con las 6 regiones ya cubiertas, la mejora restante es redundancia, y llega cuando σ ya es chico. El elitismo garantiza que la mejor nunca baja (también lo revisa una prueba unitaria). El porcentaje de válidas baja con las generaciones porque la población se acerca a regiones y bordes de zonas al explorar, pero eso no afecta a la mejor solución.

## P3 — Zonas restringidas (desechos espaciales)

| | |
|---|---|
| **Condiciones** | Solución final de P1 (etapa 2); 1,000 configuraciones al azar; inyección de un satélite en el centro de cada zona |
| **Márgenes de la solución final** | Cinturón Norte: satélite más cercano a 40.61° (margen 28.61°) · Cinturón Sur: 57.66° (margen 47.66°) · Casquete polar: 58.52° (margen 50.52°) |
| **Al azar** | 21.5 % de las configuraciones son inválidas; 94, 63 y 41 satélites (de 8,000) caen en cada cinturón |
| **Inyección** | Las 3 se detectan como inválidas, con violación igual al radio de la zona (12°, 10°, 8°) |
| **Control** | Las 10 soluciones de la etapa 1 (semillas 100 a 109) también son válidas en la etapa 2 |

**Interpretación.** Ningún satélite de la solución entra en una zona de desechos, y un satélite metido a propósito se detecta siempre. Hay que decirlo con honestidad: en el escenario base las zonas están lejos de las regiones y **no cambian el óptimo**; actúan sobre la búsqueda (descartan uno de cada cinco individuos al azar), no sobre la respuesta final. Para medir un efecto real sobre la solución están P5 y P6.

## P4 — Posiciones ocupadas

| | |
|---|---|
| **Condiciones** | Iguales a P3, con Objeto A (10°, 45°) y Objeto B (−15°, 110°), radio 5° |
| **Márgenes** | Objeto A: satélite más cercano a 45.05° (margen 40.05°) · Objeto B: 22.94° (margen 17.94°, la zona más cercana a la solución) |
| **Al azar** | 18 y 8 satélites caen dentro de cada objeto |
| **Inyección** | Las 2 se detectan como inválidas (violación 5°) |
| **Caso con efecto real** | En P6a se mueve Objeto B encima de Desierto Kami |

**Interpretación.** Igual que P3: la solución respeta los objetos y las violaciones se detectan. Que una configuración con un satélite dentro de un objeto siga teniendo aptitud 0.8923 y aun así pierda frente a cualquier válida es justo lo que pide el enunciado: una puntuación alta no sirve si incumple restricciones.

## P5 — Espacio reducido

**a) Nube de escombros de 2.5° sobre el centro de Meseta Saiyan.**

| Caso | F | % cota | Cubiertas | Satélites sobre M. Saiyan | Más cercano al centro |
|---|---|---|---|---|---|
| Etapa 2 (referencia) | 1.0462 | 100.0 | 6 | 2 | 1.02° |
| + zona de 2.5° | 1.0004 | 95.6 | 5 | 2 | 2.83° |

Con 5 semillas (42 a 46): F = 1.0004, 1.0227, 1.0075, 0.9859, 1.0249; regiones cubiertas = 5, 6, 5, 3, 6; **ninguna** suficientemente buena. Meseta Saiyan queda entre 94.6 % y 100 %.

**b) Zonas extra de 6° al azar** (que no tapan el centro de ninguna región).

| Zonas extra | % del espacio prohibido | % válidas al azar | F final | % cota | Cubiertas |
|---|---|---|---|---|---|
| 0 | 2.7 | 82.4 | 1.0462 | 100.0 | 6 |
| 10 | 5.5 | 65.6 | 1.0424 | 99.6 | 6 |
| 20 | 8.2 | 52.5 | 1.0405 | 99.5 | 6 |
| 40 | 13.4 | 33.3 | 1.0324 | 98.7 | 5 |

**Interpretación.** Cuando la zona tapa el centro de una región, el algoritmo encuentra la estrategia correcta sin que se la digamos: rodea la zona con **dos satélites** a 2.8° del centro. Ese satélite extra sale de la redundancia y la calidad baja. Al reducir el espacio con zonas al azar, la búsqueda se vuelve más difícil (con 40 zonas solo un tercio de las configuraciones al azar es válida), pero la solución final siempre es válida y la calidad baja poco a poco. **Limitación:** la cota superior supone un satélite por región; con zonas encima de una región ya no es alcanzable, así que el "% de la cota" subestima la calidad en estos casos.

## P6 — Condición difícil o inviable

| Caso | Alcanzabilidad de la región afectada | Resultado (semilla 42) | 5 semillas |
|---|---|---|---|
| a) Objeto B movido sobre Desierto Kami | Kami: 97.3 % (el centro no se puede ver desde ninguna posición permitida) | Válida, F = 0.9877, 5/6, Kami al 62.2 % | F de 0.9784 a 0.9948; Kami entre 0 % y 62 % |
| b) Zona de 9° sobre Meseta Saiyan | Saiyan: 0 % | Válida, F = 0.8185, 5/6, Saiyan al 0 % | F de 0.8156 a 0.8231 |
| c) Todo el planeta prohibido | 0 % en todas | **Inválida**, violación 8.37°, 17 problemas reportados, 0 % de válidas al final | — |

**Interpretación.**

- **a)** No se puede cubrir Kami por completo, y el algoritmo tampoco llega al máximo posible. Según la semilla, deja Kami entre 0 % y 62 %. Como Kami pesa 1, a la función de aptitud le conviene más usar los satélites en redundancia de regiones altas. **Es una limitación del criterio, no del código:** la aptitud permite abandonar una región de baja prioridad cuando es difícil.
- **b)** La región es imposible de observar y el sistema se comporta bien: no la marca como cubierta, el análisis de alcanzabilidad dice que es imposible y entrega la mejor configuración válida para las otras cinco.
- **c)** No existe ninguna configuración válida. El sistema no presenta una solución inválida como si fuera buena: devuelve la que menos viola, la marca **inválida** y lista cada problema.

Evidencia visual: `resultados/globo_p6_a.html`, `globo_p6_b.html`, `globo_p6_c.html` y los mapas correspondientes.

## P7 — Variación entre ejecuciones

| | |
|---|---|
| **Condiciones** | Etapa 2, 20 semillas (100 a 119), 12,000 evaluaciones cada una. Mismas semillas y mismo presupuesto para dos referencias: el algoritmo **sin reubicación informada** ("ciego") y **búsqueda aleatoria** |

| Método | F media | Desv. est. | F mín. | F máx. | 6/6 cubiertas | Suficientemente buenas |
|---|---|---|---|---|---|---|
| Evolutivo (informado) | 1.0390 | 0.0060 | 1.0191 | 1.0462 | 18/20 | 18/20 |
| Evolutivo ciego | 0.9809 | 0.0418 | 0.8983 | 1.0437 | 4/20 | 4/20 |
| Búsqueda aleatoria | 0.3583 | 0.0488 | 0.2931 | 0.4761 | 0/20 | 0/20 |

Detalle de las 20 corridas: 2 llegan exactamente a la cota (semillas 101 y 114); las que fallan son la 113 y la 116, que dejan Desierto Kami parcial (81 % y 95 %). La generación en que se alcanza el 98 % de la cota va de 48 a 107. Lo que más cambia entre corridas es **dónde quedan los satélites sobrantes**: Selva Namek con redundancia completa en 10 corridas, Meseta Saiyan en 6, alguna región media en 5 (algunas corridas duplican dos regiones y otras ninguna por completo). Gráficas: `resultados/variacion_20_semillas.png` y `resultados/comparacion_metodos.png`.

**Interpretación.** El resultado es estable en calidad (desviación 0.006) pero no en forma: hay muchas constelaciones casi igual de buenas y el algoritmo encuentra una distinta cada vez. Que la búsqueda aleatoria no pase de 0.48 con el mismo trabajo demuestra que la evolución sí aporta. La versión ciega muestra que los operadores importan: la reubicación informada pasa el éxito de 4/20 a 18/20.

## P8 — Prueba propia 1: falla de un satélite

| | |
|---|---|
| **Pregunta** | El criterio premia la redundancia, pero ¿sirve de verdad? ¿Qué pasa si falla cada satélite de la solución final? |
| **Condiciones** | Solución de P1 (etapa 2); se quita un satélite a la vez y se evalúa con 7 |

| Satélite que falla | Estaba sobre | F con 7 | Caída | Regiones perdidas |
|---|---|---|---|---|
| 0, 5 | Selva Namek | 1.0231 | 0.0231 | ninguna |
| 3, 6 | Meseta Saiyan | 1.0231 | 0.0231 | ninguna |
| 1 | Desierto Kami | 0.9692 | 0.0769 | Desierto Kami |
| 2 | Archipiélago Zenkai | 0.8923 | 0.1538 | Archipiélago Zenkai |
| 4 | Valle Capsule | 0.8923 | 0.1538 | Valle Capsule |
| 7 | Llanura Kaio | 0.8923 | 0.1538 | Llanura Kaio |

**Interpretación.** La redundancia funciona: las dos regiones de prioridad alta sobreviven a la falla de cualquiera de sus satélites. La limitación queda medida: con 8 satélites y 6 regiones, 4 regiones dependen de un solo satélite y se pierden si este falla.

## P9 — Prueba propia 2: ¿el muestreo de 37 puntos engaña?

| | |
|---|---|
| **Error que busca** | El algoritmo optimiza la cobertura medida con 37 puntos. Podría poner los satélites de forma que los 37 puntos queden vistos pero haya huecos entre ellos. Sería un error de nuestra propia implementación que ninguna otra prueba vería |
| **Condiciones** | Las 21 soluciones finales (P1 + P7) se vuelven a medir con 121 puntos por región |
| **Resultado** | Diferencias en 3 de 126 casos (región × solución); 1 cambio de estado |

| Solución | Región | Cobertura con 37 | Con 121 | ¿Cubierta? 37 → 121 |
|---|---|---|---|---|
| semilla 113 | Desierto Kami | 81.1 % | 81.0 % | no → no |
| semilla 116 | Desierto Kami | 94.6 % | 96.7 % | no → **sí** |
| semilla 118 | Meseta Saiyan | 100 % | **98.3 %** | sí → sí |

**Interpretación.** El error existe pero es chico. En la semilla 118, una región que con 37 puntos parecía vista al 100 % tiene un hueco de 1.7 %. En la 116 pasa lo contrario: la muestra chica fue pesimista y la región sí estaba cubierta. Ninguna conclusión cambia, pero el "100 %" del reporte debe leerse como una **estimación**. Mejora posible: reportar la cobertura final con la muestra densa.

## P10 — Cambio en las condiciones (sección 3.3)

| Caso | Configuración anterior | Nueva corrida |
|---|---|---|
| a) Selva Namek baja de alta a normal (nueva cota 1.0455) | **Sigue válida**, F = 1.0364 (99.1 %), pero gasta redundancia en Selva Namek | F = 1.0435 (99.8 %), 6/6, ya solo duplica Meseta Saiyan |
| b) Se cierra una zona de 2° justo donde estaba el satélite que ve Llanura Kaio | **Inválida** (aunque su aptitud sea 1.0462) | Válida, F = 1.0385 (99.3 %), 6/6, mueve la redundancia a Meseta Saiyan y Valle Capsule |

**Interpretación.** Un cambio de prioridad nunca invalida una constelación; solo puede hacerla menos conveniente, y el sistema lo mide. Un cambio de restricciones sí puede invalidarla, y el sistema lo detecta antes de volver a buscar. El globo `resultados/globo_p10_b.html` muestra la configuración anterior con el satélite en rojo dentro de la zona nueva.

---

## Pruebas unitarias (`pytest`)

```
python -m pytest pruebas
29 passed
```

| Archivo | Qué revisa |
|---|---|
| `test_geometria.py` (10) | Distancias conocidas (0°, 1°, 180°, cruce del antimeridiano), que haversine y producto punto coincidan, que el punto destino recorra la distancia pedida, que los puntos al azar sean uniformes en área, la huella de Veguitto (4.774°) |
| `test_evaluacion.py` (13) | Un satélite en el centro cubre el 100 %; uno lejano, 0 %; la cobertura baja al alejarse; la configuración ideal da justo la cota; un satélite no puede ver dos regiones; dentro de una zona = inválido; justo afuera = válido; separación mínima; orden de Deb; alcanzabilidad de una región bloqueada; cambio de prioridad |
| `test_evolutivo.py` (6) | Misma semilla = mismo resultado; el elitismo nunca empeora la mejor; conteo de evaluaciones; el resultado respeta las restricciones; mejora sobre la población inicial; la búsqueda aleatoria funciona |
