# Experimentos — Sistema LiDAR 3D

Documentación completa de todos los experimentos realizados para la tesis.
**No modificar el orden de ejecución.** El dispositivo se desmonta progresivamente.

## Estado general

- [ ] **FASE 1** — LD19 con C SDK (dispositivo armado)
- [ ] **FASE 2** — LD19 con MicroPython (mismo dispositivo, cambiar firmware)
- [ ] **FASE 3** — TF-Mini S estático (desarmar Pico, conectar TF-Mini S)
- [ ] **FASE 4** — Aplicación arqueológica en Huehuetenango (rearmar dispositivo completo)

---

## Índice de experimentos

| ID | Nombre | Fase | Estado | README |
|----|--------|------|--------|--------|
| 1A | Benchmark C SDK | 1 | ⬜ Pendiente | [→](fase1_ld19_c/exp1a_benchmark/README.md) |
| 1B | Precisión LD19 con C | 1 | ⬜ Pendiente | [→](fase1_ld19_c/exp1b_precision/README.md) |
| 1C | Escaneo 3D objeto referencia (C) | 1 | ⬜ Pendiente | [→](fase1_ld19_c/exp1c_scan_referencia/README.md) |
| 1D | Registro multi-posición referencia (C) | 1 | ⬜ Pendiente | [→](fase1_ld19_c/exp1d_multipos_referencia/README.md) |
| 2A | Benchmark MicroPython | 2 | ⬜ Pendiente | [→](fase2_ld19_micropython/exp2a_benchmark/README.md) |
| 2B | Precisión LD19 con MicroPython | 2 | ⬜ Pendiente | [→](fase2_ld19_micropython/exp2b_precision/README.md) |
| 2C | Escaneo 3D objeto referencia (Python) | 2 | ⬜ Pendiente | [→](fase2_ld19_micropython/exp2c_scan_referencia/README.md) |
| 3A | Benchmark TF-Mini S | 3 | ⬜ Pendiente | [→](fase3_tfminis/exp3a_benchmark/README.md) |
| 3B | Precisión TF-Mini S | 3 | ⬜ Pendiente | [→](fase3_tfminis/exp3b_precision/README.md) |
| NET1 | Comparativa transmisión por red | 1/2 | ⬜ Pendiente | [→](exp_red_transmision/README.md) |
| 4A | Escaneo arqueológico posición única | 4 | ⬜ Pendiente | [→](fase4_arqueologia/exp4a_scan_espacio/README.md) |
| 4B | Validación dimensional modelo | 4 | ⬜ Pendiente | [→](fase4_arqueologia/exp4b_validacion/README.md) |
| 4C | Registro multi-posición arqueológico | 4 | ⬜ Pendiente | [→](fase4_arqueologia/exp4c_multipos/README.md) |

---

## Producibles finales

### Tablas para el capítulo 4

| ID | Tabla | Experimentos fuente |
|----|-------|---------------------|
| T1 | Especificaciones técnicas LD19 vs. TF-Mini S | Datasheets |
| T2 | Benchmark C SDK — media ± SD (3 repeticiones) | 1A |
| T3 | Benchmark MicroPython — media ± SD (3 repeticiones) | 2A |
| T4 | Comparativa C SDK vs. MicroPython (todas las métricas, factor ×N) | 1A + 2A |
| T5 | Precisión LD19 — error medio, RMSE, SD por distancia | 1B |
| T6 | Precisión TF-Mini S — error medio, RMSE, SD por distancia | 3B |
| T7 | Comparativa de precisión LD19 vs. TF-Mini S | 1B + 3B |
| T8 | Comparativa densidad nube 3D: LD19-C vs. LD19-Python vs. TF-Mini S | 1C + 2C + sesiones existentes |
| T9 | Validación modelo 3D — dimensiones reales vs. modelo vs. error | 1C + 4B |
| T10 | Resumen aplicación arqueológica — posiciones, puntos, tiempo, error | 4A + 4B + 4C |
| docs T4 | Comparativa de transmisión de datos por red | NET1 + telemetría del server |

### Gráficas para el capítulo 4

| ID | Gráfica | Tipo | Experimentos fuente |
|----|---------|------|---------------------|
| G1 | Frames/s y Puntos/s: C SDK vs. MicroPython | Barras agrupadas | 1A + 2A |
| G2 | Tiempo por operación (CRC, parsing, UART): C vs. Python | Barras, escala log | 1A + 2A |
| G3 | Tasa de error (CRC, header, global): C vs. Python | Barras | 1A + 2A |
| G4 | Error de medición vs. distancia: LD19 vs. TF-Mini S | Líneas con banda de error | 1B + 3B |
| G5 | Distribución de lecturas por distancia: ambos sensores | Boxplot (2×5 cajas) | 1B + 3B |
| G6 | Intensidad de señal vs. distancia: LD19 vs. TF-Mini S | Líneas | 1B + 3B |
| G7 | Nube de puntos objeto referencia — C SDK (3 vistas) | Capturas de pantalla | 1C |
| G8 | Nube de puntos objeto referencia — MicroPython (3 vistas) | Capturas de pantalla | 2C |
| G9 | Comparación visual densidad: C SDK vs. MicroPython (misma escena) | Capturas lado a lado | 1C + 2C |
| G10 | Nube de puntos espacio arqueológico — posición única | Capturas de pantalla | 4A |
| G11 | Nube de puntos registro multi-posición combinado | Captura de pantalla | 4C |
| G12 | Throughput TF-Mini S vs. LD19: lecturas/s, bytes/s | Barras | 1A + 3A |

### Scripts de análisis a escribir

| Script | Genera | Fuente de datos |
|--------|--------|-----------------|
| `data/scripts/analizar_benchmark.py` | G1, G2, G3, T2, T3, T4, G12 | Reportes .txt de 1A, 2A, 3A |
| `data/scripts/analizar_precision.py` | G4, G5, G6, T5, T6, T7 | CSVs de 1B, 2B, 3B |
| `data/scripts/analizar_nubes.py` | T8, G7, G8, G9 | JSONs de 1C, 2C |
| `data/scripts/analizar_red.py` | Tabla 4 de `docs/resultados/README.md` | CSV del server + resumen EXP del firmware |

---

## Orden de ejecución

```
[Dispositivo armado: LD19 + servo + C SDK]
    1A  Benchmark C SDK (60s × 3 reps)              ~30 min
    1B  Precisión LD19 con C (5 distancias × 300)   ~45 min
    1C  Escaneo 3D caja referencia (C SDK)           ~45 min
    1D  Registro multi-posición referencia           ~45 min
    NET1-C Transmisión por red C SDK                  ~15 min
    ── Viaje a Huehuetenango ──
    4A  Escaneo arqueológico posición única       ─┐
    4B  Validación dimensional                     ├─ En campo
    4C  Registro multi-posición arqueológico       ┘

[Sin desarmar — cambiar firmware a MicroPython]
    2A  Benchmark MicroPython (60s × 3 reps)         ~30 min
    NET1-PY Transmisión por red MicroPython           ~15 min
    2B  Precisión LD19 con Python (5 distancias)     ~45 min
    2C  Escaneo 3D caja referencia (MicroPython)     ~45 min

[Desarmar Pico — conectar TF-Mini S]
    3A  Benchmark TF-Mini S (60s × 3 reps)           ~30 min
    3B  Precisión TF-Mini S (5 distancias × 300)     ~45 min
```

**Tiempo en laboratorio:** ~6 horas en 2 sesiones
**Tiempo en campo:** ~3–4 horas incluyendo desplazamiento interno
