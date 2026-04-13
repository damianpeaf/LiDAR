# Experimento 1C — Escaneo 3D objeto de referencia (C SDK)

**Objetivo:** Validar la calidad geométrica del modelo 3D generado por el sistema completo LD19 + servo + C SDK. Prueba de concepto del pipeline antes del escaneo arqueológico.

**Responde a:** OBJ 1, OBJ 2

## Setup

- Dispositivo completo: LD19 + servo + Pico W + firmware picoscan
- Objeto de referencia: caja de cartón de dimensiones conocidas
- Medir con cinta métrica ANTES del escaneo: largo, ancho, alto
- Distancia al objeto: ~40 cm, centrada en el campo de visión
- Escaneo completo hasta que el servo finalice su recorrido

## Datos a registrar

- Dimensiones físicas del objeto (anotar antes del escaneo)
- Nube de puntos exportada desde el visualizador (JSON)
- Tiempo total de escaneo (cronómetro)
- Número de puntos en la nube

## Checklist

- [ ] Medir y anotar dimensiones físicas de la caja (largo, ancho, alto)
- [ ] Verificar que firmware picoscan está cargado y conectividad OK
- [ ] Ejecutar escaneo completo
- [ ] Exportar nube de puntos como JSON
- [ ] Registrar tiempo total y número de puntos
- [ ] Tomar capturas del visualizador (frente, lateral, superior)

## Entregables

```
data/experiments/ld19_scan/caja_referencia_c.json
data/experiments/ld19_scan/caja_referencia_medidas.txt   ← dimensiones físicas reales
data/experiments/ld19_scan/capturas/caja_c_frente.png
data/experiments/ld19_scan/capturas/caja_c_lateral.png
data/experiments/ld19_scan/capturas/caja_c_superior.png
```

## Análisis que habilita

- **T9:** Dimensiones reales vs. modelo vs. error absoluto vs. error %
- **T8:** Densidad de nube — número de puntos, cobertura angular
- **G7:** Nube de puntos objeto referencia — C SDK (3 vistas)
- **G9:** Comparación visual con resultado de MicroPython (exp 2C)
