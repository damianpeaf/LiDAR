"""
Figura alternativa: Puntos/s a lo largo del tiempo -- LD19 SDK de C vs MicroPython.
Muestra las 3 replicas individuales por implementacion (6 lineas en total, 2 colores).
Salida: output/figura1_replicas_ld19.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

REP_FILES_C = [
    ROOT / "data/experiments/ld19c/bench_c_rep1.json",
    ROOT / "data/experiments/ld19c/bench_c_rep2.json",
    ROOT / "data/experiments/ld19c/bench_c_rep3.json",
]
REP_FILES_PY = [
    ROOT / "data/experiments/ld19_micropython/bench_py_rep1.json",
    ROOT / "data/experiments/ld19_micropython/bench_py_rep2.json",
    ROOT / "data/experiments/ld19_micropython/bench_py_rep3.json",
]

COLOR_C  = "#1f77b4"
COLOR_PY = "#d62728"


def load_series(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    events = [e for e in data["events"] if e.get("event") == "stats"]
    t_key = "elapsed_s" if "elapsed_s" in events[0] else "duration_s"
    t = np.array([e[t_key] for e in events])
    y = np.array([e["points_per_s"] for e in events])
    return t, y


fig, ax = plt.subplots(figsize=(8, 4.5))

for i, path in enumerate(REP_FILES_C):
    t, y = load_series(path)
    label = "SDK de C" if i == 0 else None
    ax.plot(t, y, color=COLOR_C, linewidth=1.5, alpha=0.75, label=label)

for i, path in enumerate(REP_FILES_PY):
    t, y = load_series(path)
    label = "MicroPython" if i == 0 else None
    ax.plot(t, y, color=COLOR_PY, linewidth=1.5, alpha=0.75, label=label)

ax.set_xlabel("Tiempo (s)", fontsize=11)
ax.set_ylabel("Puntos/s", fontsize=11)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(fontsize=10, framealpha=0.9)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura1_replicas_ld19.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
