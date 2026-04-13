# Experimento 2C — Escaneo 3D objeto de referencia (MicroPython)

**Objetivo:** Comparar la calidad del modelo 3D producido por MicroPython vs. C SDK sobre el mismo objeto. ¿Produce la misma geometría? ¿Con menor densidad de puntos o más gaps?

**Responde a:** OBJ 3

## Setup

- Dispositivo completo con firmware MicroPython habilitando servo y transmisión
- **Mismo objeto que 1C** (la caja de cartón — no volver a medir dimensiones)
- **Misma posición** que en 1C (misma distancia y orientación)

## Checklist

- [ ] Firmware MicroPython con servo y transmisión activados
- [ ] Objeto en la misma posición que en 1C
- [ ] Escaneo completo ejecutado
- [ ] Nube de puntos exportada como JSON
- [ ] Registrar tiempo total y número de puntos
- [ ] Tomar capturas desde los mismos 3 ángulos que en 1C (frente, lateral, superior)

## Entregables

```
data/experiments/ld19_scan/caja_micropython.json
data/experiments/ld19_scan/capturas/caja_py_frente.png
data/experiments/ld19_scan/capturas/caja_py_lateral.png
data/experiments/ld19_scan/capturas/caja_py_superior.png
```

## Análisis que habilita

- **T8:** Comparar puntos totales, cobertura angular, gaps entre C SDK y MicroPython
- **G8:** Nube de puntos objeto referencia — MicroPython (3 vistas)
- **G9:** Comparación visual de densidad lado a lado (C SDK vs. MicroPython)
- Cierra el argumento del OBJ 3: MicroPython no solo es más lento, produce modelos de menor calidad
