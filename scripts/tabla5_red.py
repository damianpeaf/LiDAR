"""
Tabla 5: Comparativa de transmision de datos por red — SDK de C vs MicroPython.
Fuentes: experimentos NET1-C y NET1-PY (1 replica cada uno).
Sin media +/- sigma por ser replica unica.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))[0]


c  = load(ROOT / "data/experiments/red/c_sdk_network_summary.csv")
py = load(ROOT / "data/experiments/red/micropython_network_summary.csv")

# Tasa de exito de envio
c_send_success_pct  = float(c["batches_sent"]) / (float(c["batches_sent"]) + float(c["batch_failures"])) * 100
py_send_success_pct = float(py["messages_sent"]) / (float(py["messages_sent"]) + float(py["send_failures"])) * 100

header = ["Metrica", "SDK de C", "MicroPython"]

rows = [
    ["Duracion (s)",
     f"{float(c['duration_s']):.0f}",
     f"{float(py['duration_s']):.0f}"],
    ["Unidad de transmision",
     "Lote binario (batch)",
     "Mensaje WebSocket (texto)"],
    ["Unidades enviadas",
     c["batches_sent"],
     py["messages_sent"]],
    ["Intentos de envio fallidos",
     c["batch_failures"],
     py["send_failures"]],
    ["Tasa de exito de envio (%)",
     f"{c_send_success_pct:.2f}",
     f"{py_send_success_pct:.2f}"],
    ["Tamano medio por unidad (bytes)",
     f"{float(c['avg_payload_bytes_per_batch']):.1f}",
     f"{float(py['avg_payload_bytes_per_message']):.1f}"],
    ["Payload bytes/s",
     f"{float(c['payload_bytes_per_s']):.1f}",
     f"{float(py['payload_bytes_per_s']):.1f}"],
    ["Bytes/s WebSocket",
     f"{float(c['websocket_frame_bytes_per_s']):.1f}",
     f"{float(py['websocket_frame_bytes_per_s']):.1f}"],
    ["Puntos/s procesados bajo carga de red",
     f"{float(c['points_per_s']):.1f}",
     f"{float(py['points_per_s']):.1f}"],
    ["Tasa de error UART (%)",
     f"{float(c['error_rate_pct']):.3f}",
     f"{float(py['error_rate_pct']):.3f}"],
    ["Tiempo promedio de parsing (us)",
     f"{float(c['avg_parse_time_us']):.0f}",
     f"{float(py['avg_parse_time_us']):.0f}"],
]

OUT_TSV = OUT_DIR / "tabla5_red.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
