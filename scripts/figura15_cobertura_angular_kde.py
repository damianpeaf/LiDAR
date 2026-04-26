"""
Figura 15: Mapa de cobertura angular con zoom al bounding box real + isolineas KDE.
Panel 2x3, un subplot por escaneo arqueologico.
Fondo: hexbin (log escala). Encima: isolineas de densidad KDE.
"""

import json, math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

ROOT     = Path(__file__).resolve().parent.parent
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
DATASETS = Path("C:/Users/damia/tesis/LiDAR/datasets/final-datasets")

R_MAX = 11000
MARGIN = 3  # deg de margen alrededor del bounding box real

FILES = [
    ("esquina-del-juego-de-pelota-iximche-estructura-8.json",   "Juego de Pelota E1",    "Semicerrado"),
    ("esquina-2-del-juego-de-pelota-iximche-estructura-8.json", "Juego de Pelota E2",    "Semicerrado"),
    ("pared-estructura-38-iximche-1.json",                      "Pared Estr. 38 E1",     "Abierto"),
    ("pared-estructura-38-iximche-2.json",                      "Pared Estr. 38 E2",     "Abierto"),
    ("escalera-gran-palacio-iximche-1.json",                    "Escalera Palacio E1",   "Abierto"),
    ("escalera-gran-palacio-iximche-2.json",                    "Escalera Palacio E2",   "Abierto"),
]

fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

for ax, (fname, title, entorno) in zip(axes, FILES):
    print(f"Procesando {title}...")

    with open(DATASETS / fname, encoding="utf-8") as f:
        pts = json.load(f)
    pts = [p for p in pts if math.sqrt(p["x"]**2 + p["y"]**2 + p["z"]**2) < R_MAX]

    thetas = np.array([math.degrees(math.atan2(p["y"], p["x"])) for p in pts])
    phis   = np.array([math.degrees(math.atan2(p["z"], math.sqrt(p["x"]**2 + p["y"]**2))) for p in pts])

    # Bounding box real con margen
    t0, t1 = thetas.min() - MARGIN, thetas.max() + MARGIN
    p0, p1 = phis.min()   - MARGIN, phis.max()   + MARGIN

    # Hexbin como fondo (log escala automatica)
    hb = ax.hexbin(thetas, phis, gridsize=80, cmap="plasma",
                   bins="log", extent=[t0, t1, p0, p1],
                   mincnt=1, linewidths=0.0)

    # KDE sobre muestra (max 40k pts para velocidad)
    rng = np.random.default_rng(42)
    idx = rng.choice(len(thetas), size=min(40_000, len(thetas)), replace=False)
    kde = gaussian_kde(np.vstack([thetas[idx], phis[idx]]), bw_method=0.15)

    tg = np.linspace(t0, t1, 120)
    pg = np.linspace(p0, p1, 80)
    TT, PP = np.meshgrid(tg, pg)
    Z = kde(np.vstack([TT.ravel(), PP.ravel()])).reshape(TT.shape)

    # Isolineas en percentiles 30, 60, 85 de la densidad KDE
    levels = np.percentile(Z[Z > Z.max() * 0.01], [30, 60, 85])
    if len(np.unique(levels)) == len(levels):
        ax.contour(TT, PP, Z, levels=levels, colors="white",
                   linewidths=[0.6, 0.9, 1.2], alpha=0.75)

    ax.set_xlim(t0, t1)
    ax.set_ylim(p0, p1)
    ax.set_xlabel("theta (deg)", fontsize=8)
    ax.set_ylabel("phi (deg)", fontsize=8)
    ax.set_title(f"{title}\n({entorno})", fontsize=9, pad=4)
    ax.tick_params(labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    cb = fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("log(n)", fontsize=7)
    cb.ax.tick_params(labelsize=6)

fig.tight_layout(h_pad=3.0, w_pad=2.0)
out_path = OUT_DIR / "figura15_cobertura_angular_kde.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
