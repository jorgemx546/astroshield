"""Visualización: globo 3D interactivo de Veguitto, mapa plano y curvas de evolución.

Todo se dibuja a partir de una configuración real y de su reporte de evaluación,
nunca de datos fijos: lo que se ve es lo que calculó el algoritmo.
"""

import numpy as np

from . import geometria as g

COLOR_REGION = {"cubierta": "#2ecc71", "parcial": "#f5b041", "sin": "#e74c3c"}
COLOR_ZONA = {"escombros": "#c0392b", "ocupada": "#8e44ad", "separacion": "#7f8c8d"}
COLOR_SAT = {"final": "#00e5ff", "inicial": "#ffffff"}


def _estado_region(r, umbral):
    if r["cobertura"] >= umbral:
        return "cubierta"
    return "parcial" if r["cobertura"] > 0 else "sin"


def _xyz(latlon, radio=1.0):
    v = g.a_vector(latlon) * radio
    return v[..., 0], v[..., 1], v[..., 2]


def _relieve(lat, lon):
    """Relieve procedural (inventado) de Veguitto: suma de ondas fija, sin azar."""
    la, lo = np.radians(lat), np.radians(lon)
    return (np.sin(3 * lo + 0.7) * np.cos(2 * la)
            + 0.6 * np.sin(5 * lo - 2 * la + 1.3)
            + 0.4 * np.cos(7 * la + 2 * lo)
            + 0.3 * np.sin(11 * lo + 5 * la + 0.4))


