"""
Figura 13: Dispersion cobertura angular (pts/deg2) vs saturacion (%) por escaneo.
Punto coloreado por entorno, etiquetado con nombre de escaneo.
"""

import json, math, statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT     = Path(__file__).resolve().parent.parent
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")

R_MAX = 11000

FILES = [
    ("JP E1",    "esquina-del-juego-de-pelota-iximche-estructura-8.json",   "Semicerrado", "#2ca02c"),
    ("JP E2",    "esquina-2-del-juego-de-pelota-iximche-estructura-8.json", "Semicerrado", "#2ca02c"),
    ("Pared E1", "pared-estructura-38-iximche-1.json",                      "Abierto",     "#1f77b4"),
    ("Pared E2", "pared-estructura-38-iximche-2.json",                      "Abierto",     "#1f77b4"),
    ("Esc. E1",  "escalera-gran-palacio-iximche-1.json",                    "Abierto",     "#d62728"),
    ("Esc. E2",  "escalera-gran-palacio-iximche-2.json",                    "Abierto",     "#d62728"),
]

xs, ys, colors, labels = [], [], [], []

for label, fname, entorno, color in FILES:
    print(f"Procesando {label}...")
    with open(DATASETS / fname, encoding="utf-8") as f:
        pts = json.load(f)
    pts = [p for p in pts if math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) < R_MAX]

    ins, thetas, phis = [], [], []
    for p in pts:
        r_xy = math.sqrt(p["x"]**2 + p["y"]**2)
        ins.append(p["intensity"])
        thetas.append(math.degrees(math.atan2(p["y"], p["x"])))
        phis.append(math.degrees(math.atan2(p["z"], r_xy)))

    cov_h = max(thetas) - min(thetas)
    cov_v = max(phis)   - min(phis)
    ang_density = len(pts) / (cov_h * cov_v)
    sat_pct     = sum(1 for i in ins if i == 255) / len(pts) * 100

    xs.append(ang_density)
    ys.append(sat_pct)
    colors.append(color)
    labels.append(label)

fig, ax = plt.subplots(figsize=(7, 5))

seen = set()
for x, y, c, lbl in zip(xs, ys, colors, labels):
    entorno = "Semicerrado" if c == "#2ca02c" else ("Abierto (Pared)" if c == "#1f77b4" else "Abierto (Escalera)")
    handle_label = entorno if entorno not in seen else "_nolegend_"
    seen.add(entorno)
    ax.scatter(x, y, color=c, s=80, zorder=3, label=handle_label)
    ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=8)

ax.set_xlabel("Densidad angular (pts/deg$^2$)", fontsize=11)
ax.set_ylabel("Puntos saturados (%)", fontsize=11)
ax.legend(fontsize=9, framealpha=0.9)
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura13_cobertura_vs_saturacion.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
