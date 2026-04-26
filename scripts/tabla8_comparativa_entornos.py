"""
Tabla 8: Comparativa de metricas clave por entorno (Semicerrado vs Abierto).
Media +- desviacion estandar de cada grupo.
"""

import json, csv, math, statistics
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")
R_MAX    = 11000
VOXEL_MM = 20

FILES = [
    ("Juego de Pelota E1",     "esquina-del-juego-de-pelota-iximche-estructura-8.json",   "Semicerrado"),
    ("Juego de Pelota E2",     "esquina-2-del-juego-de-pelota-iximche-estructura-8.json", "Semicerrado"),
    ("Pared Estructura 38 E1", "pared-estructura-38-iximche-1.json",                      "Abierto"),
    ("Pared Estructura 38 E2", "pared-estructura-38-iximche-2.json",                      "Abierto"),
    ("Escalera Palacio E1",    "escalera-gran-palacio-iximche-1.json",                    "Abierto"),
    ("Escalera Palacio E2",    "escalera-gran-palacio-iximche-2.json",                    "Abierto"),
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

    sat = sum(1 for i in ins if i == 255)

    return {
        "n":           len(pts),
        "cov_h":       cov_h,
        "cov_v":       cov_v,
        "ang_density": ang_density,
        "r_mean":      statistics.mean(rs),
        "voxels":      len(voxels),
        "int_mean":    statistics.mean(ins),
        "sat_pct":     sat / len(pts) * 100,
    }


groups = {"Semicerrado": [], "Abierto": []}
for label, fname, entorno in FILES:
    print(f"Procesando {label}...")
    r = analyze(DATASETS / fname)
    groups[entorno].append(r)


def fmt(vals, decimals=1):
    m = statistics.mean(vals)
    s = statistics.stdev(vals) if len(vals) > 1 else 0.0
    return f"{m:.{decimals}f} +- {s:.{decimals}f}"


header = [
    "Entorno", "N escaneos",
    "Puntos totales",
    "Cobertura horizontal (deg)",
    "Cobertura vertical (deg)",
    "Densidad angular (pts/deg2)",
    "Distancia media de retorno (mm)",
    "Voxeles ocupados (20 mm)",
    "Intensidad media",
    "Saturados (%)",
]

rows = []
for entorno, recs in groups.items():
    rows.append([
        entorno,
        str(len(recs)),
        fmt([r["n"]          for r in recs], 0),
        fmt([r["cov_h"]      for r in recs], 1),
        fmt([r["cov_v"]      for r in recs], 1),
        fmt([r["ang_density"]for r in recs], 2),
        fmt([r["r_mean"]     for r in recs], 0),
        fmt([r["voxels"]     for r in recs], 0),
        fmt([r["int_mean"]   for r in recs], 1),
        fmt([r["sat_pct"]    for r in recs], 2),
    ])

OUT_TSV = OUT_DIR / "tabla8_comparativa_entornos.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
