"""
Figura: Tasa de error UART a lo largo del tiempo.
Compara SDK de C vs MicroPython, con y sin transmision de red activa.
4 series: C benchmark, C con red, MicroPython benchmark, MicroPython con red.
Salida: output/figura4_tasa_error_temporal.png
"""

import json
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

SOURCES = {
    "SDK de C — sin red":      (ROOT / "data/experiments/ld19c/bench_c_rep1.json",                                "#1f77b4", "-"),
    "SDK de C — con red":      (ROOT / "data/experiments/red/c_sdk_network_rep1.json",                            "#1f77b4", "--"),
    "MicroPython — sin red":   (ROOT / "data/experiments/ld19_micropython/bench_py_rep1.json",                    "#d62728", "-"),
    "MicroPython — con red":   (ROOT / "data/experiments/red/micropython_network_rep1_serial.json",               "#d62728", "--"),
}


def load_error_series(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    events = [e for e in data["events"] if e.get("event") == "stats"]
    t_key = "elapsed_s" if "elapsed_s" in events[0] else "duration_s"
    t, err = [], []
    for e in events:
        recv = int(e["frames_received"])
        crc  = int(e["frames_crc_error"])
        t.append(float(e[t_key]))
        err.append((crc / recv * 100) if recv > 0 else 0.0)
    return np.array(t), np.array(err)


fig, ax = plt.subplots(figsize=(8, 4.5))

for label, (path, color, ls) in SOURCES.items():
    t, err = load_error_series(path)
    ax.plot(t, err, color=color, linestyle=ls, linewidth=1.8, label=label)

ax.set_xlabel("Tiempo (s)", fontsize=11)
ax.set_ylabel("Tasa de error UART (%)", fontsize=11)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(fontsize=9, framealpha=0.9)
ax.tick_params(labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
out_path = OUT_DIR / "figura4_tasa_error_temporal.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Guardado: {out_path}")
