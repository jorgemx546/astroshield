"""Evaluación de configuraciones: cobertura, redundancia, restricciones y aptitud.

Una configuración es un arreglo (8, 2) de (lat, lon) en grados.
Una población es un arreglo (P, 8, 2). Todo se calcula de forma vectorizada.
"""

from dataclasses import dataclass

import numpy as np

from . import geometria as g


@dataclass
class Evaluacion:
    """Resultado de evaluar una población de P configuraciones."""
    cobertura: np.ndarray      # (P, R) fracción de puntos vistos por >= 1 satélite
    redundancia: np.ndarray    # (P, R) fracción de puntos vistos por >= 2 satélites
    aptitud: np.ndarray        # (P,)  F = cobertura ponderada + β · redundancia ponderada
    violacion: np.ndarray      # (P,)  grados totales dentro de zonas prohibidas (0 = válida)
    cubiertas: np.ndarray      # (P,)  cuántas regiones superan el umbral

    @property
    def validas(self):
        return self.violacion <= 1e-9


class Evaluador:
    """Precalcula todo lo que no cambia entre configuraciones de un escenario."""

    def __init__(self, escenario):
        self.escenario = e = escenario
        self.huella = g.semiangulo_huella(e.planeta.radio_km, e.altitud_km, e.semiangulo_sensor)
        self.radio_region = float(np.degrees(e.radio_observacion_km / e.planeta.radio_km))
        self._cos_huella = np.cos(np.radians(self.huella))

        muestras = [g.muestras_disco(r.centro, self.radio_region, e.anillos_muestra) for r in e.regiones]
        self.puntos_por_region = muestras[0].shape[0] if muestras else 0
        self.muestras = np.concatenate(muestras) if muestras else np.zeros((0, 2))
        self._vec_muestras = g.a_vector(self.muestras)                      # (M, 3)
        self._region_de_muestra = np.repeat(np.arange(len(e.regiones)), self.puntos_por_region)

        self.pesos = np.array([e.pesos[r.prioridad] for r in e.regiones], dtype=float)
        self.zonas = e.zonas
        self._vec_zonas = g.a_vector([z.centro for z in e.zonas]) if e.zonas else np.zeros((0, 3))
        self._radios_zonas = np.array([z.radio_grados for z in e.zonas], dtype=float)
        self.evaluaciones = 0  # contador de configuraciones evaluadas

    # ------------------------------------------------------------------ cobertura
    def _vistas(self, vec_sat):
        """(P, S, 3) -> (P, M) cuántos satélites ven cada punto de muestra."""
        cosenos = vec_sat @ self._vec_muestras.T                          # (P, S, M)
        return (cosenos >= self._cos_huella).sum(axis=1)

    def _por_region(self, por_punto):
        """(P, M) booleano -> (P, R) fracción por región."""
        P = por_punto.shape[0]
        R = len(self.escenario.regiones)
        return por_punto.reshape(P, R, self.puntos_por_region).mean(axis=2)

    # -------------------------------------------------------------- restricciones
    def violaciones_detalladas(self, poblacion):
        """Devuelve (en_zonas, separacion).

        en_zonas: (P, S, Z) grados que cada satélite se mete en cada zona.
        separacion: (P, S, S) grados que le faltan a cada par para la separación mínima
        (solo el triángulo superior, para no contar dos veces cada par).
        """
        vec = g.a_vector(poblacion)
        P, S = poblacion.shape[:2]
        if len(self.zonas):
            ang = g.angulos_entre(vec, self._vec_zonas)                     # (P, S, Z)
            en_zonas = np.maximum(0.0, self._radios_zonas - ang)
        else:
            en_zonas = np.zeros((P, S, 0))
        cos_pares = np.clip(np.einsum("psk,pqk->psq", vec, vec), -1.0, 1.0)
        ang_pares = np.degrees(np.arccos(cos_pares))
        falta = np.maximum(0.0, self.escenario.separacion_minima - ang_pares)
        separacion = np.triu(falta, k=1)
        return en_zonas, separacion

    # -------------------------------------------------------------------- aptitud
    def evaluar(self, poblacion):
        poblacion = np.asarray(poblacion, dtype=float)
        if poblacion.ndim == 2:
            poblacion = poblacion[None]
        e = self.escenario
        vec = g.a_vector(poblacion)
        vistas = self._vistas(vec)
        cobertura = self._por_region(vistas >= 1)
        redundancia = self._por_region(vistas >= 2)
        suma_pesos = self.pesos.sum()
        aptitud = (cobertura @ self.pesos) / suma_pesos + e.peso_redundancia * (redundancia @ self.pesos) / suma_pesos
        en_zonas, separacion = self.violaciones_detalladas(poblacion)
        violacion = en_zonas.sum(axis=(1, 2)) + separacion.sum(axis=(1, 2))
        cubiertas = (cobertura >= e.umbral_cubierta).sum(axis=1)
        self.evaluaciones += poblacion.shape[0]
        return Evaluacion(cobertura, redundancia, aptitud, violacion, cubiertas)

    def cota_superior(self):
        """Mejor aptitud posible si cada satélite solo puede ver una región.

        Cada región necesita al menos un satélite para cobertura completa; los que
        sobran se usan para duplicar las regiones de mayor peso.
        """
        e = self.escenario
        R = len(e.regiones)
        sobrantes = max(0, e.num_satelites - R)
        pesos_orden = np.sort(self.pesos)[::-1]
        cobertura = 1.0 if e.num_satelites >= R else pesos_orden[: e.num_satelites].sum() / self.pesos.sum()
        redundancia = pesos_orden[: min(sobrantes, R)].sum() / self.pesos.sum()
        return float(cobertura + e.peso_redundancia * redundancia)

    def separacion_minima_entre_regiones(self):
        """Ángulo mínimo entre centros de regiones (para justificar la cota superior)."""
        centros = np.array([r.centro for r in self.escenario.regiones])
        d = g.distancia_angular(centros[:, None, :], centros[None, :, :])
        return float(d[np.triu_indices(len(centros), k=1)].min())

    # ------------------------------------------------------------------- reporte
    def reporte(self, config):
        """Explicación legible de una sola configuración."""
        config = np.asarray(config, dtype=float)
        e = self.escenario
        ev = self.evaluar(config[None])
        self.evaluaciones -= 1  # el reporte no cuenta como trabajo de búsqueda
        vec = g.a_vector(config)
        ang_muestras = g.angulos_entre(vec, self._vec_muestras)              # (S, M)
        ven = ang_muestras <= self.huella
        regiones = []
        for i, r in enumerate(e.regiones):
            sl = slice(i * self.puntos_por_region, (i + 1) * self.puntos_por_region)
            sats = [int(s) for s in np.flatnonzero(ven[:, sl].any(axis=1))]
            c = float(ev.cobertura[0, i])
            regiones.append({
                "region": r.nombre, "prioridad": r.prioridad, "peso": float(self.pesos[i]),
                "cobertura": c, "redundancia": float(ev.redundancia[0, i]),
                "cubierta": bool(c >= e.umbral_cubierta), "satelites": sats,
                "distancia_al_mas_cercano": float(g.distancia_angular(config, r.centro).min()),
            })
        en_zonas, separacion = self.violaciones_detalladas(config[None])
        problemas = []
        for s in range(config.shape[0]):
            for z, zona in enumerate(self.zonas):
                if en_zonas[0, s, z] > 0:
                    problemas.append({"satelite": s, "zona": zona.nombre, "tipo": zona.tipo,
                                      "grados_dentro": float(en_zonas[0, s, z])})
            for q in range(s + 1, config.shape[0]):
                if separacion[0, s, q] > 0:
                    problemas.append({"satelite": s, "zona": f"muy cerca del satélite {q}",
                                      "tipo": "separacion", "grados_dentro": float(separacion[0, s, q])})
        cota = self.cota_superior()
        valida = bool(ev.validas[0])
        return {
            "escenario": e.nombre, "valida": valida, "aptitud": float(ev.aptitud[0]),
            "violacion": float(ev.violacion[0]), "regiones_cubiertas": int(ev.cubiertas[0]),
            "cota_superior": cota, "porcentaje_de_la_cota": float(ev.aptitud[0] / cota * 100),
            "suficientemente_buena": bool(valida and ev.cubiertas[0] == len(e.regiones)
                                          and ev.aptitud[0] >= 0.98 * cota),
            "regiones": regiones, "problemas": problemas,
        }

    # ------------------------------------------------------------ alcanzabilidad
    def alcanzabilidad(self, rumbos=72, pasos=16):
        """Para cada región, qué fracción de sus puntos se podría ver desde ALGUNA
        posición permitida (ignorando cuántos satélites hay).

        Es una cota por región: si da menos de 1, ninguna constelación puede cubrir
        esa región por completo, sin importar lo que haga el algoritmo.
        Se revisan posiciones candidatas en círculos alrededor de cada punto.
        """
        e = self.escenario
        dist = np.linspace(0.0, self.huella * 0.999, pasos)
        rum = np.linspace(0.0, 360.0, rumbos, endpoint=False)
        D, Rb = np.meshgrid(dist, rum)
        D, Rb = D.ravel(), Rb.ravel()
        alcanzable = np.zeros(len(self.muestras), dtype=bool)
        for k, punto in enumerate(self.muestras):
            cand = g.destino(np.broadcast_to(punto, (len(D), 2)), Rb, D)
            if len(self.zonas):
                ang = g.angulos_entre(g.a_vector(cand), self._vec_zonas)
                libre = np.all(ang >= self._radios_zonas, axis=1)
            else:
                libre = np.ones(len(cand), dtype=bool)
            alcanzable[k] = libre.any()
        fr = alcanzable.reshape(len(e.regiones), self.puntos_por_region).mean(axis=1)
        return {r.nombre: float(f) for r, f in zip(e.regiones, fr)}


def orden_deb(aptitud, violacion):
    """Índices de mejor a peor según las reglas de factibilidad de Deb.

    1) válidas antes que inválidas; 2) válidas por aptitud descendente;
    3) inválidas por violación ascendente.
    """
    aptitud = np.asarray(aptitud, dtype=float)
    violacion = np.asarray(violacion, dtype=float)
    invalida = violacion > 1e-9
    clave = np.where(invalida, violacion, -aptitud)
    return np.lexsort((clave, invalida))


def rangos_deb(aptitud, violacion):
    """Rango de cada individuo (0 = el mejor) según `orden_deb`."""
    orden = orden_deb(aptitud, violacion)
    rangos = np.empty_like(orden)
    rangos[orden] = np.arange(len(orden))
    return rangos
