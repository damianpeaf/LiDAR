"""
Convierte datasets LiDAR de coordenadas esfericas {r, theta, phi, strength}
al formato cartesiano {x, y, z, intensity} requerido por el visualizador.

Convencion de coordenadas:
  theta = angulo de paneo (0-180 grados, eje horizontal, servo pan)
  phi   = angulo de inclinacion (0-135 grados, eje vertical, servo tilt)
  r     = distancia en mm

Conversion esferico -> cartesiano:
  x = r * sin(phi) * cos(theta)
  y = r * sin(phi) * sin(theta)
  z = r * cos(phi)

El campo 'strength' del TF-Mini S es proporcional a reflectividad.
Se normaliza a 0-255 para el campo 'intensity' del visualizador.
Valores r=0 o r>=12000 se descartan (OOR / sin retorno).
"""

import json
import math
import os
from pathlib import Path

BASE = Path(__file__).parent.parent.parent

DATASETS = {
    "dataset-01": BASE / "data/apps/visualizer/public/puntos1.json",
    "dataset-02": BASE / "data/apps/visualizer/public/puntos2.json",
    "dataset-03": BASE / "data/apps/visualizer/public/puntos copy.json",
    "dataset-04": BASE / "data/apps/visualizer/public/puntos copy 2.json",
    "dataset-05": BASE / "apps/visualizer/public/puntos.json",
}

OUT_DIR = BASE / "data/scripts/converted"
OUT_DIR.mkdir(exist_ok=True)

def normalize_intensity(strength_vals, strength):
    """Normaliza strength al rango 0-255."""
    s_min = min(strength_vals)
    s_max = max(strength_vals)
    if s_max == s_min:
        return 128
    return round((strength - s_min) / (s_max - s_min) * 255)

def convert(name, path):
    print(f"\nProcesando {name} ({path.name})...")
    with open(path, encoding="utf-8") as f:
        points = json.load(f)

    if not points:
        print(f"  [VACIO] Saltando.")
        return None

    # Filtrar valores fuera de rango
    valid = [p for p in points if 0 < p["r"] < 12000]
    removed = len(points) - len(valid)
    print(f"  Total: {len(points):,}  |  Validos: {len(valid):,}  |  Descartados (OOR): {removed:,}")

    if not valid:
        print(f"  [SIN PUNTOS VALIDOS]")
        return None

    strength_vals = [p["strength"] for p in valid]

    converted = []
    for p in valid:
        r     = p["r"]
        # theta y phi en grados -> radianes
        theta = math.radians(p["theta"])
        phi   = math.radians(p["phi"])

        x = round(r * math.sin(phi) * math.cos(theta), 2)
        y = round(r * math.sin(phi) * math.sin(theta), 2)
        z = round(r * math.cos(phi), 2)
        intensity = normalize_intensity(strength_vals, p["strength"])

        converted.append({"intensity": intensity, "x": x, "y": y, "z": z})

    out_path = OUT_DIR / f"{name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(converted, f, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    print(f"  Guardado: {out_path.name}  ({size_kb:.1f} KB, {len(converted):,} puntos)")
    return out_path

def main():
    print("=== Conversion de datasets LiDAR ===")
    output_files = {}
    for name, path in DATASETS.items():
        if not path.exists():
            print(f"\n[NO EXISTE] {path}")
            continue
        out = convert(name, path)
        if out:
            output_files[name] = out

    print(f"\n=== Archivos generados en {OUT_DIR} ===")
    for name, p in output_files.items():
        print(f"  {name}.json  ({p.stat().st_size/1024:.1f} KB)")

    print("\nPara subir a R2 (lidar-cloud bucket), ejecutar:")
    for name in output_files:
        print(f"  npx wrangler r2 object put lidar-cloud/datasets/{name}.json --file data/scripts/converted/{name}.json --content-type application/json")

if __name__ == "__main__":
    main()