# --------------------------------------------------------------------- globo 3D
def globo_3d(evaluador, config, titulo=None, inicial=None):
    """Figura de Plotly con el planeta, regiones, zonas, satélites y huellas.

    Si se pasa `inicial`, agrega botones para alternar entre la configuración
    inicial y la final.
    """
    import plotly.graph_objects as go

    e = evaluador.escenario
    R_orbita = (e.planeta.radio_km + e.altitud_km) / e.planeta.radio_km
    fig = go.Figure()

    # Planeta
    lat = np.linspace(-90, 90, 91)
    lon = np.linspace(-180, 180, 181)
    LON, LAT = np.meshgrid(lon, lat)
    X, Y, Z = _xyz(np.stack([LAT, LON], axis=-1))
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, surfacecolor=_relieve(LAT, LON), showscale=False, hoverinfo="skip",
        colorscale=[[0.0, "#16324f"], [0.45, "#2a6f97"], [0.5, "#7a9e7e"], [0.7, "#b08d57"], [1.0, "#e9d8a6"]],
        lighting=dict(ambient=0.55, diffuse=0.8, roughness=0.9), name=e.planeta.nombre,
    ))

    # Zonas prohibidas: casquete a la altura de la órbita + contorno sobre la superficie
    for z in e.zonas:
        borde = g.circulo(z.centro, z.radio_grados, 72)
        for radio, ancho, guion in [(R_orbita, 5, "solid"), (1.003, 2, "dot")]:
            x, y, zz = _xyz(borde, radio)
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=zz, mode="lines", line=dict(color=COLOR_ZONA[z.tipo], width=ancho, dash=guion),
                name=z.nombre, legendgroup=z.nombre, showlegend=radio == R_orbita, hoverinfo="name",
            ))
        cx, cy, cz = _xyz(np.array([z.centro]), R_orbita)
        fig.add_trace(go.Scatter3d(
            x=cx, y=cy, z=cz, mode="markers+text", text=[z.nombre], textfont=dict(color=COLOR_ZONA[z.tipo], size=10),
            marker=dict(size=4 if z.tipo == "escombros" else 7, color=COLOR_ZONA[z.tipo],
                        symbol="x" if z.tipo == "escombros" else "square"),
            legendgroup=z.nombre, showlegend=False,
            hovertext=f"{z.nombre} · {z.tipo} · radio {z.radio_grados}°", hoverinfo="text",
        ))

    indices_por_conf = {}
    confs = [("final", config)] + ([("inicial", inicial)] if inicial is not None else [])
    for clave, conf in confs:
        rep = evaluador.reporte(conf)
        inicio = len(fig.data)
        visible = clave == "final"
        etiqueta = "Final" if clave == "final" else "Inicial"
        # Regiones con color según el estado en ESTA configuración
        for r, region in zip(rep["regiones"], e.regiones):
            estado = _estado_region(r, e.umbral_cubierta)
            x, y, zz = _xyz(g.circulo(region.centro, evaluador.radio_region, 60), 1.004)
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=zz, mode="lines", line=dict(color=COLOR_REGION[estado], width=6),
                name=f"{region.nombre} ({etiqueta.lower()})", visible=visible, showlegend=False,
                hovertext=f"{region.nombre} · {r['prioridad']} · cobertura {r['cobertura']:.0%}", hoverinfo="text",
            ))
            cx, cy, cz = _xyz(np.array([region.centro]), 1.02)
            fig.add_trace(go.Scatter3d(
                x=cx, y=cy, z=cz, mode="text", text=[f"{region.nombre} {r['cobertura']:.0%}"],
                textfont=dict(color=COLOR_REGION[estado], size=11), visible=visible, showlegend=False, hoverinfo="skip",
            ))
        # Satélites, su línea al nadir y su huella
        mal = {p["satelite"] for p in rep["problemas"]}
        for s, pos in enumerate(np.asarray(conf)):
            x, y, zz = _xyz(g.circulo(pos, evaluador.huella, 48), 1.002)
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=zz, mode="lines", line=dict(color=COLOR_SAT[clave], width=2),
                visible=visible, showlegend=False, hoverinfo="skip",
            ))
            sx, sy, sz = _xyz(pos[None], R_orbita)
            nx, ny, nz = _xyz(pos[None], 1.0)
            fig.add_trace(go.Scatter3d(
                x=[sx[0], nx[0]], y=[sy[0], ny[0]], z=[sz[0], nz[0]], mode="lines",
                line=dict(color=COLOR_SAT[clave], width=1), visible=visible, showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter3d(
                x=sx, y=sy, z=sz, mode="markers",
                marker=dict(size=7, color="#e74c3c" if s in mal else COLOR_SAT[clave], line=dict(color="#000", width=1),
                            symbol="diamond"),
                name=f"Satélites ({etiqueta.lower()})", legendgroup=f"sat-{clave}", showlegend=s == 0, visible=visible,
                hovertext=f"Satélite {s} · lat {pos[0]:.2f}°, lon {pos[1]:.2f}°" + (" · ⚠ en zona prohibida" if s in mal else ""),
                hoverinfo="text",
            ))
        indices_por_conf[clave] = (inicio, len(fig.data), rep)

    fijos = indices_por_conf["final"][0]
    if inicial is not None:
        botones = []
        for clave, etiqueta in [("final", "Configuración final"), ("inicial", "Configuración inicial")]:
            vis = [True] * fijos + [False] * (len(fig.data) - fijos)
            a, b, rep = indices_por_conf[clave]
            vis[a:b] = [True] * (b - a)
            botones.append(dict(label=etiqueta, method="update", args=[
                {"visible": vis},
                {"title.text": _titulo(titulo, etiqueta, rep, e)},
            ]))
        fig.update_layout(updatemenus=[dict(type="buttons", direction="right", x=0.01, y=0.02, xanchor="left",
                                            yanchor="bottom", buttons=botones, bgcolor="#e5e7eb",
                                            font=dict(color="#111827"), showactive=True)])

    rep_final = indices_por_conf["final"][2]
    fig.update_layout(
        title=dict(text=_titulo(titulo, "Configuración final", rep_final, e), font=dict(size=15)),
        paper_bgcolor="#0b0f19", font=dict(color="#e5e7eb"), height=720, margin=dict(l=0, r=0, t=70, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0.4)", x=0.0, y=0.92),
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                   aspectmode="data", bgcolor="#0b0f19",
                   camera=dict(eye=dict(x=-0.2, y=-1.9, z=0.7))),
    )
    return fig


def _titulo(base, etiqueta, rep, e):
    base = base or e.nombre
    estado = "válida" if rep["valida"] else f"INVÁLIDA (violación {rep['violacion']:.2f}°)"
    return (f"{base} — {etiqueta}<br><sup>Aptitud {rep['aptitud']:.4f} "
            f"({rep['porcentaje_de_la_cota']:.1f} % de la cota) · {rep['regiones_cubiertas']}/6 regiones cubiertas · {estado}</sup>")


