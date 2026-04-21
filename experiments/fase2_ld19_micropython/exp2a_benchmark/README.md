# Experimento 2A — Benchmark de rendimiento MicroPython

**Objetivo:** Caracterizar la capacidad de procesamiento de MicroPython con el LD19 en condiciones idénticas a 1A para permitir comparación directa y defendible con C.

**Responde a:** OBJ 3

## Setup

Idéntico al experimento 1A — solo cambia el firmware:

- Sensor: LD19 conectado a Pico W, sin servo activo
- Firmware: script MicroPython de benchmark (sin WiFi, solo serial)
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Duración: 60 segundos por repetición
- Repeticiones: 3 (reiniciar firmware entre cada una)

## Datos a capturar

### Métricas mínimas por repetición

- duración real de la corrida (s)
- frames recibidos
- frames válidos / procesados
- frames inválidos por CRC
- frames inválidos por header o desincronización
- puntos totales procesados
- frames/s
- puntos/s
- bytes/s
- tiempo promedio por frame (µs)

### Métricas deseables

- tiempo mínimo / máximo por frame (µs)
- RAM libre antes y después de la corrida
- cantidad de lecturas válidas vs. inválidas en porcentaje

### Resumen sugerido (`bench_py_summary.csv`)

```csv
repeticion,duracion_s,frames_recibidos,frames_validos,frames_crc_error,frames_header_error,puntos_totales,frames_por_s,puntos_por_s,bytes_por_s,tiempo_promedio_frame_us,ram_libre_bytes,pct_frames_validos,observaciones
1,60.0,0,0,0,0,0,0,0,0,0,,0,
```

## Checklist

- [ ] Script MicroPython de benchmark listo y verificado
- [ ] Repetición 1 — reporte guardado
- [ ] Repetición 2 — reporte guardado
- [ ] Repetición 3 — reporte guardado
- [ ] Resumen CSV completado con una fila por repetición
- [ ] Verificar consistencia entre las 3 repeticiones

## Entregables

```
data/experiments/ld19_micropython/bench_py_rep1.txt
data/experiments/ld19_micropython/bench_py_rep2.txt
data/experiments/ld19_micropython/bench_py_rep3.txt
data/experiments/ld19_micropython/bench_py_summary.csv
```

## Análisis que habilita

- **T3:** Benchmark MicroPython — media ± SD de las 3 repeticiones
- **T4:** Comparativa directa C SDK vs. MicroPython con foco en throughput, tasa de error, porcentaje válido y RAM si está disponible
- **G1:** Frames/s y Puntos/s comparativo
- **G2:** Tiempo por operación en escala logarítmica
- **G3:** Tasa de error comparativa
