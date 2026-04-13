# Experimento 3A — Benchmark de rendimiento TF-Mini S

**Objetivo:** Caracterizar throughput, latencia y tasa de errores del TF-Mini S con C SDK. Comparar con el LD19 (experimento 1A).

**Responde a:** OBJ 2

## Setup

- TF-Mini S conectado directamente a Pico W (UART1, 115,200 baud, pines 8/9)
- Firmware de benchmark adaptado de `experiments/tf_poc/tf_poc.c`
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Duración: 60 segundos por repetición
- Repeticiones: 3

## Datos a capturar

- Frames recibidos / válidos / con checksum inválido
- Lecturas/s efectivas
- Tiempo promedio / mínimo / máximo por lectura (µs)
- Bytes leídos / bytes por segundo

## Checklist

- [ ] Firmware bench_tf.c compilado y flasheado
- [ ] Repetición 1 — reporte guardado
- [ ] Repetición 2 — reporte guardado
- [ ] Repetición 3 — reporte guardado

## Entregables

```
experiments/tf_poc/bench_tf.c                    ← script nuevo a crear
data/experiments/tf_poc/bench_tf_rep1.txt
data/experiments/tf_poc/bench_tf_rep2.txt
data/experiments/tf_poc/bench_tf_rep3.txt
```

## Análisis que habilita

- **G12:** Throughput comparativo TF-Mini S vs. LD19 (lecturas/s, bytes/s)
- Parte de la tabla comparativa de sensores (OBJ 2)
