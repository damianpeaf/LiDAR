# Experimento 1A — Benchmark de rendimiento C SDK

**Objetivo:** Caracterizar la capacidad de procesamiento del C SDK con el LD19 de forma reproducible y dejar una base comparable contra MicroPython.

**Responde a:** OBJ 3

## Setup

- Sensor: LD19 conectado a Pico W, sin servo activo
- Firmware: `experiments/ld19c/bench.txt` (el benchmark standalone)
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Duración: 60 segundos por repetición
- Repeticiones: 3 (reiniciar firmware entre cada una)
- Temperatura ambiente estable

## Datos a capturar

### Métricas mínimas por repetición

- duración real de la corrida (s)
- frames recibidos
- frames válidos / procesados
- frames inválidos por CRC
- frames inválidos por header
- puntos totales procesados
- frames/s
- puntos/s
- bytes/s
- tiempo promedio por frame (µs)

### Métricas deseables si ya salen del firmware

- tiempo mínimo / máximo por frame (µs)
- tiempo promedio de CRC por frame (µs)
- tiempo promedio de parsing por frame (µs)
- RAM libre o usada

### Resumen sugerido (`bench_c_summary.csv`)

```csv
repeticion,duracion_s,frames_recibidos,frames_validos,frames_crc_error,frames_header_error,puntos_totales,frames_por_s,puntos_por_s,bytes_por_s,tiempo_promedio_frame_us,ram_libre_bytes,observaciones
1,60.0,0,0,0,0,0,0,0,0,0,,
```

> Si RAM no puede medirse de forma confiable, dejar la columna vacía y anotarlo en `observaciones`.

## Checklist

- [ ] Repetición 1 — reporte guardado
- [ ] Repetición 2 — reporte guardado
- [ ] Repetición 3 — reporte guardado
- [ ] Resumen CSV completado con una fila por repetición
- [ ] Verificar que las 3 repeticiones son consistentes entre sí (variación razonable, sin outliers groseros)

## Entregables

```
data/experiments/ld19c/bench_c_rep1.txt
data/experiments/ld19c/bench_c_rep2.txt
data/experiments/ld19c/bench_c_rep3.txt
data/experiments/ld19c/bench_c_summary.csv
```

## Análisis que habilita

- **T2:** Benchmark C SDK — media ± desviación estándar de las 3 repeticiones
- **T4:** Base para comparación directa con MicroPython (exp 2A), sobre todo en throughput, tasa de error y porcentaje de datos válidos
- **G1:** Frames/s y Puntos/s comparativo
- **G2:** Tiempo por operación (CRC, parsing, UART)
- **G3:** Tasa de error global
- **G12:** Throughput vs. TF-Mini S
