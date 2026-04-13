# Experimento 3B — Precisión del TF-Mini S a distancias conocidas

**Objetivo:** Medir el error real del TF-Mini S a las mismas 5 distancias del experimento 1B para comparación directa entre sensores.

**Responde a:** OBJ 2

## Setup

Idéntico al experimento 1B — solo cambia el sensor:

- TF-Mini S fijo, apuntando perpendicularmente a la misma pared blanca
- Mismas 5 distancias: 20, 50, 100, 150, 200 cm
- 300 lecturas por distancia

## Formato CSV

```
distancia_nominal_mm,lectura_sensor_mm,strength
```

> Nota: el campo se llama `strength` (no `intensidad`) porque el TF-Mini S reporta un valor de 16 bits (0–65,535), a diferencia del LD19 que usa 8 bits.

## Checklist

- [ ] 20 cm — 300 lecturas capturadas
- [ ] 50 cm — 300 lecturas capturadas
- [ ] 100 cm — 300 lecturas capturadas
- [ ] 150 cm — 300 lecturas capturadas
- [ ] 200 cm — 300 lecturas capturadas

## Entregables

```
data/experiments/tf_poc/precision/d020cm.csv
data/experiments/tf_poc/precision/d050cm.csv
data/experiments/tf_poc/precision/d100cm.csv
data/experiments/tf_poc/precision/d150cm.csv
data/experiments/tf_poc/precision/d200cm.csv
```

## Análisis que habilita

- **T6:** Precisión TF-Mini S — error medio, RMSE, SD por distancia
- **T7:** Comparativa de precisión LD19 vs. TF-Mini S (este es el corazón del OBJ 2)
- **G4:** Error de medición vs. distancia — ambos sensores en la misma figura
- **G5:** Boxplot distribución de lecturas por distancia — ambos sensores
- **G6:** Intensidad/strength vs. distancia — ambos sensores
