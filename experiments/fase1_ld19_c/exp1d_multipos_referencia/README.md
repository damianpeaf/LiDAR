# Experimento 1D — Registro multi-posición (referencia)

**Objetivo:** Ensayar la metodología de registro multi-posición que se usará en Huehuetenango, usando el mismo objeto de referencia del experimento 1C. Este experimento valida el procedimiento antes de estar en campo.

**Responde a:** OBJ 1

## Setup

- Dispositivo completo: LD19 + servo + Pico W + firmware picoscan
- Mismo objeto o espacio del experimento 1C
- 2 posiciones del dispositivo, separadas ~30–50 cm lateralmente
- Identificar un **punto de referencia común** visible desde ambas posiciones (esquina del objeto, marca en el suelo)
- Medir la distancia entre las dos posiciones del dispositivo con cinta

## Procedimiento

1. Posición 1: escaneo completo → exportar JSON → anotar posición
2. Mover dispositivo ~40 cm lateralmente
3. Posición 2: escaneo completo → exportar JSON → anotar posición
4. Fotografiar el setup mostrando ambas posiciones

## Checklist

- [ ] Identificar y marcar el punto de referencia común antes de escanear
- [ ] Escaneo posición 1 completado y exportado
- [ ] Escaneo posición 2 completado y exportado
- [ ] Medir y anotar distancia entre posiciones
- [ ] Fotografiar setup con ambas posiciones visibles
- [ ] Alinear manualmente las dos nubes en el visualizador usando el punto de referencia
- [ ] Captura del modelo combinado

## Entregables

```
data/experiments/ld19_scan/multipos_ref_pos1.json
data/experiments/ld19_scan/multipos_ref_pos2.json
data/experiments/ld19_scan/multipos_ref_combinado.png   ← captura del visualizador
data/experiments/ld19_scan/multipos_ref_setup.jpg
data/experiments/ld19_scan/multipos_ref_notas.txt       ← posiciones, distancia entre ellas, punto de referencia
```

## Análisis que habilita

- Documenta el procedimiento de registro multi-posición
- Sirve como base metodológica para la sección de aplicación arqueológica
- Identifica problemas prácticos antes de estar en campo
