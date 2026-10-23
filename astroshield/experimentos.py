"""Pruebas del Entregable 3. Cada función corre el algoritmo de verdad y devuelve
las condiciones usadas y los resultados medidos, listos para tablas y gráficas.

Ningún número de estos resultados se escribe a mano: todo sale de ejecutar el código.
"""

import numpy as np

from . import geometria as g
from .escenario import Zona, escenario_etapa1, escenario_etapa2
from .evaluacion import Evaluador
from .evolutivo import Configuracion, busqueda_aleatoria, ejecutar

SEMILLA_BASE = 42
SEMILLAS_VARIACION = list(range(100, 120))   # 20 corridas


def _resumen(evaluador, conf):
    rep = evaluador.reporte(conf)
    return {
        "aptitud": round(rep["aptitud"], 4),
        "porcentaje_cota": round(rep["porcentaje_de_la_cota"], 1),
        "valida": rep["valida"],
        "violacion": round(rep["violacion"], 3),
        "regiones_cubiertas": rep["regiones_cubiertas"],
        "suficientemente_buena": rep["suficientemente_buena"],
        "cobertura": {r["region"]: round(r["cobertura"], 3) for r in rep["regiones"]},
        "redundancia": {r["region"]: round(r["redundancia"], 3) for r in rep["regiones"]},
    }


def varias_semillas(escenario, semillas=(42, 43, 44, 45, 46)):
    """Corre el mismo escenario con varias semillas y resume la dispersión."""
    apt, cub, buenas, cov = [], [], 0, []
    for s in semillas:
        ev = Evaluador(escenario)
        r = ejecutar(ev, Configuracion(semilla=s))
        rep = ev.reporte(r.mejor)
        apt.append(rep["aptitud"])
        cub.append(rep["regiones_cubiertas"])
        buenas += rep["suficientemente_buena"]
        cov.append({x["region"]: round(x["cobertura"], 3) for x in rep["regiones"]})
    return {"semillas": list(semillas), "aptitudes": [round(a, 4) for a in apt],
            "minimo": round(min(apt), 4), "mediana": round(float(np.median(apt)), 4), "maximo": round(max(apt), 4),
            "regiones_cubiertas": cub, "suficientemente_buenas": buenas, "coberturas": cov}


def generacion_que_alcanza(historial, objetivo):
    """Primera generación en que la mejor aptitud llega a `objetivo` (o None)."""
    for gen, apt in zip(historial["generacion"], historial["mejor_aptitud"]):
        if apt == apt and apt >= objetivo:   # apt == apt descarta NaN
            return gen
    return None


def margenes(evaluador, conf):
    """Para cada zona: distancia del satélite más cercano y cuánto le sobra al radio."""
    filas = []
    for z in evaluador.escenario.zonas:
        d = g.distancia_angular(np.asarray(conf), z.centro)
        filas.append({"zona": z.nombre, "tipo": z.tipo, "radio": z.radio_grados,
                      "satelite_mas_cercano": int(np.argmin(d)), "distancia": round(float(d.min()), 2),
                      "margen": round(float(d.min() - z.radio_grados), 2)})
    return filas


# ------------------------------------------------------------------ P1 y P2
def prueba_escenario_inicial(semilla=SEMILLA_BASE, cfg=None):
    """P1: qué configuración se obtiene en la etapa 1 y en la etapa 2."""
    salida = {}
    for clave, esc in [("etapa1", escenario_etapa1()), ("etapa2", escenario_etapa2())]:
        ev = Evaluador(esc)
        r = ejecutar(ev, cfg or Configuracion(semilla=semilla))
        salida[clave] = {"escenario": esc.nombre, "evaluador": ev, "resultado": r,
                         "reporte": ev.reporte(r.mejor), "resumen": _resumen(ev, r.mejor),
                         "resumen_inicial": _resumen(ev, r.mejor_inicial),
                         "cota": ev.cota_superior(), "evaluaciones": r.evaluaciones,
                         "segundos": round(r.segundos, 2)}
    return salida


def prueba_evolucion(resultado, cota):
    """P2: cómo cambia la calidad a lo largo de las generaciones."""
    h = resultado.historial
    cortes = [0, 5, 10, 25, 50, 75, 100, len(h["generacion"]) - 1]
    filas = [{"generacion": h["generacion"][i],
              "mejor_aptitud": round(h["mejor_aptitud"][i], 4),
              "promedio_validas": round(h["promedio_aptitud_validas"][i], 4),
              "porcentaje_validas": round(h["porcentaje_validas"][i], 1),
              "regiones_cubiertas": h["regiones_cubiertas_mejor"][i],
              "sigma": round(h["sigma"][i], 2)} for i in cortes]
    return {"tabla": filas,
            "gen_95": generacion_que_alcanza(h, 0.95 * cota),
            "gen_98": generacion_que_alcanza(h, 0.98 * cota),
            "gen_cota": generacion_que_alcanza(h, cota - 1e-9)}


