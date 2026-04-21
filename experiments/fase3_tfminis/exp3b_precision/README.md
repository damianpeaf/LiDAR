# Experimento 3B — Precisión del TF-Mini S a distancias conocidas

**Objetivo:** Medir el error real del TF-Mini S a las mismas 5 distancias del experimento 1B para comparación directa entre sensores con datos crudos y resumen estadístico simple.

**Responde a:** OBJ 2

## Setup

Idéntico al experimento 1B — solo cambia el sensor:

- TF-Mini S fijo, apuntando perpendicularmente a la misma pared blanca
- Mismas 5 distancias: 20, 50, 100, 150, 200 cm
- Mínimo 3 repeticiones por distancia
- Sugerencia simple: 3 bloques de 100 lecturas por distancia

## Formato CSV crudo

```
repeticion,distancia_nominal_mm,distancia_real_mm,lectura_sensor_mm,strength,valida
```

> Nota: el campo se llama `strength` (no `intensidad`) porque el TF-Mini S reporta un valor de 16 bits (0–65,535), a diferencia del LD19 que usa 8 bits.

### Resumen mínimo por distancia (`summary.csv`)

```csv
distancia_nominal_mm,distancia_real_mm,n_total,n_validas,n_invalidas,media_mm,mediana_mm,sd_mm,rmse_mm,error_absoluto_medio_mm,error_relativo_pct,strength_media
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
data/experiments/tf_poc/precision/d020cm.csv
data/experiments/tf_poc/precision/d050cm.csv
data/experiments/tf_poc/precision/d100cm.csv
data/experiments/tf_poc/precision/d150cm.csv
data/experiments/tf_poc/precision/d200cm.csv
data/experiments/tf_poc/precision/summary.csv
```

## Análisis que habilita

- **T6:** Precisión TF-Mini S — error medio, RMSE, SD por distancia
- **T7:** Comparativa de precisión LD19 vs. TF-Mini S (este es el corazón del OBJ 2), incluyendo porcentaje de lecturas válidas
- **G4:** Error de medición vs. distancia — ambos sensores en la misma figura
- **G5:** Boxplot distribución de lecturas por distancia — ambos sensores
- **G6:** Intensidad/strength vs. distancia — ambos sensores
