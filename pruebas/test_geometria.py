import numpy as np
import pytest

from astroshield import geometria as g


def test_distancia_cero_y_antipoda():
    assert g.distancia_angular([10, 20], [10, 20]) == pytest.approx(0.0)
    assert g.distancia_angular([0, 0], [0, 180]) == pytest.approx(180.0)
    assert g.distancia_angular([90, 0], [-90, 0]) == pytest.approx(180.0)


def test_distancia_un_grado_en_el_ecuador():
    assert g.distancia_angular([0, 0], [0, 1]) == pytest.approx(1.0)


def test_distancia_cruza_antimeridiano():
    # 179° y -179° están a 2° de distancia, no a 358°.
    assert g.distancia_angular([0, 179], [0, -179]) == pytest.approx(2.0)


def test_vector_y_haversine_coinciden():
    rng = np.random.default_rng(0)
    a = g.puntos_aleatorios(rng, (50,))
    b = g.puntos_aleatorios(rng, (50,))
    por_haversine = g.distancia_angular(a, b)
    va, vb = g.a_vector(a), g.a_vector(b)
    por_vectores = np.degrees(np.arccos(np.clip(np.sum(va * vb, axis=1), -1, 1)))
    assert np.allclose(por_haversine, por_vectores, atol=1e-6)


def test_destino_recorre_la_distancia_pedida():
    rng = np.random.default_rng(1)
    origen = g.puntos_aleatorios(rng, (100,))
    rumbos = rng.uniform(0, 360, 100)
    dist = rng.uniform(0, 40, 100)
    llegada = g.destino(origen, rumbos, dist)
    assert np.allclose(g.distancia_angular(origen, llegada), dist, atol=1e-6)


def test_normalizar_pasa_el_polo():
    lat, lon = g.normalizar([95.0, 10.0])
    assert lat == pytest.approx(85.0)
    assert lon == pytest.approx(-170.0)
    lat, lon = g.normalizar([0.0, 200.0])
    assert lon == pytest.approx(-160.0)


def test_puntos_aleatorios_son_uniformes_en_area():
    # En una esfera, la mitad del área está entre -30° y 30° de latitud.
    rng = np.random.default_rng(2)
    p = g.puntos_aleatorios(rng, (20000,))
    fraccion = np.mean(np.abs(p[:, 0]) <= 30)
    assert fraccion == pytest.approx(0.5, abs=0.02)


def test_muestras_disco_37_puntos_dentro_del_radio():
    m = g.muestras_disco([20.5, -89.0], 3.3)
    assert m.shape == (37, 2)
    d = g.distancia_angular(m, [20.5, -89.0])
    assert d.max() == pytest.approx(3.3, abs=1e-6)


def test_huella_veguitto():
    # R = 5200 km, h = 600 km, sensor de 35° -> ≈ 4.77°
    assert g.semiangulo_huella(5200, 600, 35) == pytest.approx(4.7738, abs=1e-3)


def test_huella_crece_con_la_altitud():
    assert g.semiangulo_huella(5200, 800, 35) > g.semiangulo_huella(5200, 600, 35)