# ------------------------------------------------------------- P3 y P4
def prueba_restricciones(ev2, resultado2, semilla=SEMILLA_BASE):
    """P3 y P4: la solución final respeta zonas y objetos; el sistema detecta violaciones."""
    rng = np.random.default_rng(semilla)
    # (a) márgenes de la solución final
    marg = margenes(ev2, resultado2.mejor)
    # (b) cuántas configuraciones al azar violan las restricciones
    pob = g.puntos_aleatorios(rng, (1000, 8))
    e_az = ev2.evaluar(pob)
    en_zonas, _ = ev2.violaciones_detalladas(pob)
    sats_en_zona = (en_zonas > 0).any(axis=2)
    por_zona = {z.nombre: int((en_zonas[:, :, k] > 0).sum()) for k, z in enumerate(ev2.escenario.zonas)}
    # (c) inyección: meter un satélite de la solución final en cada zona y ver si se detecta
    inyecciones = []
    for z in ev2.escenario.zonas:
        conf = resultado2.mejor.copy()
        conf[7] = z.centro
        rep = ev2.reporte(conf)
        inyecciones.append({"zona": z.nombre, "tipo": z.tipo, "detectada": not rep["valida"],
                            "violacion": round(rep["violacion"], 2),
                            "aptitud_sin_restricciones": round(rep["aptitud"], 4)})
    # (d) la solución de la etapa 1 (sin restricciones), ¿es válida en la etapa 2?
    e1 = Evaluador(escenario_etapa1())
    validas_e1 = []
    for s in SEMILLAS_VARIACION[:10]:
        r1 = ejecutar(e1, Configuracion(semilla=s))
        validas_e1.append(ev2.reporte(r1.mejor)["valida"])
    return {
        "margenes": marg,
        "azar_invalidas_pct": round(float((~e_az.validas).mean() * 100), 1),
        "azar_satelites_en_zona_pct": round(float(sats_en_zona.mean() * 100), 1),
        "azar_por_zona": por_zona,
        "inyecciones": inyecciones,
        "etapa1_validas_en_etapa2": f"{sum(validas_e1)}/{len(validas_e1)}",
    }


# ------------------------------------------------------------------- P5
def prueba_espacio_reducido(semilla=SEMILLA_BASE):
    """P5: (a) zona nueva sobre el centro de Meseta Saiyan; (b) más y más zonas al azar."""
    base = escenario_etapa2()
    filas = []
    caso_saiyan = {}
    # (a)
    zona_saiyan = Zona("Nube de escombros sobre Meseta Saiyan", 20.5, -89.0, 2.5, "escombros")
    for nombre, esc in [("Etapa 2 (referencia)", base), ("+ zona de 2.5° sobre Meseta Saiyan", base.con_zona(zona_saiyan))]:
        ev = Evaluador(esc)
        r = ejecutar(ev, Configuracion(semilla=semilla))
        rep = ev.reporte(r.mejor)
        saiyan = rep["regiones"][0]
        caso_saiyan = {"evaluador": ev, "resultado": r}
        filas.append({"caso": nombre, **_resumen(ev, r.mejor),
                      "satelites_en_saiyan": len(saiyan["satelites"]),
                      "distancia_mas_cercano_saiyan": round(saiyan["distancia_al_mas_cercano"], 2)})
    # (b) zonas al azar de 6° que no tapan el centro de ninguna región
    rng = np.random.default_rng(semilla)
    centros = np.array([r.centro for r in base.regiones])
    candidatas = []
    while len(candidatas) < 40:
        c = g.puntos_aleatorios(rng, (1,))[0]
        if g.distancia_angular(centros, c).min() > 6.0 + 1.5:
            candidatas.append(c)
    progresivo = []
    for n in [0, 10, 20, 40]:
        esc = base
        for k in range(n):
            esc = esc.con_zona(Zona(f"Zona extra {k + 1}", float(candidatas[k][0]), float(candidatas[k][1]), 6.0, "escombros"),
                               nombre=f"Etapa 2 + {n} zonas extra")
        ev = Evaluador(esc)
        area = _area_prohibida(esc)
        pob = g.puntos_aleatorios(np.random.default_rng(1), (1000, 8))
        validas_azar = float(ev.evaluar(pob).validas.mean() * 100)
        r = ejecutar(ev, Configuracion(semilla=semilla))
        progresivo.append({"zonas_extra": n, "area_prohibida_pct": round(area, 1),
                           "azar_validas_pct": round(validas_azar, 1),
                           "gen_primera_valida": next((gg for gg, p in zip(r.historial["generacion"], r.historial["porcentaje_validas"]) if p > 0), None),
                           **_resumen(ev, r.mejor)})
    cinco = varias_semillas(base.con_zona(zona_saiyan))
    return {"saiyan": filas, "saiyan_5_semillas": cinco, "progresivo": progresivo, "caso_saiyan": caso_saiyan}


