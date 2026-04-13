# Fase 3 — TF-Mini S estático

**Hardware:** TF-Mini S conectado directamente a Pico W
**Firmware:** C SDK — adaptar `experiments/tf_poc/tf_poc.c`
**Estado del dispositivo:** Desarmar Pico del dispositivo LD19. Conectar TF-Mini S (UART a 115,200 baud).

## Justificación metodológica

> "Para aislar las características intrínsecas de cada sensor de las variables del sistema mecánico, la comparación de precisión se realizó en condición estática controlada. La diferencia en capacidad de cobertura 3D se establece a partir de las características operacionales de cada sensor: el LD19 cubre 360° por rotación propia; el TF-Mini S requiere posicionamiento mecánico externo para cada punto de medición."

## Prerrequisito

Adaptar `experiments/tf_poc/tf_poc.c` para generar un reporte de benchmark en el mismo formato que el LD19, midiendo:
- Lecturas/s efectivas
- Tiempo promedio / mín / máx por lectura (µs)
- Frames con checksum inválido
- Bytes/s

## Checklist de fase

- [ ] Firmware de benchmark TF-Mini S adaptado y compilado
- [ ] 3A — Benchmark completado (3 repeticiones)
- [ ] 3B — Precisión medida (5 distancias)

## Experimentos

| ID | Experimento | README |
|----|-------------|--------|
| 3A | Benchmark TF-Mini S | [→](exp3a_benchmark/README.md) |
| 3B | Precisión TF-Mini S | [→](exp3b_precision/README.md) |
