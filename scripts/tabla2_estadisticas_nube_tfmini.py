"""
Tabla 2: Analisis estadistico de la nube exploratoria TF-Mini S.
Responde al objetivo: cobertura y densidad de la nube de punto unico vs multipunto.

Fuentes:
  - S1: data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s.json
  - S2: data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s-2.json

Las dos sesiones se consolidan como media +/- sigma para consistencia con tabla 1.

Este mismo script (funcion analyze) se reutilizara para otras nubes en tablas futuras.
"""

import json
import csv
import math
import statistics
from pathlib import Path
from scipy.spatial import KDTree

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

VOXEL_MM = 20


def analyze(path):
    with open(path, encoding="utf-8") as f:
        pts = json.load(f)

    ins = [p["intensity"] for p in pts]

    thetas, phis, rs = [], [], []
    for p in pts:
        r_xy = math.sqrt(p["x"]**2 + p["y"]**2)
        thetas.append(math.degrees(math.atan2(p["y"], p["x"])))
        phis.append(math.degrees(math.atan2(p["z"], r_xy)))
        rs.append(math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2))

    cov_h = max(thetas) - min(thetas)
    cov_v = max(phis)   - min(phis)
    ang_density = len(pts) / (cov_h * cov_v) if cov_h * cov_v > 0 else 0

    voxels = {}
    for p in pts:
        key = (int(p["x"] // VOXEL_MM), int(p["y"] // VOXEL_MM), int(p["z"] // VOXEL_MM))
        voxels[key] = voxels.get(key, 0) + 1
    counts = list(voxels.values())
    cv = statistics.stdev(counts) / statistics.mean(counts)

    coords = [[p["x"], p["y"], p["z"]] for p in pts]
    tree = KDTree(coords)
    dists, _ = tree.query(coords, k=2)
    nn = [d[1] for d in dists]

    return {
        "n":           len(pts),
        "cov_h":       cov_h,
        "cov_v":       cov_v,
        "ang_density": ang_density,
        "r_mean":      statistics.mean(rs),
        "nn_median":   statistics.median(nn),
        "voxels":      len(voxels),
        "cv":          cv,
        "int_mean":    statistics.mean(ins),
        "int_std":     statistics.stdev(ins),
    }


files = [
    ROOT / "data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s.json",
    ROOT / "data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s-2.json",
]

# Usar la sesion con mas puntos
reps = [(p, analyze(p)) for p in files]
_, r = max(reps, key=lambda x: x[1]["n"])

def fmt(key, f):
    return f.format(r[key])

header = ["Metrica", "TF-Mini S"]

rows = [
    ["Puntos totales",                               fmt("n",           "{:.0f}")],
    ["Cobertura horizontal (deg)",                   fmt("cov_h",       "{:.1f}")],
    ["Cobertura vertical (deg)",                     fmt("cov_v",       "{:.1f}")],
    ["Densidad angular (pts/deg²)",                  fmt("ang_density", "{:.2f}")],
    ["Distancia media de retorno (mm)",              fmt("r_mean",      "{:.1f}")],
    ["Distancia mediana al vecino mas cercano (mm)", fmt("nn_median",   "{:.2f}")],
    ["Voxeles ocupados (voxel = 20 mm)",             fmt("voxels",      "{:.0f}")],
    ["CV densidad por voxel",                        fmt("cv",          "{:.3f}")],
    ["Intensidad media",                             fmt("int_mean",    "{:.1f}")],
]

OUT_TSV = OUT_DIR / "tabla2_estadisticas_nube_tfmini.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
