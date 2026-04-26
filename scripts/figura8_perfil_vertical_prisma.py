"""
Figura: Perfil de distancia mediana por nivel de servo — escaneo del prisma.
Muestra la geometria vertical del objeto capturada por el sensor.
Salida: output/figura8_perfil_vertical_prisma.png
"""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

with open(ROOT / "data/experiments/ld19_scan/caja_referencia_c_scan1_sector_lento_points.csv", encoding="utf-8") as f:
    pts = list(csv.DictReader(f))

by_servo = defaultdict(list)
for p in pts:
    by_servo[round(float(p["servo_deg"]), 0)].append(float(p["distance_mm"]))

servos  = sorted(by_servo.keys())
medians = [statistics.median(by_servo[s]) for s in servos]
q25     = [statistics.quantiles(by_servo[s], n=4)[0] for s in servos]
q75     = [statistics.quantiles(by_servo[s], n=4)[2] for s in servos]

fig, ax = plt.subplots(figsize=(7, 4.5))

ax.fill_betweenx(servos, q25, q75, alpha=0.2, color="#1f77b4", label="IQR (Q1–Q3)")
ax.plot(medians, servos, color="#1f77b4", linewidth=2.0, label="Mediana")

ax.set_xlabel("Distancia de retorno (mm)", fontsize=11)
ax.set_ylabel("Angulo vertical del servo (deg)", fontsize=11)
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(fontsize=9, framealpha=0.9)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura8_perfil_vertical_prisma.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
