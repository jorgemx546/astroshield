# Entregable 4 — Análisis de resultados

Las respuestas se apoyan en las pruebas de [03-pruebas-y-validacion.md](03-pruebas-y-validacion.md) (P1 a P10). Todos los números salen de ejecutar el programa.

## ¿Qué tan bien se observan las regiones en la configuración final?

En el escenario de la etapa 2, la configuración final (semilla 42) ve las **6 regiones al 100 %** según la muestra de 37 puntos. Las dos regiones de prioridad alta, Meseta Saiyan y Selva Namek, las ven **dos satélites** cada una. Su aptitud es 1.0462, igual a la cota superior, así que con este modelo no existe una configuración mejor (P1).

En 20 corridas distintas, 18 cubren las 6 regiones; las otras 2 dejan Desierto Kami al 81 % y al 95 % (P7). La revisión con 121 puntos (P9) muestra que el "100 %" es una estimación: en 1 de 21 soluciones había un hueco de 1.7 % que la muestra chica no veía.

## ¿Cómo cambió la calidad durante el proceso evolutivo?

La mejor configuración de la población inicial no cubría ninguna región (F = 0.39). La calidad subió rápido al principio (F = 0.92 en la generación 25) y después por escalones, uno por cada región que entraba en una huella. Las 6 regiones quedaron cubiertas cerca de la generación 75; la mejora final (generaciones 75 a 130) fue ajuste fino para la redundancia, cuando la mutación ya daba pasos chicos (P2).

La diferencia entre la mejor aptitud y el promedio de la población no se cierra: la mutación y la reubicación mantienen variedad a propósito, para no estancarse.

## ¿Qué diferencias se encontraron entre distintas ejecuciones?

La **calidad** casi no cambia: F media = 1.039, desviación = 0.006, mínimo 1.019 (P7). La **forma** sí cambia. Hay muchas constelaciones casi igual de buenas, que se distinguen sobre todo por dónde quedan los dos satélites sobrantes (Selva Namek, Meseta Saiyan o una región media). Solo 2 de 20 corridas encontraron la combinación exacta de la cota. También cambia la velocidad: el 98 % de la cota se alcanza entre la generación 48 y la 107.

Esa variación es normal en un algoritmo estocástico. Por eso las conclusiones se sacaron de 20 corridas, no de una.

## ¿Qué efecto tuvieron las restricciones espaciales sobre la solución?

Depende de dónde estén:

- **En el escenario del enunciado, ningún efecto sobre el óptimo.** Las zonas de desechos y los objetos están lejos de las regiones: las 10 soluciones obtenidas sin restricciones también eran válidas con restricciones (P3). Su efecto se ve en la búsqueda, porque el 21.5 % de las configuraciones al azar son inválidas y no pueden ganar.
- **Cerca de una región, el efecto es fuerte.** Una zona de 2.5° sobre Meseta Saiyan obliga a usar dos satélites alrededor de ella; esa redundancia se pierde en otra parte y ninguna corrida llega a "suficientemente buena" (P5a).
- **Al reducir el espacio en general**, la búsqueda se vuelve más difícil: con 40 zonas extra solo el 33 % de las configuraciones al azar es válida. La solución final siempre fue válida y su calidad bajó poco: 98.7 % de la cota (P5b).

En todos los casos la solución final **nunca** quedó dentro de una zona cuando existía una alternativa válida, y cada satélite metido a propósito en una zona se detectó (P3, P4).

## ¿Qué sucede cuando el sistema no puede satisfacer todas las condiciones?

Hay dos situaciones distintas y el sistema las distingue (P6):

1. **Una región no se puede observar** (zona de 9° encima de Meseta Saiyan). El análisis de alcanzabilidad dice que la región es inalcanzable. El algoritmo entrega una configuración **válida** que cubre las otras 5 y reporta la región al 0 %, sin fingir que está cubierta.
2. **No existe ninguna configuración válida** (todo el planeta prohibido). El sistema devuelve la configuración que **menos viola**, la marca **inválida** (violación 8.37°) y lista los 17 problemas. No se presenta como solución.

Cuando la condición es difícil pero no imposible (Objeto B encima de Desierto Kami), el algoritmo se queda corto: Kami podría verse hasta al 97.3 %, pero el algoritmo la deja entre 0 % y 62 % según la semilla. Eso lleva a la siguiente pregunta.

## ¿Qué limitaciones tiene el criterio utilizado para evaluar las configuraciones?

1. **Permite abandonar una región de prioridad baja.** Con pesos 3-2-1, cubrir la mitad de Desierto Kami (peso 1) vale menos que dar redundancia completa a una región alta. Cuando Kami es difícil, el algoritmo la sacrifica (P6a). Si la organización quisiera "todas las regiones al menos parcialmente", habría que agregarlo como restricción o con un término que castigue las regiones en 0 %.
2. **La cobertura es una estimación por muestreo.** 37 puntos por región pueden sobreestimar o subestimar la cobertura real; lo medimos en P9 (diferencias de hasta 2 %).
3. **La cota superior no considera las restricciones.** Supone un satélite por región; si una zona tapa una región, la cota ya no es alcanzable y el "% de la cota" subestima la solución (P5).
4. **El modelo es estático.** Los satélites son puntos fijos; no se simula la órbita, así que "cubierta" significa "vista en este instante", no "vista todo el tiempo".
5. **Los pesos y el factor de redundancia (0.10) son decisiones del equipo.** Con otros valores el algoritmo preferiría otras constelaciones; P10a muestra que con solo cambiar una prioridad cambia dónde conviene la redundancia.
6. **La redundancia solo protege a 2 regiones.** Con 8 satélites y 6 regiones, 4 regiones dependen de un solo satélite (P8).

## ¿Qué evidencia permite afirmar que una solución es mejor que otra?

Usamos cinco evidencias, todas medidas por el programa:

1. **Validez primero.** Una solución inválida nunca es mejor que una válida, sin importar su aptitud (reglas de Deb). Ejemplo: en P10b la configuración anterior tiene F = 1.0462 pero es inválida, y la nueva, con F = 1.0385 y válida, es mejor.
2. **Aptitud F**, que resume la cobertura pesada por prioridad más la redundancia.
3. **Distancia a la cota superior.** Como sabemos que F no puede pasar de 1.0462 en el escenario base, podemos decir que una solución al 100 % no se puede mejorar con este modelo. Que el algoritmo deje de mejorar no basta para afirmarlo.
4. **Comparación contra referencias con el mismo trabajo.** Con 12,000 evaluaciones, el evolutivo logra F media = 1.039, el evolutivo ciego 0.981 y la búsqueda aleatoria 0.358 (P7). La diferencia es mucho mayor que la variación entre semillas.
5. **Pruebas que miran más allá de F**: resiliencia ante la falla de un satélite (P8) y cobertura con muestra densa (P9). Dos soluciones con la misma F pueden ser distintas en estas medidas.

## Conclusión

El algoritmo evolutivo resuelve el escenario: en 18 de 20 corridas encuentra una constelación válida que cubre las 6 regiones a menos del 2 % de la cota superior, y nunca acepta una configuración que viole las restricciones si existe otra. Las pruebas también mostraron sus límites. El criterio puede sacrificar la región de menor prioridad, la cobertura es una estimación y el modelo no simula órbitas. Por eso, una constelación es "buena" en este proyecto **porque cumple las restricciones y se mide contra una cota y contra referencias**, no porque se vea bien en el globo.
