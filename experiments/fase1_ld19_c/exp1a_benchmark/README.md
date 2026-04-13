# Experimento 1A — Benchmark de rendimiento C SDK

**Objetivo:** Caracterizar la capacidad de procesamiento del C SDK con el LD19 de forma reproducible con 3 repeticiones independientes.

**Responde a:** OBJ 3

## Setup

- Sensor: LD19 conectado a Pico W, sin servo activo
- Firmware: `experiments/ld19c/bench.txt` (el benchmark standalone)
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Duración: 60 segundos por repetición
- Repeticiones: 3 (reiniciar firmware entre cada una)
- Temperatura ambiente estable

## Datos a capturar

Por cada repetición, el firmware genera un reporte con:

- Frames recibidos / procesados / con error CRC / con error de header
- Bytes recibidos / bytes procesados
- Puntos procesados totales
- Puntos/s, Frames/s, Bytes/s
- Tiempo promedio / mínimo / máximo por frame (µs)
- Tiempo promedio de CRC por frame (µs)
- Tiempo promedio de parsing por frame (µs)
- % CPU en UART / CRC / parsing

## Checklist

- [ ] Repetición 1 — reporte guardado
- [ ] Repetición 2 — reporte guardado
- [ ] Repetición 3 — reporte guardado
- [ ] Verificar que las 3 repeticiones son consistentes entre sí

## Entregables

```
data/experiments/ld19c/bench_c_rep1.txt
data/experiments/ld19c/bench_c_rep2.txt
data/experiments/ld19c/bench_c_rep3.txt
```

## Análisis que habilita

- **T2:** Benchmark C SDK — media ± desviación estándar de las 3 repeticiones
- **T4:** Base para comparación directa con MicroPython (exp 2A)
- **G1:** Frames/s y Puntos/s comparativo
- **G2:** Tiempo por operación (CRC, parsing, UART)
- **G3:** Tasa de error global
- **G12:** Throughput vs. TF-Mini S
