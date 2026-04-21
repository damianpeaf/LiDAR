# Experimento 2C — Escaneo 3D objeto de referencia (MicroPython)

**Objetivo:** Comparar la calidad del modelo 3D producido por MicroPython vs. C SDK sobre el mismo objeto con métricas simples: tiempo, puntos, error dimensional y huecos observados.

**Responde a:** OBJ 3

## Setup

- Dispositivo completo con firmware MicroPython habilitando servo y transmisión
- **Mismo objeto que 1C** (la caja de cartón — no volver a medir dimensiones)
- **Misma posición** que en 1C (misma distancia y orientación)
- Mínimo 3 escaneos completos para comparar consistencia

## Datos a registrar

### Métricas mínimas por escaneo

- duración total del escaneo (s)
- puntos finales exportados
- dimensiones del modelo para largo, ancho y alto
- error absoluto por dimensión respecto a las medidas reales ya tomadas en 1C
- cobertura/huecos observados: `bajo`, `medio` o `alto`

### Resumen sugerido (`caja_micropython_summary.csv`)

```csv
escaneo_id,duracion_s,puntos_finales,largo_modelo_mm,error_largo_mm,ancho_modelo_mm,error_ancho_mm,alto_modelo_mm,error_alto_mm,cobertura_huecos,observaciones
1,0,0,0,0,0,0,0,0,bajo,
```

## Checklist

- [ ] Firmware MicroPython con servo y transmisión activados
- [ ] Objeto en la misma posición que en 1C
- [ ] Ejecutar 3 escaneos completos
- [ ] Exportar cada nube de puntos como JSON
- [ ] Registrar tiempo total, puntos finales, medidas del modelo y huecos observados
- [ ] Tomar capturas desde los mismos 3 ángulos que en 1C (frente, lateral, superior)
- [ ] Completar resumen CSV

## Entregables

```
data/experiments/ld19_scan/caja_micropython_scan1.json
data/experiments/ld19_scan/caja_micropython_scan2.json
data/experiments/ld19_scan/caja_micropython_scan3.json
data/experiments/ld19_scan/caja_micropython_summary.csv
data/experiments/ld19_scan/capturas/caja_py_frente.png
data/experiments/ld19_scan/capturas/caja_py_lateral.png
data/experiments/ld19_scan/capturas/caja_py_superior.png
```

## Análisis que habilita

- **T8:** Comparar puntos totales, error dimensional y huecos entre C SDK y MicroPython
- **G8:** Nube de puntos objeto referencia — MicroPython (3 vistas)
- **G9:** Comparación visual de densidad lado a lado (C SDK vs. MicroPython)
- Cierra el argumento del OBJ 3: MicroPython no solo es más lento, produce modelos de menor calidad
