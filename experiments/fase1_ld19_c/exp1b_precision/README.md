# Experimento 1B — Precisión del LD19 con C SDK

**Objetivo:** Medir el error real del LD19 con evidencia propia a 5 distancias conocidas. No citar únicamente el datasheet.

**Responde a:** OBJ 2

## Setup

- Sensor: LD19 fijo, apuntando perpendicularmente a una pared blanca plana
- Sin servo activo
- Medir la distancia real con cinta métrica antes de cada captura
- 300 lecturas consecutivas por distancia
- Capturar salida serial con script en PC

## Distancias de referencia

| Distancia nominal | Archivo de salida |
|:-----------------:|-------------------|
| 200 mm (20 cm) | `d020cm.csv` |
| 500 mm (50 cm) | `d050cm.csv` |
| 1000 mm (100 cm) | `d100cm.csv` |
| 1500 mm (150 cm) | `d150cm.csv` |
| 2000 mm (200 cm) | `d200cm.csv` |

## Formato CSV

```
distancia_nominal_mm,lectura_sensor_mm,intensidad
200,198,240
200,201,238
...
```

## Checklist

- [ ] Preparar script de captura serial en PC
- [ ] 20 cm — 300 lecturas capturadas
- [ ] 50 cm — 300 lecturas capturadas
- [ ] 100 cm — 300 lecturas capturadas
- [ ] 150 cm — 300 lecturas capturadas
- [ ] 200 cm — 300 lecturas capturadas
- [ ] Verificar que cada CSV tiene exactamente 300 filas de datos

## Entregables

```
data/experiments/ld19_precision/c/d020cm.csv
data/experiments/ld19_precision/c/d050cm.csv
data/experiments/ld19_precision/c/d100cm.csv
data/experiments/ld19_precision/c/d150cm.csv
data/experiments/ld19_precision/c/d200cm.csv
```

## Análisis que habilita

- **T5:** Error medio, RMSE, SD por distancia para LD19
- **T7:** Base para comparación con TF-Mini S (exp 3B)
- **G4:** Error de medición vs. distancia
- **G5:** Boxplot distribución de lecturas por distancia
- **G6:** Intensidad de señal vs. distancia
