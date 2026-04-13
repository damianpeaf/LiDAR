# Experimento 4A — Escaneo arqueológico (posición única)

**Objetivo:** Producir el primer modelo 3D de un espacio arqueológico real con el sistema desarrollado.

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

## Checklist

- [ ] Dimensiones del espacio medidas y anotadas antes del escaneo
- [ ] Escaneo completado sin interrupciones
- [ ] Nube de puntos exportada como JSON
- [ ] Número de puntos y tiempo de escaneo registrados
- [ ] Fotografías del setup tomadas
- [ ] Capturas del visualizador (al menos 3 ángulos)

## Entregables

```
data/experiments/arqueologia/espacio_01.json
data/experiments/arqueologia/espacio_01_medidas.txt
data/experiments/arqueologia/fotos/setup_01.jpg
data/experiments/arqueologia/capturas/espacio_01_frente.png
data/experiments/arqueologia/capturas/espacio_01_lateral.png
data/experiments/arqueologia/capturas/espacio_01_superior.png
```

## Análisis que habilita

- **T10:** Puntos capturados, tiempo de escaneo, descripción del espacio
- **G10:** Nube de puntos del espacio arqueológico desde múltiples ángulos
