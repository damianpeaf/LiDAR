# Experimento 4C — Registro multi-posición arqueológico

**Objetivo:** Documentar un área más grande combinando 2–3 escaneos desde posiciones distintas y dejar evidencia suficiente para evaluar cobertura, tiempo adicional y calidad del registro.

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

## Datos a registrar

- número de posiciones usadas
- tiempo de captura por posición (s)
- tiempo total incluyendo alineación (s)
- puntos exportados por posición
- puntos del modelo combinado final
- resultado del registro: `exitoso`, `parcial`, `fallido`
- cobertura final observada: `baja`, `media`, `alta`

### Resumen sugerido (`multipos_summary.csv`)

```csv
sesion_id,n_posiciones,tiempo_pos1_s,tiempo_pos2_s,tiempo_pos3_s,tiempo_total_s,puntos_pos1,puntos_pos2,puntos_pos3,puntos_combinado,registro_resultado,cobertura_final,observaciones
1,2,0,0,,0,0,0,,0,exitoso,media,
```

## Checklist

- [ ] Elemento de referencia común identificado y fotografiado
- [ ] Posición 1 — escaneo completado y exportado
- [ ] Posición 2 — escaneo completado y exportado
- [ ] Posición 3 — escaneo completado y exportado (si aplica)
- [ ] Distancias entre posiciones medidas y anotadas
- [ ] Nubes alineadas manualmente en el visualizador
- [ ] Captura del modelo combinado tomada
- [ ] Registrar tiempos, puntos y resultado del registro en el resumen CSV

## Entregables

```
data/experiments/arqueologia/multipos_01.json
data/experiments/arqueologia/multipos_02.json
data/experiments/arqueologia/multipos_03.json          ← si hay 3 posiciones
data/experiments/arqueologia/multipos_setup.jpg
data/experiments/arqueologia/multipos_notas.txt        ← posiciones, distancias, referencia
data/experiments/arqueologia/capturas/multipos_combinado.png
data/experiments/arqueologia/multipos_summary.csv
```

## Análisis que habilita

- **G11:** Nube de puntos del registro multi-posición combinado
- Cálculo del área total documentada vs. área por escaneo individual
- Discusión sobre limitaciones para espacios grandes (tiempo de escaneo, alcance)
- **T10:** Incluir número de posiciones, área total estimada, tiempo total, puntos combinados y cobertura final
