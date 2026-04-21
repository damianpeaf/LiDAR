# Experimento 4A — Escaneo arqueológico (posición única)

**Objetivo:** Producir el primer modelo 3D de un espacio arqueológico real con el sistema desarrollado y registrar evidencia suficiente para juzgar utilidad práctica del resultado.

**Responde a:** OBJ 4

## Setup

- Dispositivo completo en el interior o frente a una superficie arqueológica
- Una posición fija, escaneo completo hasta que el servo finalice
- Medir con cinta al menos 2 dimensiones del espacio antes de escanear

## Datos a registrar en campo

- [ ] Espacio escaneado (descripción breve: "corredor norte", "nicho lado este", etc.)
- [ ] Dimensiones medidas con cinta (anotar cuáles y sus valores)
- [ ] Hora de inicio y fin del escaneo
- [ ] Condiciones de iluminación
- [ ] Fotografías del dispositivo in situ y del espacio

### Resumen sugerido (`espacio_01_summary.csv`)

```csv
scan_id,espacio,duracion_s,puntos_finales,n_dimensiones_medidas,error_dimensional_medio_mm,error_dimensional_max_mm,huecos_observados,incidencias
1,,0,0,0,0,0,bajo,
```

> `error_dimensional_*` se completa después en 4B, pero conviene dejar el mismo archivo como resumen de la sesión.

## Checklist

- [ ] Dimensiones del espacio medidas y anotadas antes del escaneo
- [ ] Escaneo completado sin interrupciones
- [ ] Nube de puntos exportada como JSON
- [ ] Número de puntos y tiempo de escaneo registrados
- [ ] Fotografías del setup tomadas
- [ ] Capturas del visualizador (al menos 3 ángulos)
- [ ] Registrar huecos observados (`bajo`, `medio`, `alto`) e incidencias simples

## Entregables

```
data/experiments/arqueologia/espacio_01.json
data/experiments/arqueologia/espacio_01_medidas.txt
data/experiments/arqueologia/espacio_01_summary.csv
data/experiments/arqueologia/fotos/setup_01.jpg
data/experiments/arqueologia/capturas/espacio_01_frente.png
data/experiments/arqueologia/capturas/espacio_01_lateral.png
data/experiments/arqueologia/capturas/espacio_01_superior.png
```

## Análisis que habilita

- **T10:** Puntos capturados, tiempo de escaneo, cobertura observada y descripción del espacio
- **G10:** Nube de puntos del espacio arqueológico desde múltiples ángulos
