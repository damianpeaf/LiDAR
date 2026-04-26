"""
Tabla 7: Estadisticas de nubes de puntos arqueologicas — Iximche.
Mismas metricas que tablas 2 y 3 para comparacion consistente.
Filtro: puntos con r >= 11000 mm descartados (limite del sensor LD19).
"""

import json, csv, math, statistics
from pathlib import Path
from scipy.spatial import KDTree

ROOT     = Path(__file__).resolve().parent.parent
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")
R_MAX    = 11000
VOXEL_MM = 20

FILES = [
    ("Juego de Pelota E1",     "esquina-del-juego-de-pelota-iximche-estructura-8.json",  "Semicerrado"),
    ("Juego de Pelota E2",     "esquina-2-del-juego-de-pelota-iximche-estructura-8.json","Semicerrado"),
    ("Pared Estructura 38 E1", "pared-estructura-38-iximche-1.json",                     "Abierto"),
    ("Pared Estructura 38 E2", "pared-estructura-38-iximche-2.json",                     "Abierto"),
    ("Escalera Palacio E1",    "escalera-gran-palacio-iximche-1.json",                   "Abierto"),
    ("Escalera Palacio E2",    "escalera-gran-palacio-iximche-2.json",                   "Abierto"),
]


def analyze(path):
    with open(path, encoding="utf-8") as f:
        pts = json.load(f)
    pts = [p for p in pts if math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) < R_MAX]

    ins, rs, thetas, phis = [], [], [], []
    for p in pts:
        r_xy = math.sqrt(p["x"]**2 + p["y"]**2)
        ins.append(p["intensity"])
        rs.append(math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2))
        thetas.append(math.degrees(math.atan2(p["y"], p["x"])))
        phis.append(math.degrees(math.atan2(p["z"], r_xy)))

    cov_h = max(thetas) - min(thetas)
    cov_v = max(phis)   - min(phis)
    ang_density = len(pts) / (cov_h * cov_v)

    voxels = {}
    for p in pts:
        key = (int(p["x"]//VOXEL_MM), int(p["y"]//VOXEL_MM), int(p["z"]//VOXEL_MM))
        voxels[key] = voxels.get(key, 0) + 1
    counts = list(voxels.values())
    cv = statistics.stdev(counts) / statistics.mean(counts)

    coords = [[p["x"], p["y"], p["z"]] for p in pts]
    tree = KDTree(coords)
    dists, _ = tree.query(coords, k=2)
    nn_median = statistics.median(d[1] for d in dists)

    sat = sum(1 for i in ins if i == 255)

    return {
        "n": len(pts), "cov_h": cov_h, "cov_v": cov_v,
        "ang_density": ang_density, "r_mean": statistics.mean(rs),
        "nn_median": nn_median, "voxels": len(voxels), "cv": cv,
        "int_mean": statistics.mean(ins), "int_std": statistics.stdev(ins),
        "sat": sat, "sat_pct": sat / len(pts) * 100,
    }


header = [
    "Escaneo", "Entorno", "Puntos totales",
    "Cobertura horizontal (deg)", "Cobertura vertical (deg)",
    "Densidad angular (pts/deg²)",
    "Distancia media de retorno (mm)",
    "Distancia mediana NN (mm)",
    "Voxeles ocupados (20 mm)",
    "CV densidad por voxel",
    "Intensidad media", "Intensidad desv. est.",
    "Puntos saturados (intensity=255)", "Saturados (%)",
]

rows = []
for label, fname, entorno in FILES:
    print(f"Procesando {label}...")
    r = analyze(DATASETS / fname)
    rows.append([
        label, entorno,
        f"{r['n']:,}",
        f"{r['cov_h']:.1f}", f"{r['cov_v']:.1f}",
        f"{r['ang_density']:.2f}",
        f"{r['r_mean']:.0f}",
        f"{r['nn_median']:.2f}",
        f"{r['voxels']:,}",
        f"{r['cv']:.3f}",
        f"{r['int_mean']:.1f}", f"{r['int_std']:.1f}",
        f"{r['sat']:,}", f"{r['sat_pct']:.2f}",
    ])

OUT_TSV = OUT_DIR / "tabla7_estadisticas_nubes_arqueologicas.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
