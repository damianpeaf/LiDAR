#!/usr/bin/env python3
"""
Captura líneas `VALIDATION_STATS ` desde un puerto serial y las persiste en una corrida.

Uso básico:
    python tools/validation/capture_validation_stats.py --port /dev/tty.usbmodemXXXX

Artefactos generados por defecto:
    tools/validation/runs/<timestamp>_<branch>_<commit>/
      - metadata.json
      - validation_stats.jsonl
      - summary.json

Requiere pyserial:
    pip install pyserial
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import serial


PREFIX = "VALIDATION_STATS "
DEFAULT_TARGET_DURATION_SECONDS = 300
PROGRESS_BAR_WIDTH = 30


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_value(repo_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def format_duration(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def render_progress_line(
    elapsed_seconds: float,
    target_duration_seconds: int,
    captured: int,
    parse_failures: int,
) -> str:
    progress_ratio = (
        elapsed_seconds / target_duration_seconds
        if target_duration_seconds > 0
        else 0.0
    )
    bounded_ratio = min(progress_ratio, 1.0)
    filled = int(PROGRESS_BAR_WIDTH * bounded_ratio)
    bar = "#" * filled + "-" * (PROGRESS_BAR_WIDTH - filled)
    percentage = bounded_ratio * 100.0
    overtime = ""

    if progress_ratio > 1.0:
        overtime = f" +{format_duration(elapsed_seconds - target_duration_seconds)}"

    return (
        f"\r[{bar}] {percentage:6.2f}%  elapsed={format_duration(elapsed_seconds)}"
        f" / target={format_duration(target_duration_seconds)}{overtime}"
        f"  lines={captured}  json_errors={parse_failures}"
    )


def build_run_dir(repo_root: Path, output_dir: Path | None) -> Path:
    base_dir = output_dir or (repo_root / "tools" / "validation" / "runs")
    branch = git_value(repo_root, "rev-parse", "--abbrev-ref", "HEAD").replace("/", "-")
    commit = git_value(repo_root, "rev-parse", "--short", "HEAD")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = base_dir / f"{timestamp}_{branch}_{commit}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", required=True, help="Puerto serial, por ejemplo /dev/tty.usbmodemXXXX"
    )
    parser.add_argument(
        "--baud", type=int, default=230400, help="Baudrate serial (default: 230400)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio base opcional para corridas",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Raíz del repo",
    )
    parser.add_argument(
        "--target-duration-seconds",
        type=int,
        default=DEFAULT_TARGET_DURATION_SECONDS,
        help=(
            "Duración objetivo de la prueba para la barra de progreso "
            f"(default: {DEFAULT_TARGET_DURATION_SECONDS})"
        ),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    run_dir = build_run_dir(repo_root, args.output_dir)
    metadata_path = run_dir / "metadata.json"
    output_path = run_dir / "validation_stats.jsonl"
    summary_path = run_dir / "summary.json"

    metadata = {
        "started_at": now_iso(),
        "port": args.port,
        "baud": args.baud,
        "branch": git_value(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "commit": git_value(repo_root, "rev-parse", "--short", "HEAD"),
        "repo_root": str(repo_root),
        "run_dir": str(run_dir),
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )

    captured = 0
    parse_failures = 0
    first_data_at = None
    first_data_monotonic = None
    last_progress_render_monotonic = None

    print(f"Capturando VALIDATION_STATS desde {args.port} a {output_path}")
    print(
        "Esperando primer VALIDATION_STATS para arrancar cronómetro "
        f"(target={format_duration(args.target_duration_seconds)})"
    )

    with (
        serial.Serial(args.port, args.baud, timeout=1) as ser,
        output_path.open("a", encoding="utf-8") as out,
    ):
        try:
            while True:
                raw_line = ser.readline()
                now_monotonic = time.monotonic()

                if first_data_monotonic is not None and (
                    last_progress_render_monotonic is None
                    or now_monotonic - last_progress_render_monotonic >= 1.0
                ):
                    elapsed_seconds = now_monotonic - first_data_monotonic
                    sys.stdout.write(
                        render_progress_line(
                            elapsed_seconds,
                            args.target_duration_seconds,
                            captured,
                            parse_failures,
                        )
                    )
                    sys.stdout.flush()
                    last_progress_render_monotonic = now_monotonic

                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith(PREFIX):
                    continue

                if first_data_monotonic is None:
                    first_data_at = now_iso()
                    first_data_monotonic = now_monotonic
                    print("Primer VALIDATION_STATS detectado, iniciando cronómetro...")

                payload = line[len(PREFIX) :]
                record = {
                    "captured_at": now_iso(),
                    "raw": payload,
                }

                try:
                    record["parsed"] = json.loads(payload)
                except json.JSONDecodeError as exc:
                    parse_failures += 1
                    record["parse_error"] = str(exc)

                out.write(json.dumps(record, sort_keys=True) + "\n")
                out.flush()
                captured += 1

                if first_data_monotonic is not None:
                    elapsed_seconds = now_monotonic - first_data_monotonic
                    sys.stdout.write(
                        render_progress_line(
                            elapsed_seconds,
                            args.target_duration_seconds,
                            captured,
                            parse_failures,
                        )
                    )
                    sys.stdout.flush()
                    last_progress_render_monotonic = now_monotonic

        except KeyboardInterrupt:
            print("\nCaptura interrumpida por usuario")

    elapsed_from_first_data_seconds = None
    if first_data_monotonic is not None:
        elapsed_from_first_data_seconds = round(
            time.monotonic() - first_data_monotonic, 3
        )

    summary_path.write_text(
        json.dumps(
            {
                **metadata,
                "ended_at": now_iso(),
                "captured_lines": captured,
                "first_data_at": first_data_at,
                "elapsed_from_first_data_seconds": elapsed_from_first_data_seconds,
                "json_parse_failures": parse_failures,
                "output_file": str(output_path),
                "target_duration_seconds": args.target_duration_seconds,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(f"Resumen guardado en {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
