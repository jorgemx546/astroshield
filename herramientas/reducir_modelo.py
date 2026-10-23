"""Reduce un modelo 3D (.stl u .obj) para cargarlo rápido en el visor.

Uso:
    python herramientas/reducir_modelo.py ENTRADA SALIDA.stl [--resolucion 140]

Agrupa los vértices en una rejilla (vertex clustering) y quita los triángulos que
quedan degenerados. El resultado es un STL binario con "Z hacia arriba", que es como
el visor espera los STL.

Los modelos propios se cargan en el visor desde tu computadora y no se suben al
repositorio.
"""

import argparse
import struct
import sys
from pathlib import Path

import numpy as np


def leer_stl(ruta):
    datos = Path(ruta).read_bytes()
    if len(datos) >= 84:
        n = struct.unpack_from("<I", datos, 80)[0]
        if 84 + n * 50 == len(datos):
            reg = np.frombuffer(datos, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
            return reg["v"].reshape(-1, 3).astype(np.float64), np.arange(n * 3).reshape(-1, 3)
    # STL de texto
    v = [list(map(float, l.split()[1:4])) for l in datos.decode("utf-8", "replace").splitlines() if l.strip().startswith("vertex")]
    v = np.array(v, dtype=np.float64)
    return v, np.arange(len(v)).reshape(-1, 3)


def leer_obj(ruta):
    vertices, caras = [], []
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        for linea in f:
            if linea.startswith("v "):
                p = linea.split()
                vertices.append((float(p[1]), float(p[2]), float(p[3])))
            elif linea.startswith("f "):
                idx = []
                for parte in linea.split()[1:]:
                    i = int(parte.split("/")[0])
                    idx.append(i - 1 if i > 0 else len(vertices) + i)
                for k in range(1, len(idx) - 1):      # triangula polígonos en abanico
                    caras.append((idx[0], idx[k], idx[k + 1]))
    v = np.array(vertices, dtype=np.float64)
    # Los OBJ suelen venir con Y hacia arriba; se pasan a Z hacia arriba como los STL.
    v = np.stack([v[:, 0], -v[:, 2], v[:, 1]], axis=1)
    return v, np.array(caras, dtype=np.int64)


def reducir(v, caras, resolucion):
    minimo, maximo = v.min(axis=0), v.max(axis=0)
    paso = (maximo - minimo).max() / resolucion
    celda = np.floor((v - minimo) / paso).astype(np.int64)
    clave = celda[:, 0] + resolucion * (celda[:, 1] + (resolucion + 1) * celda[:, 2])
    unicas, inversa = np.unique(clave, return_inverse=True)
    conteo = np.bincount(inversa).astype(np.float64)
    nuevos = np.stack([np.bincount(inversa, weights=v[:, k]) / conteo for k in range(3)], axis=1)
    t = inversa[caras]
    ok = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])
    t = t[ok]
    _, primeras = np.unique(np.sort(t, axis=1), axis=0, return_index=True)
    return nuevos, t[np.sort(primeras)]


def escribir_stl(ruta, v, t):
    tri = v[t].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    reg = np.zeros(len(t), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    reg["n"], reg["v"] = n, tri
    with open(ruta, "wb") as f:
        f.write(b"AstroShield - modelo reducido".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(reg.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--resolucion", type=int, default=140)
    a = ap.parse_args()
    ext = Path(a.entrada).suffix.lower()
    if ext == ".stl":
        v, caras = leer_stl(a.entrada)
    elif ext == ".obj":
        v, caras = leer_obj(a.entrada)
    else:
        sys.exit("Solo se aceptan archivos .stl u .obj")
    nv, nt = reducir(v, caras, a.resolucion)
    escribir_stl(a.salida, nv, nt)
    print(f"{Path(a.entrada).name}: {len(caras):,} triángulos → {len(nt):,} · {Path(a.salida).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
