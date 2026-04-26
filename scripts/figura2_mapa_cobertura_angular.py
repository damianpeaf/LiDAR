"""
Figura: Mapa de calor de cobertura angular — TF-Mini S vs LD19 SDK de C.
Eje X: angulo horizontal (theta), Eje Y: angulo vertical (phi).
Color: numero de puntos por celda angular de 1x1 grado.
Salida: output/figura2_mapa_cobertura_angular.png
"""

import json
import math
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

BIN_DEG = 1  # resolucion de celda en grados


def load_angular_grid(path):
    with open(path, encoding="utf-8") as f:
        pts = json.load(f)

    grid = defaultdict(int)
    for p in pts:
        r_xy = math.sqrt(p["x"]**2 + p["y"]**2)
        theta = math.degrees(math.atan2(p["y"], p["x"]))
        phi   = math.degrees(math.atan2(p["z"], r_xy))
        ti = int(math.floor(theta / BIN_DEG))
        pi = int(math.floor(phi   / BIN_DEG))
        grid[(ti, pi)] += 1

    return grid


def grid_to_matrix(grid):
    if not grid:
        return np.zeros((1, 1)), 0, 0, 0, 0

    ts = [k[0] for k in grid]
    ps = [k[1] for k in grid]
    t_min, t_max = min(ts), max(ts)
    p_min, p_max = min(ps), max(ps)

    W = t_max - t_min + 1
    H = p_max - p_min + 1
    mat = np.zeros((H, W))
    for (ti, pi), count in grid.items():
        mat[pi - p_min, ti - t_min] = count

    return mat, t_min, t_max, p_min, p_max


print("Cargando TF-Mini S...")
grid_tf = load_angular_grid(
    ROOT / "data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s.json"
)
print("Cargando LD19...")
grid_ld = load_angular_grid(
    ROOT / "datasets/final-datasets/t3-210.json"
)

mat_tf, tf_t0, tf_t1, tf_p0, tf_p1 = grid_to_matrix(grid_tf)
mat_ld, ld_t0, ld_t1, ld_p0, ld_p1 = grid_to_matrix(grid_ld)

datasets = [
    (mat_tf, tf_t0, tf_t1, tf_p0, tf_p1, "figura2a_mapa_cobertura_tfmini.png"),
    (mat_ld, ld_t0, ld_t1, ld_p0, ld_p1, "figura2b_mapa_cobertura_ld19.png"),
]

for mat, t0, t1, p0, p1, filename in datasets:
    fig, ax = plt.subplots(figsize=(7, 5))
    mat_log = np.log1p(mat)
    im = ax.imshow(
        mat_log,
        origin="lower",
        aspect="auto",
        extent=[t0 * BIN_DEG, (t1 + 1) * BIN_DEG,
                p0 * BIN_DEG, (p1 + 1) * BIN_DEG],
        cmap="plasma",
        interpolation="nearest",
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("log(puntos + 1)", fontsize=9)
    ax.set_xlabel("Angulo horizontal, θ (deg)", fontsize=10)
    ax.set_ylabel("Angulo vertical, φ (deg)", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out_path = OUT_DIR / filename
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Guardado: {out_path}")
