"""
Figuras 12a-f: Mapa de cobertura angular (log puntos/celda) para cada escaneo arqueologico.
Misma metodologia que figura 2 para consistencia.
"""

import json, math
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT     = Path(__file__).resolve().parent.parent
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")

R_MAX   = 11000
BIN_DEG = 1

FILES = [
    ("esquina-del-juego-de-pelota-iximche-estructura-8.json",   "figura12a_cobertura_juego_pelota_e1"),
    ("esquina-2-del-juego-de-pelota-iximche-estructura-8.json", "figura12b_cobertura_juego_pelota_e2"),
    ("pared-estructura-38-iximche-1.json",                      "figura12c_cobertura_pared_e1"),
    ("pared-estructura-38-iximche-2.json",                      "figura12d_cobertura_pared_e2"),
    ("escalera-gran-palacio-iximche-1.json",                    "figura12e_cobertura_escalera_e1"),
    ("escalera-gran-palacio-iximche-2.json",                    "figura12f_cobertura_escalera_e2"),
]

for fname, slug in FILES:
    print(f"Generando {slug}...")

    with open(DATASETS / fname, encoding="utf-8") as f:
        pts = json.load(f)
    pts = [p for p in pts if math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) < R_MAX]

    grid = defaultdict(int)
    for p in pts:
        r_xy  = math.sqrt(p["x"]**2 + p["y"]**2)
        theta = math.degrees(math.atan2(p["y"], p["x"]))
        phi   = math.degrees(math.atan2(p["z"], r_xy))
        grid[(int(math.floor(theta / BIN_DEG)), int(math.floor(phi / BIN_DEG)))] += 1

    ts = [k[0] for k in grid]
    ps = [k[1] for k in grid]
    t0, t1 = min(ts), max(ts)
    p0, p1 = min(ps), max(ps)
    mat = np.zeros((p1 - p0 + 1, t1 - t0 + 1))
    for (ti, pi), cnt in grid.items():
        mat[pi - p0, ti - t0] = cnt

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(
        np.log1p(mat), origin="lower", aspect="auto",
        extent=[t0*BIN_DEG, (t1+1)*BIN_DEG, p0*BIN_DEG, (p1+1)*BIN_DEG],
        cmap="plasma", interpolation="nearest",
    )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("log(puntos + 1)", fontsize=9)
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
