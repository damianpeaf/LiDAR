"""
Tabla 4: Benchmark comparativo de procesamiento LD19 — SDK de C vs MicroPython.
Fuentes: experimentos 1A y 2A.
Solo metricas disponibles en ambas implementaciones.
"""

import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ms(rows, key):
    vals = [float(r[key]) for r in rows]
    m = statistics.mean(vals)
    s = statistics.stdev(vals)
    return f"{m:.2f} ± {s:.2f}"


c_reps  = load(ROOT / "data/experiments/ld19c/bench_c_summary.csv")
py_reps = load(ROOT / "data/experiments/ld19_micropython/bench_py_summary.csv")

header = ["Metrica", "SDK de C", "MicroPython"]

rows = [
    ["Replicas",                              f"{len(c_reps)}",                    f"{len(py_reps)}"],
    ["Duracion por replica (s)",              f"{float(c_reps[0]['duration_s']):.0f}", f"{float(py_reps[0]['duration_s']):.0f}"],
    ["Frames/s",                              ms(c_reps, "frames_per_s"),          ms(py_reps, "frames_per_s")],
    ["Puntos/s",                              ms(c_reps, "points_per_s"),          ms(py_reps, "points_per_s")],
    ["Bytes/s (UART)",                        ms(c_reps, "bytes_per_s"),           ms(py_reps, "bytes_per_s")],
    ["Tiempo promedio por frame (us)",        ms(c_reps, "avg_frame_time_us"),     ms(py_reps, "avg_frame_time_us")],
    ["Tiempo promedio de parsing (us)",       ms(c_reps, "avg_parse_time_us"),     ms(py_reps, "avg_parse_time_us")],
    ["Tasa de error (%)",                     ms(c_reps, "error_rate_pct"),        ms(py_reps, "error_rate_pct")],
    ["Errores CRC (total por replica)",       ms(c_reps, "frames_crc_error"),      ms(py_reps, "frames_crc_error")],
]

OUT_TSV = OUT_DIR / "tabla4_benchmark_ld19.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
