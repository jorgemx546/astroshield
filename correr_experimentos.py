"""Corre todas las pruebas y guarda los resultados en resultados/.

Uso:  python correr_experimentos.py

Genera:
- resultados/astroshield_3d.html     visor 3D principal (Three.js) con 7 escenarios y la evolución completa
- resultados/resumen.json            todos los números de las pruebas
- resultados/globo_etapa1.html       globo 3D de la etapa 1 (inicial vs final)
- resultados/globo_etapa2.html       globo 3D de la etapa 2 (inicial vs final)
- resultados/globo_*.html            globos de los casos difíciles y de cambio de condiciones
- resultados/*.png                   mapas y gráficas
"""

import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from astroshield import experimentos as ex  # noqa: E402
from astroshield import visualizacion as vz  # noqa: E402

SALIDA = Path(__file__).parent / "resultados"


def _limpio(obj):
    """Quita objetos que no van al JSON (evaluadores, resultados, arreglos grandes)."""
    if isinstance(obj, dict):
        return {k: _limpio(v) for k, v in obj.items()
                if k not in ("evaluador", "resultado", "escenario", "historial", "reporte")}
    if isinstance(obj, (list, tuple)):
        return [_limpio(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return np.round(obj, 4).tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return obj


def guardar_png(nombre):
    plt.savefig(SALIDA / nombre, dpi=120, bbox_inches="tight")
    plt.close("all")


def main():
    SALIDA.mkdir(exist_ok=True)
    inicio = time.perf_counter()
    resumen = {}

    print("P1 escenario inicial…")
    p1 = ex.prueba_escenario_inicial()
    resumen["P1_escenario_inicial"] = p1
    for clave in ("etapa1", "etapa2"):
        d = p1[clave]
        ev, r = d["evaluador"], d["resultado"]
        vz.globo_3d(ev, r.mejor, inicial=r.mejor_inicial).write_html(SALIDA / f"globo_{clave}.html", include_plotlyjs="cdn")
        vz.mapa(ev, r.mejor, inicial=r.mejor_inicial)
        guardar_png(f"mapa_{clave}.png")

    print("P2 evolución…")
    ev2, r2 = p1["etapa2"]["evaluador"], p1["etapa2"]["resultado"]
    resumen["P2_evolucion"] = ex.prueba_evolucion(r2, ev2.cota_superior())
    fig, ejes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
    vz.grafica_evolucion(r2.historial, cota=ev2.cota_superior(), ax=ejes[0],
                         titulo=f"Etapa 2 — evolución de la aptitud (semilla {ex.SEMILLA_BASE})")
    vz.grafica_validez(r2.historial, ax=ejes[1])
    guardar_png("evolucion_etapa2.png")

    print("P3/P4 restricciones…")
    resumen["P3_P4_restricciones"] = ex.prueba_restricciones(ev2, r2)

    print("P5 espacio reducido…")
    resumen["P5_espacio_reducido"] = ex.prueba_espacio_reducido()

    print("P6 condiciones difíciles…")
    p6 = ex.prueba_condiciones_dificiles()
    resumen["P6_condiciones_dificiles"] = p6
    for i, caso in enumerate(p6):
        vz.globo_3d(caso["evaluador"], caso["resultado"].mejor, titulo=caso["caso"]).write_html(
            SALIDA / f"globo_p6_{'abc'[i]}.html", include_plotlyjs="cdn")
        vz.mapa(caso["evaluador"], caso["resultado"].mejor, titulo=caso["caso"])
        guardar_png(f"mapa_p6_{'abc'[i]}.png")

    print("P7 variación entre ejecuciones (20 semillas × 3 métodos)…")
    p7 = ex.prueba_variacion()
    resumen["P7_variacion"] = p7
    vz.grafica_evolucion([(f"semilla {f['semilla']}", f["historial"]) for f in p7["filas"]],
                         cota=ev2.cota_superior(), titulo="Etapa 2 — 20 ejecuciones con semillas distintas")
    plt.gca().get_legend().remove()
    guardar_png("variacion_20_semillas.png")
    _, ax = plt.subplots(figsize=(8, 4))
    nombres = list(p7["estadisticas"].keys())
    datos = [[f["aptitud"] for f in p7["filas"]], [c["aptitud"] for c in p7["ciega"]], [a["aptitud"] for a in p7["aleatoria"]]]
    ax.boxplot(datos, tick_labels=nombres)
    ax.axhline(ev2.cota_superior(), color="black", ls=":", lw=1, label="Cota superior")
    ax.set_ylabel("Aptitud final")
    ax.set_title(f"Mismo número de evaluaciones ({p7['evaluaciones_por_corrida']}) · 20 semillas")
    ax.legend()
    ax.grid(alpha=0.3)
    guardar_png("comparacion_metodos.png")

    print("P8 resiliencia…")
    resumen["P8_resiliencia"] = ex.prueba_resiliencia(ev2, r2.mejor)

    print("P9 muestreo…")
    soluciones = [(f"semilla {f['semilla']}", f["mejor"]) for f in p7["filas"]] + [("semilla 42", r2.mejor)]
    resumen["P9_muestreo"] = ex.prueba_muestreo(soluciones)

    print("P10 cambio de condiciones…")
    p10 = ex.prueba_cambio_condiciones(ev2, r2.mejor)
    resumen["P10_cambio_condiciones"] = p10
    for i, caso in enumerate(p10):
        vz.globo_3d(caso["evaluador"], caso["resultado"].mejor, titulo=caso["caso"], inicial=r2.mejor).write_html(
            SALIDA / f"globo_p10_{'ab'[i]}.html", include_plotlyjs="cdn")

    print("Visor 3D…")
    casos_visor = [
        ("etapa2", "Etapa 2 — escenario del enunciado", "Las 3 zonas de escombros y los 2 objetos ocupados del enunciado. Semilla 42.", ev2, r2),
        ("etapa1", "Etapa 1 — sin restricciones", "Solo las 6 regiones, sin zonas prohibidas. Semilla 42.", p1["etapa1"]["evaluador"], p1["etapa1"]["resultado"]),
        ("p5", "P5 — nube de escombros sobre Meseta Saiyan", "Zona nueva de 2.5° justo encima de Meseta Saiyan: el algoritmo la rodea con dos satélites.",
         resumen["P5_espacio_reducido"]["caso_saiyan"]["evaluador"], resumen["P5_espacio_reducido"]["caso_saiyan"]["resultado"]),
        ("p6a", "P6a — Objeto B sobre Desierto Kami", "Condición difícil: el centro de Desierto Kami ya no se puede ver desde ninguna posición permitida.", p6[0]["evaluador"], p6[0]["resultado"]),
        ("p6b", "P6b — Meseta Saiyan bloqueada", "Inviable para una región: una zona de 9° impide observar Meseta Saiyan.", p6[1]["evaluador"], p6[1]["resultado"]),
        ("p6c", "P6c — todo el planeta prohibido", "Inviable total: no existe ninguna configuración válida; el sistema devuelve la que menos viola y la marca inválida.", p6[2]["evaluador"], p6[2]["resultado"]),
        ("p10b", "P10b — se cierra una zona", "Zona nueva de 2° donde estaba el satélite que veía Llanura Kaio; el algoritmo busca otra configuración.", p10[1]["evaluador"], p10[1]["resultado"]),
    ]
    vz.exportar_visor([vz.datos_visor(*c) for c in casos_visor], SALIDA / "astroshield_3d.html")

    resumen["tiempo_total_segundos"] = round(time.perf_counter() - inicio, 1)
    with open(SALIDA / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(_limpio(resumen), f, ensure_ascii=False, indent=2)
    print(f"Listo en {resumen['tiempo_total_segundos']} s. Resultados en {SALIDA}")


if __name__ == "__main__":
    main()
