"""
Figura: Puntos/s a lo largo del tiempo -- LD19 SDK de C vs MicroPython (exp 1A y 2A).
Una sola figura con dos lineas (una por implementacion).
La banda sombreada representa +/- 1 desviacion estandar entre las 3 replicas en cada instante.
Salida: output/figura1_puntos_por_segundo_ld19.png
"""

import json
import math
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


def load_series(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    events = [e for e in data["events"] if e.get("event") == "stats"]
    t_key = "elapsed_s" if "elapsed_s" in events[0] else "duration_s"
    t = np.array([e[t_key] for e in events])
    y = np.array([e["points_per_s"] for e in events])
    return t, y


def align_and_aggregate(rep_files):
    """Interpola todas las replicas a una grilla temporal comun y calcula media +/- std."""
    series = [load_series(p) for p in rep_files]
    t_min = max(s[0][0] for s in series)
    t_max = min(s[0][-1] for s in series)
    t_common = np.linspace(t_min, t_max, 300)

    interpolated = np.array([np.interp(t_common, s[0], s[1]) for s in series])
    mean = interpolated.mean(axis=0)
    std = interpolated.std(axis=0)
    return t_common, mean, std


t_c,  mean_c,  std_c  = align_and_aggregate(REP_FILES_C)
t_py, mean_py, std_py = align_and_aggregate(REP_FILES_PY)

COLOR_C  = "#1f77b4"
COLOR_PY = "#d62728"

fig, ax = plt.subplots(figsize=(8, 4.5))

ax.plot(t_c,  mean_c,  color=COLOR_C,  linewidth=2.0, label="SDK de C")
ax.fill_between(t_c,  mean_c  - std_c,  mean_c  + std_c,  color=COLOR_C,  alpha=0.2)

ax.plot(t_py, mean_py, color=COLOR_PY, linewidth=2.0, label="MicroPython")
ax.fill_between(t_py, mean_py - std_py, mean_py + std_py, color=COLOR_PY, alpha=0.2)

ax.set_xlabel("Tiempo (s)", fontsize=11)
ax.set_ylabel("Puntos/s", fontsize=11)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(fontsize=10, framealpha=0.9)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura1_puntos_por_segundo_ld19.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
