# Experimento 1C — Escaneo 3D objeto de referencia (C SDK)

**Objetivo:** Validar la calidad geométrica del modelo 3D generado por el sistema completo LD19 + servo + C SDK con métricas simples y defendibles antes del escaneo arqueológico.

**Responde a:** OBJ 1, OBJ 2

## Setup

- Dispositivo completo: LD19 + servo + Pico W + firmware picoscan
- Objeto de referencia: caja de cartón de dimensiones conocidas
- Medir con cinta métrica ANTES del escaneo: largo, ancho, alto
- Distancia al objeto: ~40 cm, centrada en el campo de visión
- Escaneo completo hasta que el servo finalice su recorrido
- Mínimo 3 escaneos completos del mismo objeto para verificar consistencia

## Datos a registrar

### Métricas mínimas por escaneo

- duración total del escaneo (s)
- puntos finales exportados en la nube
- dimensiones reales del objeto (largo, ancho, alto)
- dimensiones estimadas en el modelo para esas mismas 3 medidas
- error absoluto por dimensión (mm)
- observación simple de cobertura/huecos: `bajo`, `medio` o `alto`

### Archivo de resumen sugerido (`caja_referencia_c_summary.csv`)

```csv
escaneo_id,duracion_s,puntos_finales,largo_real_mm,largo_modelo_mm,error_largo_mm,ancho_real_mm,ancho_modelo_mm,error_ancho_mm,alto_real_mm,alto_modelo_mm,error_alto_mm,cobertura_huecos,observaciones
1,0,0,0,0,0,0,0,0,0,0,0,bajo,
```

> Si no podés medir una densidad formal, con `puntos_finales` + `cobertura_huecos` alcanza para una comparación útil.

## Checklist

- [ ] Medir y anotar dimensiones físicas de la caja (largo, ancho, alto)
- [ ] Verificar que firmware picoscan está cargado y conectividad OK
- [ ] Ejecutar 3 escaneos completos
- [ ] Exportar cada nube de puntos como JSON
- [ ] Registrar tiempo total, puntos finales y medidas del modelo para cada escaneo
- [ ] Tomar capturas del visualizador (frente, lateral, superior)
- [ ] Completar resumen CSV

## Entregables

```
data/experiments/ld19_scan/caja_referencia_c_scan1.json
data/experiments/ld19_scan/caja_referencia_c_scan2.json
data/experiments/ld19_scan/caja_referencia_c_scan3.json
data/experiments/ld19_scan/caja_referencia_medidas.txt   ← dimensiones físicas reales
data/experiments/ld19_scan/caja_referencia_c_summary.csv
data/experiments/ld19_scan/capturas/caja_c_frente.png
data/experiments/ld19_scan/capturas/caja_c_lateral.png
data/experiments/ld19_scan/capturas/caja_c_superior.png
```

## Análisis que habilita

- **T9:** Dimensiones reales vs. modelo vs. error absoluto vs. error %
- **T8:** Calidad de nube — número de puntos y cobertura/huecos observados
- **G7:** Nube de puntos objeto referencia — C SDK (3 vistas)
- **G9:** Comparación visual con resultado de MicroPython (exp 2C)
