# Experimento 3A — Benchmark de rendimiento TF-Mini S

**Objetivo:** Caracterizar throughput, latencia y tasa de errores del TF-Mini S con C SDK y compararlo con el LD19 usando métricas equivalentes y fáciles de obtener.

**Responde a:** OBJ 2

## Setup

- TF-Mini S conectado directamente a Pico W (UART1, 115,200 baud, pines 8/9)
- Firmware de benchmark adaptado de `experiments/tf_poc/tf_poc.c`
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Duración: 60 segundos por repetición
- Repeticiones: 3

## Datos a capturar

### Métricas mínimas por repetición

- duración real de la corrida (s)
- lecturas recibidas
- lecturas válidas
- lecturas inválidas por checksum o parseo
- lecturas/s efectivas
- bytes/s
- tiempo promedio por lectura (µs)

### Métricas deseables

- tiempo mínimo / máximo por lectura (µs)
- RAM libre o usada
- porcentaje de lecturas válidas

### Resumen sugerido (`bench_tf_summary.csv`)

```csv
repeticion,duracion_s,lecturas_recibidas,lecturas_validas,lecturas_invalidas,lecturas_por_s,bytes_por_s,tiempo_promedio_lectura_us,ram_libre_bytes,pct_lecturas_validas,observaciones
1,60.0,0,0,0,0,0,0,,0,
```

## Checklist

- [ ] Firmware bench_tf.c compilado y flasheado
- [ ] Repetición 1 — reporte guardado
- [ ] Repetición 2 — reporte guardado
- [ ] Repetición 3 — reporte guardado
- [ ] Resumen CSV completado con una fila por repetición

## Entregables

```
experiments/tf_poc/bench_tf.c                    ← script nuevo a crear
data/experiments/tf_poc/bench_tf_rep1.txt
data/experiments/tf_poc/bench_tf_rep2.txt
data/experiments/tf_poc/bench_tf_rep3.txt
data/experiments/tf_poc/bench_tf_summary.csv
```

## Análisis que habilita

- **G12:** Throughput comparativo TF-Mini S vs. LD19 (lecturas/s, bytes/s y % válidas)
- Parte de la tabla comparativa de sensores (OBJ 2)
