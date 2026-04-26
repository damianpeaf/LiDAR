"""
Tabla 9: Validacion geometrica del prisma de referencia.
Comparacion entre dimensiones reales y medidas obtenidas desde la nube de puntos
con CloudCompare. Metodo: planos seccionantes (ancho) y seleccion de esquinas (alto/largo).
"""

import csv
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

# Dimensiones reales del prisma (mm)
REAL = {"Ancho": 92.0, "Largo": 133.0, "Alto": 88.0}

# Mediciones CloudCompare
MEASURED = {
    "Ancho": {"valor": 118.033, "std": 6.061,  "metodo": "Distancia entre planos seccionantes"},
    "Largo": {"valor": 123.467, "std": None,    "metodo": "Distancia entre esquinas (deltaXY)"},
    "Alto":  {"valor": 95.492,  "std": None,    "metodo": "Distancia entre esquinas (deltaZY)"},
}

header = [
    "Dimension",
    "Real (mm)",
    "Medido (mm)",
    "Desv. est. (mm)",
    "Error absoluto (mm)",
    "Error relativo (%)",
    "Metodo CloudCompare",
]

rows = []
for dim in ["Ancho", "Largo", "Alto"]:
    real = REAL[dim]
    med  = MEASURED[dim]["valor"]
    std  = MEASURED[dim]["std"]
    err_abs = abs(med - real)
    err_rel = err_abs / real * 100

    rows.append([
        dim,
        f"{real:.1f}",
        f"{med:.1f}",
        f"{std:.1f}" if std is not None else "-",
        f"{err_abs:.1f}",
        f"{err_rel:.1f}",
        MEASURED[dim]["metodo"],
    ])

OUT_TSV = OUT_DIR / "tabla9_validacion_geometrica_prisma.tsv"
with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(header)
    writer.writerows(rows)

print(f"Guardado: {OUT_TSV}")
