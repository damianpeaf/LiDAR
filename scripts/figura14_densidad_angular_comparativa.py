"""
Figura 14: Barplot de densidad angular (pts/deg2) para los 6 escaneos arqueologicos,
agrupados por entorno (Semicerrado / Abierto).
"""

import json, math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT     = Path(__file__).resolve().parent.parent
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")

R_MAX = 11000

FILES = [
    ("JP E1",    "esquina-del-juego-de-pelota-iximche-estructura-8.json",   "Semicerrado"),
    ("JP E2",    "esquina-2-del-juego-de-pelota-iximche-estructura-8.json", "Semicerrado"),
    ("Pared E1", "pared-estructura-38-iximche-1.json",                      "Abierto"),
    ("Pared E2", "pared-estructura-38-iximche-2.json",                      "Abierto"),
    ("Esc. E1",  "escalera-gran-palacio-iximche-1.json",                    "Abierto"),
    ("Esc. E2",  "escalera-gran-palacio-iximche-2.json",                    "Abierto"),
]

COLOR_MAP = {"Semicerrado": "#2ca02c", "Abierto": "#1f77b4"}
HATCH_MAP = {"Semicerrado": "", "Abierto": "//"}

scan_labels  = []
densities    = []
bar_colors   = []
bar_hatches  = []

for label, fname, entorno in FILES:
    print(f"Procesando {label}...")
    with open(DATASETS / fname, encoding="utf-8") as f:
        pts = json.load(f)
    pts = [p for p in pts if math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) < R_MAX]

    thetas, phis = [], []
    for p in pts:
        r_xy = math.sqrt(p["x"]**2 + p["y"]**2)
        thetas.append(math.degrees(math.atan2(p["y"], p["x"])))
        phis.append(math.degrees(math.atan2(p["z"], r_xy)))

    cov_h = max(thetas) - min(thetas)
    cov_v = max(phis)   - min(phis)
    ang_density = len(pts) / (cov_h * cov_v)

    scan_labels.append(label)
    densities.append(ang_density)
    bar_colors.append(COLOR_MAP[entorno])
    bar_hatches.append(HATCH_MAP[entorno])

x = np.arange(len(scan_labels))

fig, ax = plt.subplots(figsize=(8, 4.5))

bars = ax.bar(x, densities, color=bar_colors, edgecolor="white", linewidth=0.8)
for bar, hatch in zip(bars, bar_hatches):
    bar.set_hatch(hatch)

# Separador visual entre grupos
ax.axvline(1.5, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)

# Etiquetas de grupo
ax.text(0.5, max(densities) * 1.04, "Semicerrado", ha="center", fontsize=9,
        color=COLOR_MAP["Semicerrado"], fontweight="bold")
ax.text(3.5, max(densities) * 1.04, "Abierto", ha="center", fontsize=9,
        color=COLOR_MAP["Abierto"], fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(scan_labels, fontsize=9)
ax.set_ylabel("Densidad angular (pts/deg$^2$)", fontsize=11)
ax.tick_params(labelsize=9)
ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura14_densidad_angular_comparativa.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
