"""Algoritmo evolutivo (genético generacional con elitismo) y búsqueda aleatoria de referencia."""

import time
from dataclasses import dataclass, field

import numpy as np

from . import geometria as g
from .evaluacion import orden_deb, rangos_deb


@dataclass
class Configuracion:
    poblacion: int = 80
    generaciones: int = 150
    torneo: int = 3
    prob_cruza: float = 0.9
    prob_mutacion: float = 0.2      # por satélite
    sigma_inicial: float = 8.0      # grados
    sigma_final: float = 0.3        # grados
    prob_reubicar: float = 0.2      # dentro de una mutación
    prob_informada: float = 0.5     # de las reubicaciones, cuántas caen cerca de una región
    elite: int = 2
    semilla: int | None = None


@dataclass
class Resultado:
    mejor: np.ndarray               # (8, 2) mejor configuración final (reglas de Deb)
    aptitud: float
    violacion: float
    mejor_inicial: np.ndarray       # mejor configuración de la población inicial
    historial: dict = field(default_factory=dict)
    evaluaciones: int = 0
    segundos: float = 0.0
    semilla: int | None = None

    @property
    def valida(self):
        return self.violacion <= 1e-9


def _sigma(cfg, gen):
    """Disminución geométrica de σ: de sigma_inicial a sigma_final."""
    if cfg.generaciones <= 1:
        return cfg.sigma_final
    t = gen / (cfg.generaciones - 1)
    return cfg.sigma_inicial * (cfg.sigma_final / cfg.sigma_inicial) ** t


def _torneo(rng, rangos, cuantos, k):
    """Índices ganadores de `cuantos` torneos de tamaño k (gana el de menor rango)."""
    participantes = rng.integers(0, len(rangos), size=(cuantos, k))
    ganador = np.argmin(rangos[participantes], axis=1)
    return participantes[np.arange(cuantos), ganador]


def _cruza_fondo_comun(rng, padres_a, padres_b, prob):
    """Cada hijo toma 8 satélites al azar del fondo común de sus dos padres (16)."""
    n, S = padres_a.shape[:2]
    fondo = np.concatenate([padres_a, padres_b], axis=1)                 # (n, 2S, 2)
    eleccion = np.argsort(rng.random((n, 2 * S)), axis=1)[:, :S]
    hijos = np.take_along_axis(fondo, eleccion[..., None], axis=1)
    sin_cruza = rng.random(n) >= prob
    hijos[sin_cruza] = padres_a[sin_cruza]
    return hijos


def _puntos_cerca_de_regiones(rng, centros, alcance, k):
    """k posiciones al azar a menos de `alcance` grados de una región elegida al azar."""
    elegidas = centros[rng.integers(0, len(centros), k)]
    rumbo = rng.uniform(0.0, 360.0, k)
    # sqrt(u) reparte los puntos de forma pareja en el área del disco
    distancia = alcance * np.sqrt(rng.random(k))
    return g.destino(elegidas, rumbo, distancia)


def _mutar(rng, hijos, cfg, sigma, centros=None, alcance=0.0):
    """Desplaza o reubica satélites.

    La reubicación "informada" usa el conocimiento del problema: solo cerca de una
    región un satélite puede sumar cobertura. La "ciega" lo manda a cualquier punto.
    """
    n, S = hijos.shape[:2]
    muta = rng.random((n, S)) < cfg.prob_mutacion
    reubica = muta & (rng.random((n, S)) < cfg.prob_reubicar)
    desplaza = muta & ~reubica
    if desplaza.any():
        k = int(desplaza.sum())
        rumbo = rng.uniform(0.0, 360.0, k)
        distancia = np.abs(rng.normal(0.0, sigma, k))
        hijos[desplaza] = g.destino(hijos[desplaza], rumbo, distancia)
    if reubica.any():
        k = int(reubica.sum())
        nuevos = g.puntos_aleatorios(rng, (k,))
        if centros is not None and len(centros) and cfg.prob_informada > 0:
            informada = rng.random(k) < cfg.prob_informada
            if informada.any():
                nuevos[informada] = _puntos_cerca_de_regiones(rng, centros, alcance, int(informada.sum()))
        hijos[reubica] = nuevos
    return hijos


