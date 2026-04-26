"""
Tabla 3: Analisis estadistico de la nube del salon T3-210 capturada con LD19 y SDK de C.
Mismas metricas que tabla 2 para permitir comparacion directa entre implementaciones.

Fuente: datasets/final-datasets/t3-210.json
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

with open(ROOT / "datasets/final-datasets/t3-210.json", encoding="utf-8") as f:
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
ang_density = len(pts) / (cov_h * cov_v)

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

header = ["Metrica", "LD19 — SDK de C"]

rows = [
    ["Puntos totales",                               f"{len(pts):,}"],
    ["Cobertura horizontal (deg)",                   f"{cov_h:.1f}"],
    ["Cobertura vertical (deg)",                     f"{cov_v:.1f}"],
    ["Densidad angular (pts/deg²)",                  f"{ang_density:.2f}"],
    ["Distancia media de retorno (mm)",              f"{statistics.mean(rs):.1f}"],
    ["Distancia mediana al vecino mas cercano (mm)", f"{statistics.median(nn):.2f}"],
    ["Voxeles ocupados (voxel = 20 mm)",             f"{len(voxels):,}"],
    ["CV densidad por voxel",                        f"{cv:.3f}"],
    ["Intensidad media",                             f"{statistics.mean(ins):.1f}"],
]

OUT_TSV = OUT_DIR / "tabla3_estadisticas_nube_ld19_t3210.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
