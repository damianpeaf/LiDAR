# Experimento 4C — Registro multi-posición arqueológico

**Objetivo:** Documentar un área más grande combinando 2–3 escaneos desde posiciones distintas. Demuestra que el sistema escala más allá de un solo punto de captura.

**Responde a:** OBJ 4

## Setup

- 2 o 3 posiciones del dispositivo en el mismo espacio arqueológico
- Escaneo completo desde cada posición
- Identificar un **elemento de referencia común** visible desde todas las posiciones (piedra prominente, esquina de muro, marca en el suelo)
- Medir la distancia entre posiciones del dispositivo con cinta

## Procedimiento en campo

1. Identificar y fotografiar el elemento de referencia común
2. Posición 1: escaneo completo → exportar JSON → fotografiar setup
3. Mover dispositivo a posición 2 (anotar distancia desde pos. 1)
4. Posición 2: escaneo completo → exportar JSON → fotografiar setup
5. (Opcional) Posición 3: repetir
6. En el visualizador: alinear nubes usando el elemento de referencia común
7. Captura del modelo combinado

## Checklist

- [ ] Elemento de referencia común identificado y fotografiado
- [ ] Posición 1 — escaneo completado y exportado
- [ ] Posición 2 — escaneo completado y exportado
- [ ] Posición 3 — escaneo completado y exportado (si aplica)
- [ ] Distancias entre posiciones medidas y anotadas
- [ ] Nubes alineadas manualmente en el visualizador
- [ ] Captura del modelo combinado tomada

## Entregables

```
data/experiments/arqueologia/multipos_01.json
data/experiments/arqueologia/multipos_02.json
data/experiments/arqueologia/multipos_03.json          ← si hay 3 posiciones
data/experiments/arqueologia/multipos_setup.jpg
data/experiments/arqueologia/multipos_notas.txt        ← posiciones, distancias, referencia
data/experiments/arqueologia/capturas/multipos_combinado.png
```

## Análisis que habilita

- **G11:** Nube de puntos del registro multi-posición combinado
- Cálculo del área total documentada vs. área por escaneo individual
- Discusión sobre limitaciones para espacios grandes (tiempo de escaneo, alcance)
- **T10:** Incluir número de posiciones, área total estimada, tiempo total
