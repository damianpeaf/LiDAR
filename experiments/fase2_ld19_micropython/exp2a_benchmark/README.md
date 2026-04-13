# Experimento 2A — Benchmark de rendimiento MicroPython

**Objetivo:** Caracterizar la capacidad de procesamiento de MicroPython con el LD19. Condiciones idénticas al experimento 1A para permitir comparación directa.

**Responde a:** OBJ 3

## Setup

Idéntico al experimento 1A — solo cambia el firmware:

- Sensor: LD19 conectado a Pico W, sin servo activo
- Firmware: script MicroPython de benchmark (sin WiFi, solo serial)
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Duración: 60 segundos por repetición
- Repeticiones: 3 (reiniciar firmware entre cada una)

## Datos a capturar

Idénticos a 1A — el script MicroPython debe generar exactamente las mismas métricas:

- Frames recibidos / procesados / con error CRC / con error de header
- Bytes recibidos / bytes procesados
- Puntos procesados totales
- Puntos/s, Frames/s, Bytes/s
- Tiempo promedio / mínimo / máximo por frame (µs)
- Tiempo promedio de CRC por frame (µs)
- Tiempo promedio de parsing por frame (µs)
- % CPU en UART / CRC / parsing

## Checklist

- [ ] Script MicroPython de benchmark listo y verificado
- [ ] Repetición 1 — reporte guardado
- [ ] Repetición 2 — reporte guardado
- [ ] Repetición 3 — reporte guardado
- [ ] Verificar consistencia entre las 3 repeticiones

## Entregables

```
data/experiments/ld19_micropython/bench_py_rep1.txt
data/experiments/ld19_micropython/bench_py_rep2.txt
data/experiments/ld19_micropython/bench_py_rep3.txt
```

## Análisis que habilita

- **T3:** Benchmark MicroPython — media ± SD de las 3 repeticiones
- **T4:** Comparativa directa C SDK vs. MicroPython con factor ×N
- **G1:** Frames/s y Puntos/s comparativo
- **G2:** Tiempo por operación en escala logarítmica
- **G3:** Tasa de error comparativa
