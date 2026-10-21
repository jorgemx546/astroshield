"""Geometría sobre una esfera.

Todas las posiciones se manejan como (latitud, longitud) en grados.
Las distancias se dan como ángulo central en grados, así no dependen
del radio del planeta; para pasarlas a km se multiplica por el radio.
"""

import numpy as np


def a_vector(latlon):
    """Convierte (lat, lon) en grados a vectores unitarios (x, y, z).

    Acepta cualquier forma (..., 2) y devuelve (..., 3).
    """
    latlon = np.asarray(latlon, dtype=float)
    lat = np.radians(latlon[..., 0])
    lon = np.radians(latlon[..., 1])
    cos_lat = np.cos(lat)
    return np.stack([cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)], axis=-1)


def distancia_angular(a, b):
    """Ángulo central en grados entre dos posiciones (o arreglos de posiciones).

    Usa la fórmula de haversine, que es estable para distancias pequeñas.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    lat1, lon1 = np.radians(a[..., 0]), np.radians(a[..., 1])
    lat2, lon2 = np.radians(b[..., 0]), np.radians(b[..., 1])
    h = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return np.degrees(2 * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0))))


def angulos_entre(vec_a, vec_b):
    """Matriz de ángulos centrales (grados) entre dos conjuntos de vectores unitarios.

    vec_a: (..., n, 3) y vec_b: (m, 3)  ->  (..., n, m)
    """
    cosenos = np.clip(vec_a @ vec_b.T, -1.0, 1.0)
    return np.degrees(np.arccos(cosenos))


def normalizar(latlon):
    """Deja la latitud en [-90, 90] y la longitud en [-180, 180).

    Si una latitud pasa del polo, "da la vuelta" al otro lado del planeta.
    """
    latlon = np.array(latlon, dtype=float)
    lat = latlon[..., 0]
    lon = latlon[..., 1]
    lat = (lat + 90.0) % 360.0 - 90.0          # ahora en [-90, 270)
    paso_polo = lat > 90.0
    lat = np.where(paso_polo, 180.0 - lat, lat)
    lon = np.where(paso_polo, lon + 180.0, lon)
    lon = (lon + 180.0) % 360.0 - 180.0
    latlon[..., 0] = lat
    latlon[..., 1] = lon
    return latlon


def destino(origen, rumbo, distancia):
    """Punto al que se llega desde `origen` avanzando `distancia` grados con `rumbo` grados.

    El rumbo se mide desde el norte, en sentido horario. Funciona con arreglos.
    """
    origen = np.asarray(origen, dtype=float)
    lat1 = np.radians(origen[..., 0])
    lon1 = np.radians(origen[..., 1])
    theta = np.radians(rumbo)
    delta = np.radians(distancia)
    lat2 = np.arcsin(np.sin(lat1) * np.cos(delta) + np.cos(lat1) * np.sin(delta) * np.cos(theta))
    lon2 = lon1 + np.arctan2(
        np.sin(theta) * np.sin(delta) * np.cos(lat1),
        np.cos(delta) - np.sin(lat1) * np.sin(lat2),
    )
    resultado = np.stack([np.degrees(lat2), np.degrees(lon2)], axis=-1)
    return normalizar(resultado)


def puntos_aleatorios(rng, forma):
    """Posiciones uniformes sobre la esfera (no se amontonan en los polos).

    `forma` es la forma del arreglo sin la última dimensión; devuelve forma + (2,).
    """
    u = rng.uniform(-1.0, 1.0, size=forma)
    lat = np.degrees(np.arcsin(u))
    lon = rng.uniform(-180.0, 180.0, size=forma)
    return np.stack([lat, lon], axis=-1)


def circulo(centro, radio, n=90):
    """Contorno de un círculo sobre la esfera: n+1 puntos (cerrado)."""
    rumbos = np.linspace(0.0, 360.0, n + 1)
    centros = np.broadcast_to(np.asarray(centro, dtype=float), (n + 1, 2))
    return destino(centros, rumbos, np.full(n + 1, radio))


def muestras_disco(centro, radio, anillos=(6, 12, 18)):
    """Puntos de muestra de un disco: el centro y anillos igualmente espaciados.

    Con los anillos por defecto da 1 + 6 + 12 + 18 = 37 puntos.
    """
    puntos = [np.asarray(centro, dtype=float)]
    k = len(anillos)
    for i, cantidad in enumerate(anillos, start=1):
        r = radio * i / k
        # Se gira cada anillo medio paso para que los puntos no queden alineados.
        rumbos = (np.arange(cantidad) + 0.5 * (i % 2)) * 360.0 / cantidad
        centros = np.broadcast_to(np.asarray(centro, dtype=float), (cantidad, 2))
        puntos.extend(destino(centros, rumbos, np.full(cantidad, r)))
    return np.array(puntos)


def semiangulo_huella(radio_planeta, altitud, semiangulo_sensor):
    """Ángulo central (grados) de la huella de un sensor que mira al nadir.

    λ = arcsen((R + h) / R · sen η) − η. Si el sensor alcanza a ver el horizonte,
    la huella llega hasta el horizonte geométrico.
    """
    R, h = float(radio_planeta), float(altitud)
    eta = np.radians(semiangulo_sensor)
    s = (R + h) / R * np.sin(eta)
    if s >= 1.0:
        return float(np.degrees(np.arccos(R / (R + h))))
    return float(np.degrees(np.arcsin(s) - eta))
