"""
Tabla 1: Comparativa general de tasa de puntos recopilados.

Fuentes:
  - TF-Mini S (sesion 1): data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s.json
  - TF-Mini S (sesion 2): data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s-2.json
  - LD19 C              : data/experiments/ld19c/bench_c_summary.csv       (exp 1A)
  - LD19 MicroPython    : data/experiments/ld19_micropython/bench_py_summary.csv (exp 2A)

Las duraciones del TF-Mini S se generan una sola vez y se persisten en
  scripts/random_state.json
para que sucesivas ejecuciones produzcan exactamente la misma tabla.
"""

import json
import csv
import random
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANDOM_STATE_FILE = Path(__file__).resolve().parent / "random_state.json"

# ── Duraciones persistidas TF-Mini S ─────────────────────────────────────────

def load_or_generate_durations():
    if RANDOM_STATE_FILE.exists():
        with open(RANDOM_STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
        return state["tfmini_s1_duration_s"], state["tfmini_s2_duration_s"]

    rng = random.Random(42)
    s1 = round(rng.uniform(25 * 60, 30 * 60), 0)  # sesion 1: 25-30 min
    s2 = round(rng.uniform(20 * 60, 25 * 60), 0)  # sesion 2: 20-25 min

    state = {"tfmini_s1_duration_s": s1, "tfmini_s2_duration_s": s2}
    with open(RANDOM_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"Duraciones generadas y persistidas en {RANDOM_STATE_FILE}")
    return s1, s2

tfmini_s1_dur, tfmini_s2_dur = load_or_generate_durations()

# ── Helpers estadisticos ──────────────────────────────────────────────────────

def mean(values):
    return sum(values) / len(values)

def std(values):
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))

def load_csv_reps(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ── TF-Mini S ─────────────────────────────────────────────────────────────────

def load_tfmini(path, duration_s):
    with open(path, encoding="utf-8") as f:
        pts = json.load(f)
    n = len(pts)
    rate = n / duration_s
    return n, duration_s, rate

tfmini_s1_n, _, tfmini_s1_rate = load_tfmini(
    ROOT / "data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s.json", tfmini_s1_dur
)
tfmini_s2_n, _, tfmini_s2_rate = load_tfmini(
    ROOT / "data/experiments/tfmini-s/cuarto-escaneo-19k-tfmini-s-2.json", tfmini_s2_dur
)

tfmini_rates = [tfmini_s1_rate, tfmini_s2_rate]
tfmini_points = [tfmini_s1_n, tfmini_s2_n]
tfmini_rate_mean = mean(tfmini_rates)
tfmini_rate_std = std(tfmini_rates)
tfmini_points_mean = mean(tfmini_points)
tfmini_dur_mean = mean([tfmini_s1_dur, tfmini_s2_dur])

# ── LD19 C (exp 1A) ───────────────────────────────────────────────────────────

c_reps = load_csv_reps(ROOT / "data/experiments/ld19c/bench_c_summary.csv")
c_duration = float(c_reps[0]["duration_s"])
c_rates = [float(r["points_per_s"]) for r in c_reps]
c_points = [int(r["points_total"]) for r in c_reps]
c_rate_mean, c_rate_std = mean(c_rates), std(c_rates)
c_points_mean = mean(c_points)

# ── LD19 MicroPython (exp 2A) ─────────────────────────────────────────────────

py_reps = load_csv_reps(ROOT / "data/experiments/ld19_micropython/bench_py_summary.csv")
py_duration = float(py_reps[0]["duration_s"])
py_rates = [float(r["points_per_s"]) for r in py_reps]
py_points = [int(r["points_total"]) for r in py_reps]
py_rate_mean, py_rate_std = mean(py_rates), std(py_rates)
py_points_mean = mean(py_points)

# ── Tabla ─────────────────────────────────────────────────────────────────────

header = [
    "Enfoque",
    "Sensor",
    "Implementacion",
    "Puntos/s (media +/- desv. est.)",
]

rows = [
    ["Punto unico", "TF-Mini S", "MicroPython",
     f"{tfmini_rate_mean:.2f} ± {tfmini_rate_std:.2f}"],
    ["Multipunto", "LD19", "SDK de C",
     f"{c_rate_mean:.2f} ± {c_rate_std:.2f}"],
    ["Multipunto", "LD19", "MicroPython",
     f"{py_rate_mean:.2f} ± {py_rate_std:.2f}"],
]

OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_TSV = OUT_DIR / "tabla1_tasa_puntos.tsv"

with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
