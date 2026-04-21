# Experimento 2B — Precisión del LD19 con MicroPython

**Objetivo:** Verificar si la implementación del firmware afecta la precisión del sensor. Hipótesis: los errores deberían ser muy similares a 1B; si difieren, puede haber pérdida de datos o desincronización UART en MicroPython.

**Responde a:** OBJ 2, OBJ 3

## Setup

Idéntico al experimento 1B — solo cambia el firmware. Mismas 5 distancias, misma pared blanca.

- Mínimo 3 repeticiones por distancia
- Sugerencia simple: 3 bloques de 100 lecturas consecutivas por distancia (300 lecturas en total)

## Formato CSV crudo

```
repeticion,distancia_nominal_mm,distancia_real_mm,lectura_sensor_mm,intensidad,valida
```

### Resumen mínimo por distancia (`summary.csv`)

```csv
distancia_nominal_mm,distancia_real_mm,n_total,n_validas,n_invalidas,media_mm,mediana_mm,sd_mm,rmse_mm,error_absoluto_medio_mm,error_relativo_pct,intensidad_media
200,198,300,300,0,0,0,0,0,0,0,0
```

## Checklist

- [ ] 20 cm — 3 repeticiones capturadas
- [ ] 50 cm — 3 repeticiones capturadas
- [ ] 100 cm — 3 repeticiones capturadas
- [ ] 150 cm — 3 repeticiones capturadas
- [ ] 200 cm — 3 repeticiones capturadas
- [ ] Verificar cantidad de válidas vs. inválidas por distancia
- [ ] Completar `summary.csv`

## Entregables

```
data/experiments/ld19_micropython/precision/d020cm.csv
data/experiments/ld19_micropython/precision/d050cm.csv
data/experiments/ld19_micropython/precision/d100cm.csv
data/experiments/ld19_micropython/precision/d150cm.csv
data/experiments/ld19_micropython/precision/d200cm.csv
data/experiments/ld19_micropython/precision/summary.csv
```

## Análisis que habilita

- Comparar error medio, RMSE y porcentaje de muestras válidas entre C SDK (1B) y MicroPython (2B)
- Si son iguales → la implementación no introduce error de medición relevante
- Si difieren → pérdida de frames o desincronización en MicroPython afecta la calidad del dato
- Conecta OBJ 2 y OBJ 3 de forma directa