def _area_prohibida(esc, n=200000):
    """Porcentaje del área de la esfera (a la altura de órbita) donde no se puede poner un satélite."""
    pts = g.puntos_aleatorios(np.random.default_rng(0), (n,))
    if not esc.zonas:
        return 0.0
    vec = g.a_vector(pts)
    dentro = np.zeros(n, dtype=bool)
    for z in esc.zonas:
        dentro |= (vec @ g.a_vector(np.array(z.centro))) >= np.cos(np.radians(z.radio_grados))
    return float(dentro.mean() * 100)


# ------------------------------------------------------------------- P6
def prueba_condiciones_dificiles(semilla=SEMILLA_BASE):
    """P6: (a) difícil: Objeto B movido sobre Desierto Kami; (b) inviable para una región;
    (c) inviable total: no existe ninguna posición permitida."""
    base = escenario_etapa2()
    casos = {
        "a) Objeto B movido sobre Desierto Kami (radio 5°)":
            base.con(zonas=tuple(z if z.nombre != "Objeto B" else Zona("Objeto B", -25.0, 133.0, 5.0, "ocupada")
                                 for z in base.zonas), nombre="Objeto B sobre Desierto Kami"),
        "b) Zona de 9° sobre Meseta Saiyan":
            base.con_zona(Zona("Bloqueo de Meseta Saiyan", 20.5, -89.0, 9.0, "escombros"), nombre="Meseta Saiyan bloqueada"),
        "c) Todo el planeta prohibido":
            base.con_zona(Zona("Tormenta global", 0.0, 0.0, 180.0, "escombros"), nombre="Sin espacio libre"),
    }
    salida = []
    for nombre, esc in casos.items():
        ev = Evaluador(esc)
        alc = ev.alcanzabilidad()
        r = ejecutar(ev, Configuracion(semilla=semilla))
        rep = ev.reporte(r.mejor)
        salida.append({"caso": nombre, "escenario": esc, "evaluador": ev, "resultado": r,
                       "alcanzabilidad": {k: round(v, 3) for k, v in alc.items()},
                       "resumen": _resumen(ev, r.mejor),
                       "problemas": len(rep["problemas"]),
                       "pct_validas_final": r.historial["porcentaje_validas"][-1],
                       "cinco_semillas": varias_semillas(esc) if not nombre.startswith("c)") else None})
    return salida


# ------------------------------------------------------------------- P7
def prueba_variacion(semillas=SEMILLAS_VARIACION):
    """P7: 20 corridas con semillas distintas + comparación con dos referencias:
    el mismo algoritmo sin reubicación informada y la búsqueda aleatoria."""
    esc = escenario_etapa2()
    filas, ciega, aleatoria = [], [], []
    for s in semillas:
        ev = Evaluador(esc)
        r = ejecutar(ev, Configuracion(semilla=s))
        rep = ev.reporte(r.mejor)
        cota = ev.cota_superior()
        dobles = [x["region"] for x in rep["regiones"] if x["redundancia"] >= 0.95]
        filas.append({"semilla": s, **_resumen(ev, r.mejor), "gen_98": generacion_que_alcanza(r.historial, 0.98 * cota),
                      "segundos": round(r.segundos, 2), "regiones_duplicadas": dobles, "historial": r.historial,
                      "mejor": r.mejor})
        ev_c = Evaluador(esc)
        rc = ejecutar(ev_c, Configuracion(semilla=s, prob_informada=0.0))
        ciega.append(_resumen(ev_c, rc.mejor))
        ev_a = Evaluador(esc)
        m, _, _ = busqueda_aleatoria(ev_a, r.evaluaciones, semilla=s)
        aleatoria.append(_resumen(ev_a, m))

    def stats(lista):
        apt = np.array([x["aptitud"] for x in lista])
        return {"media": round(float(apt.mean()), 4), "desviacion": round(float(apt.std(ddof=1)), 4),
                "minimo": round(float(apt.min()), 4), "maximo": round(float(apt.max()), 4),
                "validas": sum(x["valida"] for x in lista),
                "seis_cubiertas": sum(x["regiones_cubiertas"] == 6 for x in lista),
                "suficientemente_buenas": sum(x["suficientemente_buena"] for x in lista), "corridas": len(lista)}

    return {"filas": filas, "evaluaciones_por_corrida": Configuracion().poblacion * Configuracion().generaciones,
            "estadisticas": {"Evolutivo (informado)": stats(filas), "Evolutivo ciego": stats(ciega),
                             "Búsqueda aleatoria": stats(aleatoria)},
            "ciega": ciega, "aleatoria": aleatoria}


