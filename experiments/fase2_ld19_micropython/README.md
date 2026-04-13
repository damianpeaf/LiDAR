# Fase 2 — LD19 con MicroPython

**Hardware:** LD19 + servo + Pico W (mismo dispositivo que Fase 1, NO desarmar)
**Firmware:** MicroPython — adaptar `experiments/lidar/device/init.py`
**Estado del dispositivo:** NO DESARMAR durante esta fase

## Prerrequisito crítico

Adaptar el script MicroPython para que:
1. **No transmita por red** durante el benchmark (desactivar WiFi/HTTP — que no interfiera con la medición)
2. Imprima por serial las mismas métricas que el C SDK: frames/s, puntos/s, % CRC error, tiempo por frame
3. Mida tiempos con `time.ticks_us()` para CRC y parsing
4. Para 2C: reactivar servo y transmisión para escaneo completo

**Regla de oro:** Las condiciones de los experimentos 2A y 2B deben ser idénticas a 1A y 1B. Mismo sensor, misma pared, misma distancia, misma duración.

## Checklist de fase

- [ ] Script MicroPython de benchmark adaptado y probado
- [ ] 2A — Benchmark completado (3 repeticiones)
- [ ] 2B — Precisión medida (5 distancias)
- [ ] 2C — Escaneo 3D objeto de referencia

## Experimentos

| ID | Experimento | README |
|----|-------------|--------|
| 2A | Benchmark MicroPython | [→](exp2a_benchmark/README.md) |
| 2B | Precisión LD19 con MicroPython | [→](exp2b_precision/README.md) |
| 2C | Escaneo 3D objeto de referencia (Python) | [→](exp2c_scan_referencia/README.md) |
