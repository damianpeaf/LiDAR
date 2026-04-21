# Experimento 1B — Precisión del LD19 con C SDK

**Objetivo:** Medir el error real del LD19 con evidencia propia a 5 distancias conocidas y dejar datos crudos suficientes para comparar luego con TF-Mini S y MicroPython.

**Responde a:** OBJ 2

## Setup

- Sensor: LD19 fijo, apuntando perpendicularmente a una pared blanca plana
- Sin servo activo
- Medir la distancia real con cinta métrica antes de cada captura
- Mínimo 3 repeticiones por distancia
- Sugerencia simple: 3 bloques de 100 lecturas consecutivas por distancia (300 lecturas en total)
- Capturar salida serial con script en PC

## Distancias de referencia

| Distancia nominal | Archivo de salida |
|:-----------------:|-------------------|
| 200 mm (20 cm) | `d020cm.csv` |
| 500 mm (50 cm) | `d050cm.csv` |
| 1000 mm (100 cm) | `d100cm.csv` |
| 1500 mm (150 cm) | `d150cm.csv` |
| 2000 mm (200 cm) | `d200cm.csv` |

## Formato CSV crudo

```
repeticion,distancia_nominal_mm,distancia_real_mm,lectura_sensor_mm,intensidad,valida
1,200,198,198,240,1
1,200,198,201,238,1
...
```

### Resumen mínimo por distancia (`summary.csv`)

```csv
distancia_nominal_mm,distancia_real_mm,n_total,n_validas,n_invalidas,media_mm,mediana_mm,sd_mm,rmse_mm,error_absoluto_medio_mm,error_relativo_pct,intensidad_media
200,198,300,300,0,0,0,0,0,0,0,0
```

> Si una lectura viene corrupta, vacía o fuera del rango esperado, marcar `valida=0` y no borrarla del CSV crudo.

## Checklist

- [ ] Preparar script de captura serial en PC
- [ ] 20 cm — 3 repeticiones capturadas (100 lecturas c/u sugerido)
- [ ] 50 cm — 3 repeticiones capturadas
- [ ] 100 cm — 3 repeticiones capturadas
- [ ] 150 cm — 3 repeticiones capturadas
- [ ] 200 cm — 3 repeticiones capturadas
- [ ] Verificar que cada CSV tiene exactamente 300 filas de datos o justificar faltantes
- [ ] Completar `summary.csv` con métricas por distancia

## Entregables

```
data/experiments/ld19_precision/c/d020cm.csv
data/experiments/ld19_precision/c/d050cm.csv
data/experiments/ld19_precision/c/d100cm.csv
data/experiments/ld19_precision/c/d150cm.csv
data/experiments/ld19_precision/c/d200cm.csv
data/experiments/ld19_precision/c/summary.csv
```

## Análisis que habilita

- **T5:** Error medio, RMSE, SD por distancia para LD19
- **T7:** Base para comparación con TF-Mini S (exp 3B)
- **G4:** Error de medición vs. distancia
- **G5:** Boxplot distribución de lecturas por distancia
- **G6:** Intensidad de señal vs. distancia
