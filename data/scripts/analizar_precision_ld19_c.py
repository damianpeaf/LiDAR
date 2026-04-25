import csv
import math
import statistics
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "experiments" / "ld19_precision" / "c"
DISTANCES_FILE = DATA_DIR / "distancias_reales.csv"
SUMMARY_FILE = DATA_DIR / "summary.csv"


def read_distances() -> list[dict]:
    with DISTANCES_FILE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_points(capture: str) -> list[dict]:
    path = DATA_DIR / f"{capture}_points.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize_capture(distance_row: dict) -> dict:
    capture = distance_row["captura"]
    points = read_points(capture)
    distances = [float(point["distance_mm"]) for point in points]
    intensities = [float(point["intensity"]) for point in points]

    real_mm = float(distance_row["distancia_real_mm"])
    errors = [distance - real_mm for distance in distances]
    abs_errors = [abs(error) for error in errors]
    squared_errors = [error * error for error in errors]

    mean_mm = statistics.mean(distances) if distances else 0.0
    rmse = math.sqrt(statistics.mean(squared_errors)) if squared_errors else 0.0
    mean_abs_error = statistics.mean(abs_errors) if abs_errors else 0.0
    relative_error_pct = (mean_abs_error / real_mm * 100.0) if real_mm else 0.0

    return {
        "captura": capture,
        "distancia_nominal_mm": int(float(distance_row["distancia_nominal_cm"]) * 10),
        "distancia_real_mm": int(real_mm),
        "n_total": len(points),
        "n_validas": len(distances),
        "n_invalidas": len(points) - len(distances),
        "media_mm": round(mean_mm, 3),
        "mediana_mm": round(statistics.median(distances), 3) if distances else 0,
        "sd_mm": round(statistics.stdev(distances), 3) if len(distances) > 1 else 0,
        "rmse_mm": round(rmse, 3),
        "error_absoluto_medio_mm": round(mean_abs_error, 3),
        "error_relativo_pct": round(relative_error_pct, 3),
        "intensidad_media": round(statistics.mean(intensities), 3) if intensities else 0,
        "angulo_centro_deg": distance_row["ventana_centro_deg"],
        "angulo_semiancho_deg": distance_row["ventana_semiancho_deg"],
        "observaciones": distance_row.get("observaciones", ""),
    }


def main() -> int:
    rows = [summarize_capture(row) for row in read_distances()]
    if not rows:
        raise SystemExit("No hay distancias para analizar")

    with SUMMARY_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Resumen escrito en {SUMMARY_FILE}")
    for row in rows:
        print(
            f"{row['captura']}: media={row['media_mm']} mm, "
            f"sd={row['sd_mm']} mm, rmse={row['rmse_mm']} mm, "
            f"error_abs={row['error_absoluto_medio_mm']} mm"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
