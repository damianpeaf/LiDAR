# Experimentos — Estado real ejecutado

Este índice refleja lo que **sí se ejecutó y tiene artefactos verificables** en el repo.

## Experimentos ejecutados

| ID | Nombre | Estado | Evidencia principal |
|----|--------|--------|---------------------|
| 1A | Benchmark LD19 con SDK de C | Completado (3 reps) | `data/experiments/ld19c/bench_c_summary.csv` |
| 1B | Precisión LD19 con SDK de C | Completado (4 distancias) | `data/experiments/ld19_precision/c/precision_summary.csv` |
| 1C | Escaneo 3D objeto referencia con C | Completado (captura sectorial) | `data/experiments/ld19_scan/caja_referencia_c_telemetry_summary.csv` |
| 2A | Benchmark LD19 con MicroPython | Completado (3 reps) | `data/experiments/ld19_micropython/bench_py_summary.csv` |
| NET1-C | Red SDK de C | Completado (rep1) | `data/experiments/red/c_sdk_network_summary.csv` + `data/experiments/red/c_sdk_network_rep1_server.csv` |
| NET1-PY | Red MicroPython | Completado (rep1) | `data/experiments/red/micropython_network_summary.csv` + `data/experiments/red/micropython_network_rep1_server.csv` |

## Experimentos no ejecutados (sin datos defendibles)

- 1D, 2B, 2C, 3A, 3B, 4A, 4B, 4C.

Si no hay artefactos reproducibles en `data/experiments/`, se considera no ejecutado para resultados finales.

## Cobertura actual para `docs/resultados/README.md`

Con los datos actuales se puede sostener:

- **Tabla 3 (benchmark C vs MicroPython):** sí, usando 1A + 2A.
- **Tabla 4 (red C vs MicroPython):** sí, usando NET1-C + NET1-PY (serial + server).
- **Tabla 5 (precisión LD19 con C):** sí, usando 1B.
- **Tabla 6 (parámetros y métricas del escaneo del prisma):** sí, usando 1C.

No hay base suficiente hoy para tablas/figuras dependientes de:

- TF-Mini S (3A/3B),
- MicroPython precisión/escaneo 3D (2B/2C),
- aplicación arqueológica (4A/4B/4C).

## Referencias de ejecución por experimento

- 1A README: `experiments/fase1_ld19_c/exp1a_benchmark/README.md`
- 1B README: `experiments/fase1_ld19_c/exp1b_precision/README.md`
- 1C README: `experiments/fase1_ld19_c/exp1c_scan_referencia/README.md`
- 2A README: `experiments/fase2_ld19_micropython/exp2a_benchmark/README.md`
- NET1 README: `experiments/exp_red_transmision/README.md`

## Nota metodológica

Este README prioriza trazabilidad de datos sobre planificación histórica. Si un experimento se ejecuta luego, se agrega cuando existan artefactos versionados y verificables.
