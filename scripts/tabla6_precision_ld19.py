"""
Tabla 6: Precision por distancia controlada — LD19 SDK de C (experimento 1B).
Figura 7: Distribucion del error por distancia (boxplot).
"""

import csv
import math
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

CONFIGS = [
    ("d055cm",  550),
    ("d080cm",  800),
    ("d110cm", 1100),
    ("d140cm", 1400),
]


def load_readings(label):
    path = ROOT / f"data/experiments/ld19_precision/c/{label}_points.csv"
    with open(path, encoding="utf-8") as f:
        return [float(r["distance_mm"]) for r in csv.DictReader(f)]


data = {real: load_readings(label) for label, real in CONFIGS}

# ── Tabla ─────────────────────────────────────────────────────────────────────

header = [
    "Distancia real (mm)",
    "N lecturas",
    "Media (mm)",
    "Mediana (mm)",
    "Desv. est. (mm)",
    "MAE (mm)",
    "RMSE (mm)",
    "Error relativo (%)",
]

rows = []
for real, readings in data.items():
    errors = [r - real for r in readings]
    mean   = statistics.mean(readings)
    median = statistics.median(readings)
    std    = statistics.stdev(readings)
    mae    = statistics.mean(abs(e) for e in errors)
    rmse   = math.sqrt(statistics.mean(e**2 for e in errors))
    rel    = abs(mean - real) / real * 100
    rows.append([
        f"{real}",
        f"{len(readings)}",
        f"{mean:.3f}",
        f"{median:.1f}",
        f"{std:.3f}",
        f"{mae:.3f}",
        f"{rmse:.3f}",
        f"{rel:.3f}",
    ])

OUT_TSV = OUT_DIR / "tabla6_precision_ld19.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)
print(f"Guardado: {OUT_TSV}")

# ── Figura: boxplot del error por distancia ───────────────────────────────────

fig, ax = plt.subplots(figsize=(7, 4.5))

error_series = [[r - real for r in readings] for real, readings in data.items()]
labels       = [f"{real}" for real in data.keys()]

bp = ax.boxplot(
    error_series,
    labels=labels,
    patch_artist=True,
    medianprops=dict(color="black", linewidth=1.8),
    boxprops=dict(facecolor="#1f77b4", alpha=0.6),
    whiskerprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.2),
    flierprops=dict(marker="o", markersize=3, alpha=0.5, color="#1f77b4"),
)

ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
ax.set_xlabel("Distancia real (mm)", fontsize=11)
ax.set_ylabel("Error (mm)", fontsize=11)
ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.5)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura7_error_por_distancia.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
