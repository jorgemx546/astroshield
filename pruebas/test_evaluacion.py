import numpy as np
import pytest

from astroshield import geometria as g
from astroshield.escenario import Zona, escenario_etapa1, escenario_etapa2
from astroshield.evaluacion import Evaluador, orden_deb


def centros(escenario):
    return np.array([r.centro for r in escenario.regiones])


def config_ideal(escenario):
    """Un satélite en el centro de cada región + 2 extra junto a las regiones altas."""
    c = centros(escenario)
    extra = g.destino(c[:2], np.array([90.0, 90.0]), np.array([1.0, 1.0]))
    return np.vstack([c, extra])


def test_huella_y_radio_de_region():
    ev = Evaluador(escenario_etapa1())
    assert ev.huella == pytest.approx(4.7738, abs=1e-3)
    assert ev.radio_region == pytest.approx(3.3055, abs=1e-3)
    assert ev.puntos_por_region == 37


def test_satelite_en_el_centro_cubre_toda_la_region():
    e = escenario_etapa1()
    ev = Evaluador(e)
    lejos = np.array([[-80.0, 0.0]] * 7)
    config = np.vstack([[e.regiones[0].centro], lejos + np.arange(7)[:, None] * [0, 10]])
    res = ev.evaluar(config)
    assert res.cobertura[0, 0] == pytest.approx(1.0)
    assert np.all(res.cobertura[0, 1:] == 0)


def test_satelite_lejano_no_cubre_nada():
    ev = Evaluador(escenario_etapa1())
    config = g.destino(np.array([[-80.0, 0.0]] * 8), np.arange(8) * 45.0, np.full(8, 5.0))
    assert ev.evaluar(config).aptitud[0] == pytest.approx(0.0)


def test_la_cobertura_baja_al_alejar_el_satelite():
    e = escenario_etapa1()
    ev = Evaluador(e)
    resto = g.destino(np.array([[-80.0, 0.0]] * 7), np.arange(7) * 50.0, np.full(7, 5.0))
    coberturas = []
    for d in [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 9.0]:
        sat = g.destino(np.array(e.regiones[0].centro), 45.0, d)
        coberturas.append(ev.evaluar(np.vstack([sat, resto])).cobertura[0, 0])
    assert all(a >= b for a, b in zip(coberturas, coberturas[1:]))
    assert coberturas[0] == 1.0 and coberturas[-1] == 0.0


def test_configuracion_ideal_alcanza_la_cota():
    e = escenario_etapa1()
    ev = Evaluador(e)
    rep = ev.reporte(config_ideal(e))
    assert rep["valida"]
    assert rep["regiones_cubiertas"] == 6
    assert rep["aptitud"] == pytest.approx(ev.cota_superior())
    assert ev.cota_superior() == pytest.approx(1 + 0.1 * 6 / 13)


def test_un_satelite_no_puede_ver_dos_regiones():
    # La cota superior supone esto: regiones separadas más de 2·(huella + radio).
    ev = Evaluador(escenario_etapa1())
    assert ev.separacion_minima_entre_regiones() > 2 * (ev.huella + ev.radio_region)


def test_satelite_dentro_de_zona_es_invalido():
    e = escenario_etapa2()
    ev = Evaluador(e)
    config = config_ideal(e)
    config[7] = [45.0, -35.0]  # centro del Cinturón de escombros Norte (radio 12°)
    rep = ev.reporte(config)
    assert not rep["valida"]
    assert rep["violacion"] == pytest.approx(12.0)
    assert rep["problemas"][0]["zona"] == "Cinturón de escombros Norte"


def test_satelite_en_objeto_ocupado_es_invalido():
    e = escenario_etapa2()
    ev = Evaluador(e)
    config = config_ideal(e)
    config[7] = [10.0, 45.0]  # Objeto A
    assert not ev.reporte(config)["valida"]


def test_satelite_justo_afuera_de_la_zona_es_valido():
    e = escenario_etapa2()
    ev = Evaluador(e)
    config = config_ideal(e)
    config[7] = g.destino(np.array([45.0, -35.0]), 0.0, 12.01)
    assert ev.reporte(config)["valida"]


def test_satelites_demasiado_juntos_son_invalidos():
    e = escenario_etapa1()
    ev = Evaluador(e)
    config = config_ideal(e)
    config[7] = g.destino(np.array(config[0]), 0.0, 0.5)  # a 0.5° del satélite 0
    rep = ev.reporte(config)
    assert not rep["valida"]
    assert rep["problemas"][0]["tipo"] == "separacion"
    assert rep["violacion"] == pytest.approx(0.5, abs=1e-6)


def test_orden_deb_valida_antes_que_invalida():
    aptitud = np.array([0.2, 1.0, 0.5, 0.9])
    violacion = np.array([0.0, 3.0, 0.0, 1.0])
    # válidas por aptitud (2, 0), luego inválidas por violación (3, 1)
    assert list(orden_deb(aptitud, violacion)) == [2, 0, 3, 1]


def test_alcanzabilidad_detecta_region_bloqueada():
    e = escenario_etapa2()
    bloqueo = Zona("Bloqueo total", 20.5, -89.0, 9.0, "escombros")
    alc = Evaluador(e.con_zona(bloqueo)).alcanzabilidad()
    assert alc["Meseta Saiyan"] == 0.0
    assert alc["Selva Namek"] == 1.0


def test_cambio_de_prioridad_cambia_los_pesos():
    e = escenario_etapa1().con_prioridad("Desierto Kami", "alta")
    ev = Evaluador(e)
    assert ev.pesos[-1] == 3.0
