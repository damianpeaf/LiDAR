"""
Figura: Distribucion de distancias de retorno — TF-Mini S vs LD19 SDK de C.
Histograma de r (distancia al origen) para ambos sensores en una sola figura.
Salida: output/figura3_distribucion_distancias.png
"""

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


def load_distances(path):
    with open(path, encoding="utf-8") as f:
        pts = json.load(f)
    return [math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) for p in pts]


print("Cargando TF-Mini S...")
r_tf = load_distances(ROOT / "data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s.json")

print("Cargando LD19...")
r_ld = load_distances(ROOT / "datasets/final-datasets/t3-210.json")

COLOR_TF = "#d62728"
COLOR_LD = "#1f77b4"

fig, ax = plt.subplots(figsize=(8, 4.5))

ax.hist(r_tf, bins=80, color=COLOR_TF, alpha=0.7, label="TF-Mini S",
        density=True, edgecolor="none")
ax.hist(r_ld, bins=80, color=COLOR_LD, alpha=0.7, label="LD19 — SDK de C",
        density=True, edgecolor="none")

ax.set_xlabel("Distancia de retorno (mm)", fontsize=11)
ax.set_ylabel("Densidad de probabilidad", fontsize=11)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(fontsize=10, framealpha=0.9)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura3_distribucion_distancias.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
