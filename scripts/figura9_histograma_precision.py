"""
Figura: Histograma de lecturas de distancia por distancia controlada.
4 subplots, uno por distancia. Linea vertical en la distancia real.
Salida: output/figura9_histograma_precision.png
"""

import csv
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

CONFIGS = [
    ("d055cm",  550),
    ("d080cm",  800),
    ("d110cm", 1100),
    ("d140cm", 1400),
]

COLOR = "#1f77b4"

fig, axes = plt.subplots(1, 4, figsize=(13, 4), sharey=False)

for ax, (label, real) in zip(axes, CONFIGS):
    with open(ROOT / f"data/experiments/ld19_precision/c/{label}_points.csv", encoding="utf-8") as f:
        readings = [float(r["distance_mm"]) for r in csv.DictReader(f)]

    ax.hist(readings, bins=20, color=COLOR, alpha=0.75, edgecolor="none")
    ax.axvline(real, color="black", linewidth=1.5, linestyle="--", label=f"Real: {real} mm")
    ax.axvline(statistics.mean(readings), color="#d62728", linewidth=1.5, linestyle="-",
               label=f"Media: {statistics.mean(readings):.1f} mm")

    ax.set_xlabel("Distancia (mm)", fontsize=9)
    ax.set_ylabel("Frecuencia", fontsize=9)
    ax.set_title(f"{real} mm", fontsize=10)
    ax.legend(fontsize=7, framealpha=0.8)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

fig.tight_layout()
out_path = OUT_DIR / "figura9_histograma_precision.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
