# Experimento 2B — Precisión del LD19 con MicroPython

**Objetivo:** Verificar si la implementación del firmware afecta la precisión del sensor. Hipótesis: los errores deben ser iguales a 1B (el sensor es el mismo). Si difieren, indica pérdida de datos por desincronización UART en MicroPython.

**Responde a:** OBJ 2, OBJ 3

## Setup

Idéntico al experimento 1B — solo cambia el firmware. Mismas 5 distancias, misma pared blanca, 300 lecturas por distancia.

## Formato CSV

```
distancia_nominal_mm,lectura_sensor_mm,intensidad
```

## Checklist

- [ ] 20 cm — 300 lecturas capturadas
- [ ] 50 cm — 300 lecturas capturadas
- [ ] 100 cm — 300 lecturas capturadas
- [ ] 150 cm — 300 lecturas capturadas
- [ ] 200 cm — 300 lecturas capturadas

## Entregables

```
data/experiments/ld19_micropython/precision/d020cm.csv
data/experiments/ld19_micropython/precision/d050cm.csv
data/experiments/ld19_micropython/precision/d100cm.csv
data/experiments/ld19_micropython/precision/d150cm.csv
data/experiments/ld19_micropython/precision/d200cm.csv
```

## Análisis que habilita

- Comparar error medio y RMSE entre C SDK (1B) y MicroPython (2B)
- Si son iguales → la implementación no introduce error de medición
- Si difieren → pérdida de frames en MicroPython afecta incluso la precisión reportada
- Conecta OBJ 2 y OBJ 3 de forma directa
