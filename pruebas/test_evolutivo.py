import numpy as np
import pytest

from astroshield.escenario import escenario_etapa1, escenario_etapa2
from astroshield.evaluacion import Evaluador
from astroshield.evolutivo import Configuracion, busqueda_aleatoria, ejecutar

RAPIDA = dict(poblacion=30, generaciones=40)


def test_misma_semilla_mismo_resultado():
    cfg = Configuracion(semilla=7, **RAPIDA)
    a = ejecutar(Evaluador(escenario_etapa2()), cfg)
    b = ejecutar(Evaluador(escenario_etapa2()), cfg)
    assert np.array_equal(a.mejor, b.mejor)
    assert a.aptitud == b.aptitud


def test_el_mejor_nunca_empeora_por_el_elitismo():
    r = ejecutar(Evaluador(escenario_etapa2()), Configuracion(semilla=3, **RAPIDA))
    mejores = np.array(r.historial["mejor_aptitud"])
    validos = ~np.isnan(mejores)
    # una vez que aparece una válida, la mejor aptitud no baja
    primeras = np.argmax(validos)
    serie = mejores[primeras:]
    assert np.all(np.diff(serie) >= -1e-12)


def test_cuenta_las_evaluaciones():
    cfg = Configuracion(semilla=1, **RAPIDA)
    r = ejecutar(Evaluador(escenario_etapa1()), cfg)
    assert r.evaluaciones == cfg.poblacion * cfg.generaciones
    assert len(r.historial["mejor_aptitud"]) == cfg.generaciones


def test_resultado_final_respeta_las_restricciones():
    ev = Evaluador(escenario_etapa2())
    r = ejecutar(ev, Configuracion(semilla=11, **RAPIDA))
    rep = ev.reporte(r.mejor)
    assert rep["valida"], rep["problemas"]
    assert r.mejor.shape == (8, 2)


def test_mejora_respecto_a_la_poblacion_inicial():
    ev = Evaluador(escenario_etapa2())
    r = ejecutar(ev, Configuracion(semilla=5, **RAPIDA))
    inicial = ev.reporte(r.mejor_inicial)["aptitud"]
    assert r.aptitud > inicial


def test_busqueda_aleatoria_devuelve_una_configuracion():
    mejor, apt, vio = busqueda_aleatoria(Evaluador(escenario_etapa1()), 1000, semilla=0)
    assert mejor.shape == (8, 2)
    assert 0.0 <= apt <= 1.1