def _registrar(hist, ev, pob, gen, sigma, evaluaciones):
    validas = ev.validas
    orden = orden_deb(ev.aptitud, ev.violacion)
    i = orden[0]
    hist["generacion"].append(gen)
    hist["mejor_aptitud"].append(float(ev.aptitud[i]) if validas[i] else float("nan"))
    hist["promedio_aptitud_validas"].append(float(ev.aptitud[validas].mean()) if validas.any() else float("nan"))
    hist["porcentaje_validas"].append(float(validas.mean() * 100))
    hist["menor_violacion"].append(float(ev.violacion.min()))
    hist["regiones_cubiertas_mejor"].append(int(ev.cubiertas[i]))
    hist["sigma"].append(float(sigma))
    hist["evaluaciones"].append(int(evaluaciones))
    hist["mejor_config"].append(pob[i].copy())   # para reproducir la evolución en el globo 3D


def ejecutar(evaluador, cfg=None, poblacion_inicial=None):
    """Corre el algoritmo evolutivo y devuelve un `Resultado` con su historial."""
    cfg = cfg or Configuracion()
    rng = np.random.default_rng(cfg.semilla)
    S = evaluador.escenario.num_satelites
    centros = np.array([r.centro for r in evaluador.escenario.regiones], dtype=float)
    alcance = evaluador.huella + evaluador.radio_region   # más lejos, un satélite no toca la región
    inicio = time.perf_counter()
    evals_antes = evaluador.evaluaciones

    if poblacion_inicial is None:
        pob = g.puntos_aleatorios(rng, (cfg.poblacion, S))
    else:
        pob = np.array(poblacion_inicial, dtype=float)
    ev = evaluador.evaluar(pob)
    mejor_inicial = pob[orden_deb(ev.aptitud, ev.violacion)[0]].copy()

    hist = {k: [] for k in ["generacion", "mejor_aptitud", "promedio_aptitud_validas", "porcentaje_validas",
                            "menor_violacion", "regiones_cubiertas_mejor", "sigma", "evaluaciones", "mejor_config"]}
    _registrar(hist, ev, pob, 0, _sigma(cfg, 0), evaluador.evaluaciones - evals_antes)

    for gen in range(1, cfg.generaciones):
        sigma = _sigma(cfg, gen)
        rangos = rangos_deb(ev.aptitud, ev.violacion)
        n_hijos = cfg.poblacion - cfg.elite
        a = pob[_torneo(rng, rangos, n_hijos, cfg.torneo)]
        b = pob[_torneo(rng, rangos, n_hijos, cfg.torneo)]
        hijos = _mutar(rng, _cruza_fondo_comun(rng, a, b, cfg.prob_cruza), cfg, sigma, centros, alcance)
        elite = pob[orden_deb(ev.aptitud, ev.violacion)[: cfg.elite]]
        pob = np.concatenate([elite, hijos])
        ev = evaluador.evaluar(pob)
        _registrar(hist, ev, pob, gen, sigma, evaluador.evaluaciones - evals_antes)

    i = orden_deb(ev.aptitud, ev.violacion)[0]
    return Resultado(
        mejor=pob[i].copy(), aptitud=float(ev.aptitud[i]), violacion=float(ev.violacion[i]),
        mejor_inicial=mejor_inicial, historial=hist,
        evaluaciones=evaluador.evaluaciones - evals_antes,
        segundos=time.perf_counter() - inicio, semilla=cfg.semilla,
    )


def busqueda_aleatoria(evaluador, evaluaciones, semilla=None, lote=500):
    """Referencia: genera configuraciones al azar y se queda con la mejor (reglas de Deb).

    Sirve para comprobar que el algoritmo evolutivo hace algo mejor que adivinar
    con el mismo número de evaluaciones.
    """
    rng = np.random.default_rng(semilla)
    S = evaluador.escenario.num_satelites
    mejor, mejor_apt, mejor_vio = None, -np.inf, np.inf
    restantes = evaluaciones
    while restantes > 0:
        n = min(lote, restantes)
        pob = g.puntos_aleatorios(rng, (n, S))
        ev = evaluador.evaluar(pob)
        i = orden_deb(ev.aptitud, ev.violacion)[0]
        candidato = (ev.violacion[i] > 1e-9, ev.violacion[i] if ev.violacion[i] > 1e-9 else -ev.aptitud[i])
        actual = (mejor_vio > 1e-9, mejor_vio if mejor_vio > 1e-9 else -mejor_apt)
        if mejor is None or candidato < actual:
            mejor, mejor_apt, mejor_vio = pob[i].copy(), float(ev.aptitud[i]), float(ev.violacion[i])
        restantes -= n
    return mejor, mejor_apt, mejor_vio
