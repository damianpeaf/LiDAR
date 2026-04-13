"""
Script de análisis de datasets LiDAR para la tesis.
Procesa todos los archivos JSON de puntos y genera estadísticas comparativas.

Datasets encontrados:
  - data/apps/visualizer/public/puntos1.json        (TF-Mini, phi=60 → tilt 60°)
  - data/apps/visualizer/public/puntos2.json        (TF-Mini, phi=120 → tilt 120°)
  - data/apps/visualizer/public/puntos copy.json    (TF-Mini, phi=120, sesión más larga)
  - data/apps/visualizer/public/puntos copy 2.json  (TF-Mini, phi=120, sesión más larga)
  - apps/visualizer/public/puntos.json              (LD19, phi=0 → modo 2D)
"""

import json
import os
import statistics
from pathlib import Path

BASE = Path(__file__).parent.parent.parent  # raíz del repo

DATASETS = {
    "TF-Mini S1 (phi=60°)": BASE / "data/apps/visualizer/public/puntos1.json",
    "TF-Mini S2 (phi=120°)": BASE / "data/apps/visualizer/public/puntos2.json",
    "TF-Mini S3 (phi=120°, sesión extendida A)": BASE / "data/apps/visualizer/public/puntos copy.json",
    "TF-Mini S4 (phi=120°, sesión extendida B)": BASE / "data/apps/visualizer/public/puntos copy 2.json",
    "LD19 (2D, phi=0°)": BASE / "apps/visualizer/public/puntos.json",
}

def analyze_dataset(name, path):
    print(f"\n{'='*60}")
    print(f"Dataset: {name}")
    print(f"Archivo: {path}")
    if not path.exists():
        print("  [NO EXISTE]")
        return None

    with open(path, encoding="utf-8") as f:
        points = json.load(f)

    if not points:
        print("  [VACÍO]")
        return None

    n = len(points)
    r_vals       = [p["r"]        for p in points]
    theta_vals   = [p["theta"]    for p in points]
    phi_vals     = [p["phi"]      for p in points]
    strength_vals= [p["strength"] for p in points]

    r_min, r_max = min(r_vals), max(r_vals)
    r_mean = statistics.mean(r_vals)
    r_std  = statistics.stdev(r_vals) if n > 1 else 0

    theta_unique = sorted(set(theta_vals))
    phi_unique   = sorted(set(phi_vals))
    str_mean     = statistics.mean(strength_vals)
    str_std      = statistics.stdev(strength_vals) if n > 1 else 0

    # Cobertura angular: theta 0-180°, phi segun dataset
    theta_coverage = (len(theta_unique) / 181) * 100  # 0..180 = 181 valores

    result = {
        "name": name,
        "n_points": n,
        "r_min": r_min,
        "r_max": r_max,
        "r_mean": round(r_mean, 2),
        "r_std": round(r_std, 2),
        "theta_unique": len(theta_unique),
        "theta_min": min(theta_vals),
        "theta_max": max(theta_vals),
        "phi_unique": len(phi_unique),
        "phi_values": phi_unique[:10],  # primeros 10
        "strength_mean": round(str_mean, 1),
        "strength_std": round(str_std, 1),
        "strength_min": min(strength_vals),
        "strength_max": max(strength_vals),
        "theta_coverage_pct": round(theta_coverage, 1),
    }

    print(f"  Puntos totales:      {n:,}")
    print(f"  Distancia (r) mm:    min={r_min}, max={r_max}, media={r_mean:.1f}, sd={r_std:.1f}")
    print(f"  Theta (°):           {min(theta_vals)}–{max(theta_vals)}, únicos={len(theta_unique)}, cobertura={theta_coverage:.1f}%")
    print(f"  Phi (°) únicos:      {phi_unique[:20]}")
    print(f"  Strength:            min={min(strength_vals)}, max={max(strength_vals)}, media={str_mean:.1f}, sd={str_std:.1f}")
    return result

def main():
    results = {}
    for name, path in DATASETS.items():
        r = analyze_dataset(name, path)
        if r:
            results[name] = r

    print("\n\n" + "="*60)
    print("TABLA COMPARATIVA RESUMEN")
    print("="*60)
    header = f"{'Dataset':<42} {'Puntos':>8} {'r_min':>6} {'r_max':>6} {'r_mean':>7} {'r_std':>6} {'theta_cov%':>10} {'str_mean':>9}"
    print(header)
    print("-"*100)
    for name, r in results.items():
        short = name[:42]
        print(f"{short:<42} {r['n_points']:>8,} {r['r_min']:>6} {r['r_max']:>6} {r['r_mean']:>7.1f} {r['r_std']:>6.1f} {r['theta_coverage_pct']:>10.1f} {r['strength_mean']:>9.1f}")

    # Estadísticas de precisión: variabilidad de r a distancia fija
    print("\n\n" + "="*60)
    print("ANÁLISIS DE PRECISIÓN POR ÁNGULO FIJO (theta=90°)")
    print("="*60)
    for name, path in DATASETS.items():
        if not path.exists(): continue
        with open(path, encoding="utf-8") as f:
            points = json.load(f)
        if not points: continue
        fixed = [p["r"] for p in points if p["theta"] == 90]
        if len(fixed) > 1:
            print(f"  {name[:40]}: n={len(fixed)}, media={statistics.mean(fixed):.1f} mm, sd={statistics.stdev(fixed):.2f} mm, rango={min(fixed)}-{max(fixed)} mm")
        elif fixed:
            print(f"  {name[:40]}: n={len(fixed)}, r={fixed[0]} mm")

    # Densidad de puntos por posición phi
    print("\n\n" + "="*60)
    print("DENSIDAD DE PUNTOS POR NIVEL PHI")
    print("="*60)
    for name, path in DATASETS.items():
        if not path.exists(): continue
        with open(path, encoding="utf-8") as f:
            points = json.load(f)
        if not points: continue
        from collections import Counter
        phi_counts = Counter(p["phi"] for p in points)
        print(f"\n  {name}:")
        for phi, cnt in sorted(phi_counts.items()):
            print(f"    phi={phi:3d}°: {cnt:5d} puntos")

if __name__ == "__main__":
    main()
