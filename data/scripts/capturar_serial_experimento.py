import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover
    print("Falta pyserial. Instala con: pip install pyserial", file=sys.stderr)
    raise


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "experiments" / "ld19c"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def parse_value(raw: str):
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    try:
        if any(ch in raw for ch in ".eE"):
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def parse_structured_line(line: str):
    if not line.startswith("EXP|"):
        return None

    event = {}
    for fragment in line.strip().split("|")[1:]:
        if not fragment or "=" not in fragment:
            continue
        key, value = fragment.split("=", 1)
        event[key] = parse_value(value)
    return event or None


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def append_csv(path: Path, row: dict) -> None:
    ensure_parent(path)
    fieldnames = list(row.keys())
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def build_summary(final_event, metadata, raw_log_path: Path):
    try:
        raw_log_value = str(raw_log_path.relative_to(REPO_ROOT))
    except ValueError:
        raw_log_value = str(raw_log_path)

    summary = {
        "captured_at_utc": utc_now_iso(),
        "raw_log": raw_log_value,
    }
    summary.update(metadata)
    if final_event:
        summary.update(final_event)
    return summary


def run_capture(args):
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = args.name or f"serial_capture_{timestamp}"
    raw_log_path = output_dir / f"{stem}.txt"
    parsed_json_path = output_dir / f"{stem}.json"
    summary_csv_path = output_dir / args.summary_csv_name

    metadata = {
        "port": args.port,
        "host_baud": args.baud,
        "timeout_s": args.timeout,
        "stop_on_done": args.stop_on_done,
        "label": args.label,
    }

    parsed_events = []
    final_report = None
    done_seen = False
    start_monotonic = time.monotonic()

    try:
        with serial.Serial(args.port, args.baud, timeout=0.25) as ser:
            if args.reset_wait > 0:
                time.sleep(args.reset_wait)
                ser.reset_input_buffer()

            print(f"Escuchando {args.port} a {args.baud} baud")
            print(f"RAW -> {raw_log_path}")
            print(f"JSON -> {parsed_json_path}")

            with raw_log_path.open("w", encoding="utf-8") as raw_handle:
                while True:
                    if args.timeout > 0 and (time.monotonic() - start_monotonic) > args.timeout:
                        print("Timeout alcanzado. Cerrando captura.")
                        break

                    packet = ser.readline()
                    if not packet:
                        continue

                    decoded = packet.decode("utf-8", errors="replace").rstrip("\r\n")
                    host_ts = utc_now_iso()
                    raw_handle.write(f"[{host_ts}] {decoded}\n")
                    raw_handle.flush()
                    print(decoded)

                    parsed = parse_structured_line(decoded)
                    if not parsed:
                        continue

                    parsed["host_timestamp_utc"] = host_ts
                    if args.label:
                        parsed["label"] = args.label
                    parsed_events.append(parsed)

                    if parsed.get("event") == "report":
                        final_report = parsed
                    if parsed.get("event") == "done":
                        done_seen = True
                        if args.stop_on_done:
                            break
    except SerialException as exc:
        print(f"No pude abrir el puerto serial: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Captura interrumpida por usuario.")

    payload = {
        "metadata": metadata,
        "events": parsed_events,
        "final_report": final_report,
        "done_seen": done_seen,
    }
    write_json(parsed_json_path, payload)

    if final_report:
        summary_row = build_summary(final_report, metadata, raw_log_path)
        append_csv(summary_csv_path, summary_row)
        print(f"Resumen CSV actualizado: {summary_csv_path}")
    else:
        print("No hubo reporte final parseable; se guardo RAW + JSON de eventos.")

    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Captura telemetria serial del dispositivo y extrae reportes estructurados EXP|..."
    )
    parser.add_argument("--port", required=True, help="Puerto serial del dispositivo, por ejemplo COM5")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate del puerto USB serial")
    parser.add_argument("--timeout", type=float, default=90.0, help="Timeout total de captura en segundos")
    parser.add_argument("--reset-wait", type=float, default=2.0, help="Espera inicial para dejar bootear al dispositivo")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directorio de salida")
    parser.add_argument("--name", default="", help="Base del nombre de archivo sin extension")
    parser.add_argument("--summary-csv-name", default="bench_c_summary.csv", help="Nombre del CSV resumen")
    parser.add_argument("--label", default="", help="Etiqueta opcional para la corrida, por ejemplo rep1")
    parser.add_argument("--stop-on-done", action="store_true", help="Corta cuando llega EXP|event=done")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(run_capture(args))


if __name__ == "__main__":
    main()