# ---------------------------------------------------------------- mapa plano
def mapa(evaluador, config, ax=None, titulo=None, inicial=None):
    """Mapa plano (equirectangular) con matplotlib. Sirve como imagen fija."""
    import matplotlib.pyplot as plt

    e = evaluador.escenario
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    lat = np.linspace(-90, 90, 181)
    lon = np.linspace(-180, 180, 361)
    LON, LAT = np.meshgrid(lon, lat)
    ax.contourf(LON, LAT, _relieve(LAT, LON), levels=[-3, 0, 3], colors=["#cfe0ee", "#efe3c8"])

    def contorno(centro, radio, **kw):
        c = g.circulo(centro, radio, 120)
        # cortar la línea donde cruza el antimeridiano
        salto = np.abs(np.diff(c[:, 1])) > 180
        c = c.astype(float).copy()
        lon_c = np.insert(c[:, 1], np.flatnonzero(salto) + 1, np.nan)
        lat_c = np.insert(c[:, 0], np.flatnonzero(salto) + 1, np.nan)
        ax.plot(lon_c, lat_c, **kw)

    for z in e.zonas:
        contorno(z.centro, z.radio_grados, color=COLOR_ZONA[z.tipo], lw=2,
                 ls="-" if z.tipo == "escombros" else "--")
        ax.text(z.lon, z.lat, z.nombre, color=COLOR_ZONA[z.tipo], fontsize=7, ha="center", va="center")

    rep = evaluador.reporte(config)
    for r, region in zip(rep["regiones"], e.regiones):
        estado = _estado_region(r, e.umbral_cubierta)
        contorno(region.centro, evaluador.radio_region, color=COLOR_REGION[estado], lw=2.5)
        ax.text(region.lon, region.lat - evaluador.radio_region - 2.5, f"{region.nombre}\n{r['cobertura']:.0%}",
                ha="center", va="top", fontsize=8, color="#1b2433")

    if inicial is not None:
        ini = np.asarray(inicial)
        ax.scatter(ini[:, 1], ini[:, 0], marker="o", s=30, facecolors="none", edgecolors="#555", label="Inicial")
    conf = np.asarray(config)
    for s, pos in enumerate(conf):
        contorno(pos, evaluador.huella, color="#0077b6", lw=0.8)
    ax.scatter(conf[:, 1], conf[:, 0], marker="D", s=40, c="#0077b6", edgecolors="black", zorder=5, label="Final")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitud (°)")
    ax.set_ylabel("Latitud (°)")
    ax.set_title(titulo or f"{e.nombre} — aptitud {rep['aptitud']:.4f}, {rep['regiones_cubiertas']}/6 cubiertas, "
                           f"{'válida' if rep['valida'] else 'inválida'}", fontsize=10)
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.3)
    return ax


# -------------------------------------------------------------- evolución
def grafica_evolucion(historiales, cota=None, ax=None, titulo="Evolución de la aptitud"):
    """Curvas de mejor aptitud (y promedio si hay una sola corrida) por generación.

    `historiales` puede ser un dict (una corrida) o una lista de (etiqueta, dict).
    """
    import matplotlib.pyplot as plt

    if isinstance(historiales, dict):
        historiales = [("Mejor", historiales)]
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.5))
    for etiqueta, h in historiales:
        ax.plot(h["generacion"], h["mejor_aptitud"], lw=1.8, label=etiqueta)
    if len(historiales) == 1:
        h = historiales[0][1]
        ax.plot(h["generacion"], h["promedio_aptitud_validas"], lw=1.2, ls="--", label="Promedio de las válidas")
    if cota is not None:
        ax.axhline(cota, color="black", lw=1, ls=":", label=f"Cota superior ({cota:.4f})")
        ax.axhline(0.98 * cota, color="gray", lw=1, ls=":", label="98 % de la cota")
    ax.set_xlabel("Generación")
    ax.set_ylabel("Aptitud F")
    ax.set_title(titulo)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ax


