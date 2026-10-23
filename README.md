# AstroShield — constelación inteligente sobre Veguitto

Algoritmo evolutivo que diseña una constelación de **8 satélites** para observar seis regiones del planeta ficticio **Veguitto**, respetando zonas de escombros espaciales y posiciones ocupadas por otros objetos. El resultado se explora en un globo 3D interactivo.

Práctica de **Fundamentos de Inteligencia Artificial** · Ing. Carlos André Castro Rodríguez · UT Cancún

| Integrante | Parte del proyecto |
|---|---|
| Navarrete Tzuc Jorge | Definición del problema, geometría de la esfera, notebook principal, análisis de resultados |
| Ríos Astudillo Daniel Eduardo | Escenario de Veguitto y función de evaluación (cobertura, restricciones, aptitud) |
| Itza Santizo Jarett Osiel | Algoritmo evolutivo, búsqueda aleatoria de referencia y calibración de parámetros |
| Salinas Beatriz Erick | Visor 3D, gráficas, experimentos y documento de pruebas |

## Resultado principal

| Método (20 semillas, 12,000 evaluaciones cada una) | F media | Corridas con 6/6 regiones |
|---|---|---|
| Algoritmo evolutivo | 1.0390 | 18/20 |
| Algoritmo evolutivo sin reubicación informada | 0.9809 | 4/20 |
| Búsqueda aleatoria | 0.3583 | 0/20 |

La aptitud máxima posible es **1.0462** (ver la cota superior en el Entregable 1). Todos los números salen de ejecutar el código con semillas fijas.

## Entregables

