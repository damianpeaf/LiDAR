# Experimento 4B — Validación dimensional del modelo arqueológico

**Objetivo:** Demostrar que el modelo 3D capturado es geométricamente coherente con el espacio real, comparando dimensiones medidas en campo con las extraídas del modelo.

**Responde a:** OBJ 4

## Metodología

1. Usar las medidas tomadas en campo durante el experimento 4A
2. En el visualizador, identificar las mismas dimensiones en la nube de puntos
3. Comparar: real vs. modelo → error absoluto → error porcentual
4. Criterio de éxito: error del mismo orden que la precisión nominal del sensor y sin desvíos groseros en dimensiones clave

## Datos mínimos a registrar

- mínimo 3 dimensiones comparables entre realidad y modelo si el espacio lo permite
- medida real (mm)
- medida en modelo (mm)
- error absoluto (mm)
- error relativo (%)
- nota breve sobre qué tan clara fue esa medida en la nube (`clara`, `regular`, `difusa`)

## Checklist

- [ ] Al menos 3 dimensiones identificadas en el modelo 3D si el espacio lo permite
- [ ] Tabla de comparación completada
- [ ] Capturas del visualizador mostrando dónde se midió cada dimensión

## Entregables

Tabla (incluir directamente en el capítulo):

| Dimensión | Medida real (mm) | En modelo (mm) | Error absoluto (mm) | Error % | Claridad |
|-----------|:----------------:|:--------------:|:-------------------:|:-------:|:--------:|
| [e.g. Ancho corredor] | | | | | |
| [e.g. Altura bóveda] | | | | | |

Resumen sugerido (`espacio_01_validacion.csv`):

```csv
dimension,medida_real_mm,medida_modelo_mm,error_absoluto_mm,error_relativo_pct,claridad,observaciones
ancho_corredor,0,0,0,0,clara,
```

```
data/experiments/arqueologia/capturas/espacio_01_validacion_dim1.png
data/experiments/arqueologia/capturas/espacio_01_validacion_dim2.png
data/experiments/arqueologia/espacio_01_validacion.csv
```

## Análisis que habilita

- **T9:** Validación dimensional — base cuantitativa para el OBJ 4 con error medio y error máximo
