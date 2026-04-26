"""
Figura 10: Histograma de intensidad por entorno — semicerrado vs abierto.
Figura 11: Mapa de calor de intensidad angular para cada escaneo arqueologico.
"""

import json, math
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")

R_MAX   = 11000
BIN_DEG = 1

FILES = [
    ("Juego de Pelota E1",     "esquina-del-juego-de-pelota-iximche-estructura-8.json",   "Semicerrado", "#2ca02c"),
    ("Juego de Pelota E2",     "esquina-2-del-juego-de-pelota-iximche-estructura-8.json", "Semicerrado", "#2ca02c"),
    ("Pared Estructura 38 E1", "pared-estructura-38-iximche-1.json",                      "Abierto",     "#1f77b4"),
    ("Pared Estructura 38 E2", "pared-estructura-38-iximche-2.json",                      "Abierto",     "#1f77b4"),
    ("Escalera Palacio E1",    "escalera-gran-palacio-iximche-1.json",                    "Abierto",     "#d62728"),
    ("Escalera Palacio E2",    "escalera-gran-palacio-iximche-2.json",                    "Abierto",     "#d62728"),
]


def load_filtered(path):
    with open(path, encoding="utf-8") as f:
        pts = json.load(f)
    return [p for p in pts if math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) < R_MAX]


# ── Figura 10: Histograma de intensidad por escaneo ───────────────────────────

print("Generando figura 10...")
fig, ax = plt.subplots(figsize=(9, 4.5))

for label, fname, entorno, color in FILES:
    pts = load_filtered(DATASETS / fname)
    ins = [p["intensity"] for p in pts]
    ls = "-" if "E1" in label else "--"
    ax.hist(ins, bins=64, range=(0, 255), density=True, alpha=0.45,
            color=color, edgecolor="none", label=f"{label} ({entorno})", histtype="stepfilled")

ax.set_xlabel("Intensidad", fontsize=11)
ax.set_ylabel("Densidad de probabilidad", fontsize=11)
ax.legend(fontsize=8, framealpha=0.9, ncol=2)
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(OUT_DIR / "figura10_intensidad_por_entorno.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: figura10_intensidad_por_entorno.png")

# ── Figuras 11a-f: Mapa de calor de intensidad angular individual ─────────────

SLUGS = [
    "figura11a_intensidad_juego_pelota_e1",
    "figura11b_intensidad_juego_pelota_e2",
    "figura11c_intensidad_pared_e1",
    "figura11d_intensidad_pared_e2",
    "figura11e_intensidad_escalera_e1",
    "figura11f_intensidad_escalera_e2",
]

for (label, fname, entorno, _), slug in zip(FILES, SLUGS):
    print(f"Generando {slug}...")
    pts = load_filtered(DATASETS / fname)

    grid_sum = defaultdict(float)
    grid_cnt = defaultdict(int)
    for p in pts:
        r_xy = math.sqrt(p["x"]**2 + p["y"]**2)
        theta = math.degrees(math.atan2(p["y"], p["x"]))
        phi   = math.degrees(math.atan2(p["z"], r_xy))
        ti = int(math.floor(theta / BIN_DEG))
        pi = int(math.floor(phi   / BIN_DEG))
        grid_sum[(ti, pi)] += p["intensity"]
        grid_cnt[(ti, pi)] += 1

    ts = [k[0] for k in grid_cnt]
    ps = [k[1] for k in grid_cnt]
    t0, t1 = min(ts), max(ts)
    p0, p1 = min(ps), max(ps)
    mat = np.zeros((p1 - p0 + 1, t1 - t0 + 1))
    for (ti, pi), cnt in grid_cnt.items():
        mat[pi - p0, ti - t0] = grid_sum[(ti, pi)] / cnt

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(mat, origin="lower", aspect="auto",
                   extent=[t0*BIN_DEG, (t1+1)*BIN_DEG, p0*BIN_DEG, (p1+1)*BIN_DEG],
                   cmap="inferno", interpolation="nearest", vmin=0, vmax=255)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("Intensidad media", fontsize=9)
    ax.set_xlabel("Angulo horizontal, θ (deg)", fontsize=10)
    ax.set_ylabel("Angulo vertical, φ (deg)", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out_path = OUT_DIR / f"{slug}.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Guardado: {out_path}")