| # | Entregable | Dónde |
|---|---|---|
| 1 | Definición del problema | [docs/01-definicion-del-problema.md](docs/01-definicion-del-problema.md) |
| 2 | Implementación funcional | Paquete [`astroshield/`](astroshield) y notebook [`AstroShield.ipynb`](AstroShield.ipynb) |
| 3 | Pruebas y validación | [docs/03-pruebas-y-validacion.md](docs/03-pruebas-y-validacion.md) + pruebas unitarias en [`pruebas/`](pruebas) |
| 4 | Análisis de resultados | [docs/04-analisis-de-resultados.md](docs/04-analisis-de-resultados.md) |
| 5 | Visualización 3D | **[visor en línea](https://jorgemx546.github.io/astroshield/resultados/astroshield_3d.html)** · `resultados/astroshield_3d.html` (visor principal) · `resultados/globo_*.html` (versiones simples en Plotly) · dentro del notebook |
| 6 | Repositorio | Este repositorio, con su historial de commits |

## Visor 3D

**En línea:** https://jorgemx546.github.io/astroshield/resultados/astroshield_3d.html (GitHub Pages; no hay que descargar nada).

También se puede abrir `resultados/astroshield_3d.html` con doble clic en el navegador (necesita internet la primera vez para cargar Three.js). Todo lo que muestra sale de la ejecución real:

- **Planeta Veguitto** generado por procedimiento: relieve, océanos con reflejo del sol, nubes en movimiento, atmósfera y bioluminiscencia en el lado nocturno.
- **Restricciones** a la altura de la órbita: nubes de escombros (partículas) y objetos ocupados con su zona de exclusión.
- **Satélites** con su cono de visión y su huella en el suelo; en rojo si violan una zona.
- **Línea de tiempo**: reproduce las 150 generaciones (la mejor configuración de cada una). Los satélites se mueven, las regiones cambian de color y la curva de aptitud avanza.
- **7 escenarios**: las dos etapas, espacio reducido, las tres condiciones difíciles o inviables y el cambio de condiciones.
- **Guía**: al elegir una región, el guía vuela hasta ella, la señala y explica sus datos en esa generación (equivalencia, prioridad, satélites que la ven, cobertura, redundancia y si es imposible de cubrir).

Guías incluidos: **Sol** y **Nova**, personajes originales hechos con figuras simples. Con **Agregar modelos (.stl, .obj)** se pueden cargar modelos 3D propios como guías; se procesan y se guardan **solo en el navegador** de quien los carga y no forman parte del repositorio. Para modelos muy pesados está `herramientas/reducir_modelo.py`:

```bash
python herramientas/reducir_modelo.py modelo_original.obj modelo_ligero.stl
```

## Cómo ejecutarlo

Requiere Python 3.10 o superior.

```bash
git clone https://github.com/jorgemx546/astroshield.git
cd astroshield
python -m venv .venv
```

Activar el entorno: en Windows `.venv\Scripts\activate`; en Linux o macOS `source .venv/bin/activate`. Después:

```bash
pip install -r requirements.txt
python -m pytest pruebas            # 29 pruebas unitarias
python correr_experimentos.py       # corre las 10 pruebas, el visor 3D y guarda todo en resultados/ (≈ 2 min)
python calibrar.py                  # repite la calibración de parámetros (≈ 3 min)
```

El notebook `AstroShield.ipynb` se abre con Jupyter o VS Code y se ejecuta de arriba a abajo (≈ 1.5 min).

### En Google Colab

Abrir https://colab.research.google.com/github/jorgemx546/astroshield/blob/main/AstroShield.ipynb y elegir **Entorno de ejecución → Ejecutar todas**. La primera celda clona el repositorio e instala lo necesario; el visor 3D aparece incrustado al final.

### Usarlo desde código

```python
from astroshield.escenario import escenario_etapa2
from astroshield.evaluacion import Evaluador
from astroshield.evolutivo import Configuracion, ejecutar
from astroshield import visualizacion as vz

ev = Evaluador(escenario_etapa2())
r = ejecutar(ev, Configuracion(generaciones=150, semilla=42))
print(ev.reporte(r.mejor))                                   # cobertura, validez, problemas
vz.globo_3d(ev, r.mejor, inicial=r.mejor_inicial).show()     # globo 3D
```

Para probar otras condiciones: `escenario_etapa2().con_zona(Zona(...))` agrega una zona y `.con_prioridad("Desierto Kami", "alta")` cambia una prioridad.

## Estructura

```
astroshield/
├── AstroShield.ipynb          notebook principal, ya ejecutado
├── astroshield/
│   ├── geometria.py           distancias y puntos sobre la esfera
│   ├── escenario.py           Veguitto: regiones, zonas, parámetros
│   ├── evaluacion.py          cobertura, restricciones, aptitud, reporte, alcanzabilidad
│   ├── evolutivo.py           algoritmo genético y búsqueda aleatoria
│   ├── visualizacion.py       globo 3D (Plotly), mapa, gráficas y exportador del visor
│   ├── plantilla_globo.html   visor 3D (Three.js); los datos se insertan al exportar
│   └── experimentos.py        las 10 pruebas del Entregable 3
├── herramientas/              reducir_modelo.py (modelos 3D propios para el visor)
├── pruebas/                   pruebas unitarias (pytest)
├── docs/                      entregables 1, 3 y 4
├── resultados/                globos HTML, imágenes y resumen.json
├── correr_experimentos.py
├── calibrar.py
└── requirements.txt
```

## Supuestos del modelo

- Veguitto es una esfera de 5,200 km de radio (planeta ficticio definido por el equipo).
- Los satélites son puntos fijos a 600 km de altitud: no se simula la órbita.
- Un satélite ve un círculo de 4.77° (≈ 433 km) alrededor del punto bajo él.
- Las coordenadas, prioridades, zonas y el radio de 300 km son los del enunciado.

## Uso de inteligencia artificial

Usamos **Claude (Anthropic), mediante Claude Code**, como asistente para:

- Proponer la estructura del código y escribir una primera versión de los módulos, las pruebas y los documentos.
- Calcular la geometría de la huella del sensor y la cota superior de la aptitud.
- Programar el visor 3D (shaders del planeta, guías y línea de tiempo).
- Detectar que la versión inicial del algoritmo dejaba regiones sin cubrir y proponer la reubicación informada.

Cómo se verificó lo generado:

- **29 pruebas unitarias** con casos de resultado conocido: distancias exactas en la esfera, un satélite en el centro de una región cubre el 100 %, la configuración ideal da exactamente la cota superior, un satélite dentro de una zona se marca inválido, misma semilla produce el mismo resultado.
- **Comparación contra referencias** (búsqueda aleatoria y versión ciega) con el mismo número de evaluaciones, para comprobar que el algoritmo aporta.
- **Prueba P9**, diseñada para buscar un error de nuestra propia implementación (el muestreo de 37 puntos); encontró una sobreestimación de 1.7 % en un caso.
- Todos los números de los documentos se revisaron contra la salida real del notebook y de `resultados/resumen.json`; ninguno se escribió a mano.

Revisión de cada integrante sobre su parte *(cada quien completa la suya)*:

- Navarrete Tzuc Jorge: con el equipo decidimos usar el planeta Veguitto, como pidió el profe, pero dejando las coordenadas y prioridades del enunciado. Yo organicé qué le tocaba a cada quien. Abrí el visor 3D en mi navegador y le encontré dos problemas: uno de los modelos de guía salía acostado y se veía demasiado brillante. Los reporté y se corrigieron antes de entregar. Al final junté las partes de todos y revisé que el repositorio tuviera los seis entregables.
- Ríos Astudillo Daniel Eduardo: *(pendiente)*
- Itza Santizo Jarett Osiel: *(pendiente)*
- Salinas Beatriz Erick: *(pendiente)*