# ------------------------------------------------------------- P8 y P9 propias
def prueba_resiliencia(ev, conf):
    """P8 (propia): qué pasa si falla cada uno de los 8 satélites."""
    base = ev.reporte(conf)
    filas = []
    for s in range(len(conf)):
        resto = np.delete(np.asarray(conf), s, axis=0)
        # Se evalúa con 7 satélites: se usa un escenario de 7 para que la cota sea coherente.
        ev7 = Evaluador(ev.escenario.con(num_satelites=7))
        rep = ev7.reporte(resto)
        perdidas = [r["region"] for r, r0 in zip(rep["regiones"], base["regiones"]) if r0["cubierta"] and not r["cubierta"]]
        region_sat = [r["region"] for r in base["regiones"] if s in r["satelites"]]
        filas.append({"satelite_que_falla": s, "estaba_sobre": region_sat[0] if region_sat else "ninguna",
                      "aptitud": round(rep["aptitud"], 4), "caida": round(base["aptitud"] - rep["aptitud"], 4),
                      "regiones_cubiertas": rep["regiones_cubiertas"], "regiones_perdidas": perdidas})
    return {"aptitud_completa": round(base["aptitud"], 4), "filas": filas}


def prueba_muestreo(soluciones, anillos_densos=(8, 16, 24, 32, 40)):
    """P9 (propia): ¿la cobertura medida con 37 puntos se sostiene con 121 puntos?

    Si la muestra de 37 puntos fuera demasiado optimista, una región "cubierta"
    podría tener huecos que no se ven. Esta prueba busca ese error.
    """
    esc = escenario_etapa2()
    ev37 = Evaluador(esc)
    ev121 = Evaluador(esc.con(anillos_muestra=anillos_densos))
    filas = []
    for etiqueta, conf in soluciones:
        r37 = ev37.reporte(conf)
        r121 = ev121.reporte(conf)
        for a, b in zip(r37["regiones"], r121["regiones"]):
            if abs(a["cobertura"] - b["cobertura"]) > 1e-9 or a["cubierta"] != b["cubierta"]:
                filas.append({"solucion": etiqueta, "region": a["region"],
                              "cobertura_37": round(a["cobertura"], 3), "cobertura_121": round(b["cobertura"], 3),
                              "cubierta_37": a["cubierta"], "cubierta_121": b["cubierta"]})
    return {"puntos_densos": ev121.puntos_por_region, "soluciones_revisadas": len(soluciones),
            "diferencias": filas,
            "cambios_de_estado": sum(f["cubierta_37"] != f["cubierta_121"] for f in filas)}


# ------------------------------------------------------------------ P10
def prueba_cambio_condiciones(ev2, conf_anterior, semilla=SEMILLA_BASE):
    """P10 (sección 3.3): cambian las condiciones; ¿la configuración anterior sigue siendo válida y buena?"""
    base = ev2.escenario
    # El satélite que cubre Llanura Kaio en la solución anterior
    rep = ev2.reporte(conf_anterior)
    sat_kaio = rep["regiones"][3]["satelites"][0]
    pos = conf_anterior[sat_kaio]
    casos = {
        "a) Selva Namek baja de alta a normal": base.con_prioridad("Selva Namek", "normal"),
        "b) Se cierra la zona donde estaba un satélite (2° alrededor del que ve Llanura Kaio)":
            base.con_zona(Zona("Nueva zona cerrada", float(pos[0]), float(pos[1]), 2.0, "escombros"), nombre="Zona nueva sobre Llanura Kaio"),
    }
    salida = []
    for nombre, esc in casos.items():
        ev = Evaluador(esc)
        antes = ev.reporte(conf_anterior)
        r = ejecutar(ev, Configuracion(semilla=semilla))
        despues = ev.reporte(r.mejor)
        salida.append({"caso": nombre, "cota_nueva": round(ev.cota_superior(), 4),
                       "anterior": _resumen(ev, conf_anterior), "nueva": _resumen(ev, r.mejor),
                       "anterior_dobles": [x["region"] for x in antes["regiones"] if x["redundancia"] >= 0.95],
                       "nueva_dobles": [x["region"] for x in despues["regiones"] if x["redundancia"] >= 0.95],
                       "evaluador": ev, "resultado": r})
    return salida
