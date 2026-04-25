import argparse
import csv
import statistics
from pathlib import Path


def angular_distance(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def load_points(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize_window(points: list[dict], center: float, half_width: float) -> dict:
    selected = [
        point for point in points
        if angular_distance(float(point["pan_deg"]), center) <= half_width
    ]
    distances = [float(point["distance_mm"]) for point in selected]
    intensities = [float(point["intensity"]) for point in selected]

    if not distances:
        return {
            "center_deg": center,
            "half_width_deg": half_width,
            "n": 0,
            "distance_min_mm": "",
            "distance_median_mm": "",
            "distance_mean_mm": "",
            "distance_max_mm": "",
            "distance_sd_mm": "",
            "intensity_mean": "",
        }

    return {
        "center_deg": center,
        "half_width_deg": half_width,
        "n": len(distances),
        "distance_min_mm": round(min(distances), 2),
        "distance_median_mm": round(statistics.median(distances), 2),
        "distance_mean_mm": round(statistics.mean(distances), 2),
        "distance_max_mm": round(max(distances), 2),
        "distance_sd_mm": round(statistics.stdev(distances), 2) if len(distances) > 1 else 0,
        "intensity_mean": round(statistics.mean(intensities), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume distancias por ventanas angulares cardinales")
    parser.add_argument("points_csv", type=Path, help="CSV generado por capturar_serial_experimento.py")
    parser.add_argument("--half-width", type=float, default=5.0, help="Semiancho de ventana angular en grados")
    parser.add_argument("--centers", default="0,90,180,270", help="Centros angulares separados por coma")
    args = parser.parse_args()

    points = load_points(args.points_csv)
    centers = [float(value.strip()) for value in args.centers.split(",") if value.strip()]
    summaries = [summarize_window(points, center, args.half_width) for center in centers]

    fieldnames = list(summaries[0].keys()) if summaries else []
    writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