def grafica_validez(historial, ax=None):
    """Porcentaje de individuos válidos por generación."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3))
    ax.plot(historial["generacion"], historial["porcentaje_validas"], color="#2a9d8f")
    ax.set_ylim(0, 105)
    ax.set_xlabel("Generación")
    ax.set_ylabel("% de individuos válidos")
    ax.grid(alpha=0.3)
    return ax


# ------------------------------------------------------------ visor 3D (Three.js)
def _emparejar(previa, actual):
    """Reordena `actual` para que cada satélite quede junto al más cercano de `previa`.

    Entre generaciones la mejor configuración puede ser otro individuo con los
    satélites en otro orden; sin esto, la animación los haría saltar de lugar.
    """
    d = g.distancia_angular(previa[:, None, :], actual[None, :, :])
    asignado = [-1] * len(previa)
    libres_p, libres_a = set(range(len(previa))), set(range(len(actual)))
    for k in np.argsort(d, axis=None):
        i, j = divmod(int(k), d.shape[1])
        if i in libres_p and j in libres_a:
            asignado[i] = j
            libres_p.discard(i)
            libres_a.discard(j)
    return actual[asignado]


def datos_visor(caso_id, nombre, descripcion, evaluador, resultado):
    """Datos de una corrida para el visor 3D: escenario + la mejor configuración de cada generación."""
    e = evaluador.escenario
    hist = resultado.historial
    configs = [np.asarray(c, dtype=float) for c in hist["mejor_config"]]
    ordenadas = [None] * len(configs)
    ordenadas[-1] = configs[-1]
    for k in range(len(configs) - 2, -1, -1):
        ordenadas[k] = _emparejar(ordenadas[k + 1], configs[k])
    gens = []
    for k, conf in enumerate(ordenadas):
        rep = evaluador.reporte(conf)
        gens.append({
            "s": np.round(conf, 3).tolist(),
            "F": round(rep["aptitud"], 4), "v": rep["valida"], "vi": round(rep["violacion"], 3),
            "c": rep["regiones_cubiertas"],
            "cob": [round(r["cobertura"], 3) for r in rep["regiones"]],
            "red": [round(r["redundancia"], 3) for r in rep["regiones"]],
            "ven": [r["satelites"] for r in rep["regiones"]],
            "mal": sorted({p["satelite"] for p in rep["problemas"]}),
            "sig": round(hist["sigma"][k], 3),
        })
    alcance = evaluador.alcanzabilidad()
    return {
        "id": caso_id, "nombre": nombre, "descripcion": descripcion,
        "planeta": e.planeta.nombre, "radio_km": e.planeta.radio_km, "altitud_km": e.altitud_km,
        "r_orbita": (e.planeta.radio_km + e.altitud_km) / e.planeta.radio_km,
        "huella": evaluador.huella, "radio_region": evaluador.radio_region,
        "umbral": e.umbral_cubierta, "cota": evaluador.cota_superior(), "num_satelites": e.num_satelites,
        "semilla": resultado.semilla, "evaluaciones": resultado.evaluaciones,
        "regiones": [{"nombre": r.nombre, "equivale_a": r.equivale_a, "lat": r.lat, "lon": r.lon,
                      "prioridad": r.prioridad, "peso": e.pesos[r.prioridad],
                      "alcanzable": round(alcance[r.nombre], 3)} for r in e.regiones],
        "zonas": [{"nombre": z.nombre, "tipo": z.tipo, "lat": z.lat, "lon": z.lon, "radio": z.radio_grados,
                   "equivale_a": z.equivale_a} for z in e.zonas],
        "gens": gens,
    }


def exportar_visor(casos, ruta):
    """Escribe el visor 3D (un solo HTML) con una o varias corridas.

    `casos` es una lista de dicts devueltos por `datos_visor`.
    """
    import json
    from pathlib import Path

    plantilla = (Path(__file__).parent / "plantilla_globo.html").read_text(encoding="utf-8")
    datos = json.dumps({"casos": casos}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    Path(ruta).write_text(plantilla.replace("__DATOS_ASTROSHIELD__", datos), encoding="utf-8")
    return ruta
