"""Calibración de parámetros: corre varias combinaciones con 20 semillas cada una.

Uso:  python calibrar.py      (tarda unos 3 minutos)

Para cada combinación cuenta en cuántas de las 20 corridas la solución final es
"suficientemente buena" (válida, 6/6 regiones y F >= 98 % de la cota).
Guarda la tabla en resultados/calibracion.json.
"""

import json
from pathlib import Path

import numpy as np

from astroshield.escenario import escenario_etapa2
from astroshield.evaluacion import Evaluador
from astroshield.evolutivo import Configuracion, ejecutar

SEMILLAS = range(100, 120)

COMBINACIONES = [
    # (población, generaciones, prob_reubicar, prob_informada, prob_mutacion, sigma_final)
    (60, 150, 0.1, 0.0, 0.2, 0.3),   # versión inicial: reubicación ciega
    (60, 150, 0.1, 0.5, 0.2, 0.3),
    (60, 150, 0.2, 0.5, 0.2, 0.3),
    (60, 150, 0.2, 1.0, 0.2, 0.3),
    (60, 200, 0.2, 0.5, 0.2, 0.3),
    (80, 150, 0.2, 0.5, 0.2, 0.3),   # elegida
    (100, 150, 0.2, 0.5, 0.2, 0.3),
    (80, 250, 0.2, 0.5, 0.2, 0.3),
    (80, 150, 0.2, 0.5, 0.15, 0.3),
    (80, 150, 0.2, 0.5, 0.2, 0.1),
]


def main():
    esc = escenario_etapa2()
    filas = []
    for pob, gen, pr, pi, pm, sf in COMBINACIONES:
        apt, buenas = [], 0
        for s in SEMILLAS:
            ev = Evaluador(esc)
            cfg = Configuracion(poblacion=pob, generaciones=gen, prob_reubicar=pr, prob_informada=pi,
                                prob_mutacion=pm, sigma_final=sf, semilla=s)
            r = ejecutar(ev, cfg)
            rep = ev.reporte(r.mejor)
            apt.append(rep["aptitud"])
            buenas += rep["suficientemente_buena"]
        fila = {"poblacion": pob, "generaciones": gen, "prob_reubicar": pr, "prob_informada": pi,
                "prob_mutacion": pm, "sigma_final": sf, "evaluaciones": pob * gen,
                "aptitud_media": round(float(np.mean(apt)), 4), "aptitud_minima": round(float(np.min(apt)), 4),
                "suficientemente_buenas": f"{buenas}/{len(SEMILLAS)}"}
        filas.append(fila)
        print(fila)
    salida = Path(__file__).parent / "resultados" / "calibracion.json"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
