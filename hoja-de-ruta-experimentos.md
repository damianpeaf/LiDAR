# Hoja de Ruta: Experimentos de Tesis LiDAR

> **Este documento es el resumen ejecutivo.** La documentación detallada de cada experimento, con checklists, entregables y análisis vive en `experiments/README.md` y sus subcarpetas.

## Contexto y decisiones de diseño

**Lo que tienes:** Dispositivo LD19 + servos + Pico W con firmware C SDK funcional.
**Lo que puedes hacer:** LD19 con C, LD19 con MicroPython (sin desarmar), TF-Mini S estático directo a Pico (sin mecanismo de barrido).
**Lo que NO vas a reconstruir:** El mecanismo completo de barrido con TF-Mini S. No es necesario.

**Argumento central de la tesis:**
> Se construyó un sistema de escaneo LiDAR 3D de bajo costo basado en Raspberry Pi Pico W. Se evaluaron dos sensores (multipunto LD19 vs. punto único TF-Mini S) y dos implementaciones de firmware (C SDK vs. MicroPython) bajo condiciones controladas. El sistema se aplicó a la documentación de patrimonio arqueológico en Huehuetenango.

---

## Objetivos y cómo se responden

| Objetivo | Cómo se responde | Experimentos |
|----------|-----------------|--------------|
| OBJ 1: Flujo de trabajo captura → modelo 3D | Pipeline completo documentado. Datos existentes reutilizables. | 1C, 1D, 4A |
| OBJ 2: Comparar sensores (multipunto vs. punto único) | Precisión medida con ground truth a 5 distancias. Densidad y cobertura de nubes 3D. | 1B, 1C, 3A, 3B |
| OBJ 3: Comparar MicroPython vs. C SDK | Benchmark idéntico: mismo sensor, mismas condiciones, misma duración. | 1A, 2A, 2B, 2C |
| OBJ 4: Aplicación arqueológica real | Escaneo en pirámides de Huehuetenango. Registro multi-posición. | 4A, 4B, 4C |

---

## FASE 1 — LD19 con C SDK (dispositivo actual, no desarmar)

**Prerrequisito:** El dispositivo ya funciona. Firmware de benchmark en `experiments/ld19c/`. No se usa picoscan aún.

---

### Experimento 1A — Benchmark de rendimiento C SDK

**Objetivo:** Caracterizar la capacidad de procesamiento del C SDK con el LD19 de forma reproducible.

**Setup:**
- LD19 conectado a Pico W, sin servo activo
- Sensor apuntando a pared plana a ~50 cm, ángulo perpendicular
- Firmware de benchmark corriendo exactamente 60 segundos
- 3 repeticiones independientes (reiniciar firmware entre cada una)

**Datos a capturar por repetición** (el firmware ya los genera, solo asegurarte de registrar todos):
- Frames recibidos / procesados / con error CRC / con error de header
- Bytes recibidos / procesados
- Puntos procesados
- Puntos/s, Frames/s, Bytes/s
- Tiempo promedio / mín / máx por frame (µs)
- Tiempo promedio de CRC por frame (µs)
- Tiempo promedio de parsing por frame (µs)
- % CPU en UART / CRC / parsing

**Entregables:**
```
data/experiments/ld19c/bench_c_rep1.txt
data/experiments/ld19c/bench_c_rep2.txt
data/experiments/ld19c/bench_c_rep3.txt
```

**Análisis que habilita:**
- Media ± desviación estándar de cada métrica entre las 3 repeticiones
- Confirma reproducibilidad del dato existente (ya tienes uno de 30 s, este lo reemplaza con mayor rigor)

---

### Experimento 1B — Precisión del LD19 a distancias conocidas (con C SDK)

**Objetivo:** Medir el error real del LD19, con evidencia propia, no solo citar el datasheet.

**Setup:**
- LD19 fijo, apuntando perpendicularmente a una pared blanca plana
- Mover el sensor (o la pared) a cada distancia y verificar con cinta métrica
- 300 lecturas consecutivas por distancia (el firmware las imprime por serial, capturar con script)
- Distancias: **20, 50, 100, 150, 200 cm**

**Datos a capturar** (un CSV por distancia):
```
distancia_nominal_mm, lectura_sensor_mm, intensidad
```

**Entregables:**
```
data/experiments/ld19_precision/c/d020cm.csv
data/experiments/ld19_precision/c/d050cm.csv
data/experiments/ld19_precision/c/d100cm.csv
data/experiments/ld19_precision/c/d150cm.csv
data/experiments/ld19_precision/c/d200cm.csv
```

**Análisis que habilita:**
- Error medio por distancia (sesgo sistemático)
- RMSE por distancia
- Desviación estándar por distancia (repetibilidad)
- Boxplot: distribución de lecturas por distancia
- Línea: error vs. distancia (¿el error crece con la distancia?)
- Línea: intensidad vs. distancia (¿cae la señal con la distancia?)

---

### Experimento 1C — Escaneo 3D de objeto de referencia con LD19 + C SDK

**Objetivo:** Validar la calidad geométrica del modelo 3D generado por el sistema completo. Es la prueba de concepto del pipeline antes del escaneo arqueológico.

**Setup:**
- Dispositivo completo (LD19 + servo + Pico W + firmware picoscan)
- Objeto de referencia: **caja de cartón** de dimensiones conocidas, medida con cinta antes del escaneo
  - Medir: largo, ancho, alto (3 dimensiones)
  - Colocar a ~40 cm del sensor, centrada en el campo de visión
- Escaneo completo hasta que el servo finalice su recorrido

**Datos a capturar:**
- Dimensiones físicas del objeto (cinta métrica, antes del escaneo)
- Nube de puntos completa exportada desde el visualizador
- Tiempo total de escaneo (cronómetro)
- Número de puntos en la nube

**Entregables:**
```
data/experiments/ld19_scan/caja_referencia.json          ← nube de puntos
data/experiments/ld19_scan/caja_referencia_medidas.txt   ← dimensiones físicas reales
```

**Análisis que habilita:**
- Extraer dimensiones del modelo 3D (largo, ancho, alto visibles en la nube)
- Tabla: dimensión real vs. dimensión en modelo vs. error absoluto vs. error %
- Capturas del visualizador desde 3 ángulos (frente, lateral, superior)
- Esto es la validación directa del sistema para OBJ 1 y OBJ 2

---

### Experimento 1D — Registro multi-posición con objeto de referencia

**Objetivo:** Demostrar que el sistema puede documentar un espacio más grande combinando múltiples escaneos desde posiciones distintas. Es el ensayo previo a la aplicación arqueológica.

**Setup:**
- Mismo objeto o espacio del experimento 1C
- 2 posiciones del dispositivo separadas ~30–50 cm lateralmente
- Escaneo completo desde cada posición
- Identificar un **punto de referencia común** visible en ambas nubes (esquina del objeto, marca en el suelo)

**Datos a capturar:**
- 2 nubes de puntos (JSON), una por posición
- Fotografía del setup mostrando ambas posiciones del dispositivo
- Posición relativa aproximada entre escaneos (medir con cinta)

**Entregables:**
```
data/experiments/ld19_scan/multipos_pos1.json
data/experiments/ld19_scan/multipos_pos2.json
data/experiments/ld19_scan/multipos_setup.jpg
```

**Análisis que habilita:**
- Alineación manual de las dos nubes en el visualizador usando el punto de referencia común
- Captura del resultado combinado
- Demuestra la metodología de registro multi-posición que se usará en Huehuetenango
- Documenta la zona de solapamiento y cómo se integran los datos

---

## FASE 2 — LD19 con MicroPython (mismo dispositivo, cambiar firmware)

**Prerrequisito:** Adaptar el script existente (`experiments/lidar/device/init.py`) para que:
1. No transmita por red durante el benchmark (desactivar WiFi/HTTP)
2. Imprima por serial las mismas métricas que genera el firmware C SDK
3. Mida tiempos con `time.ticks_us()` para CRC y parsing

**Regla de oro:** Condiciones idénticas a Fase 1. Mismo sensor, misma pared, misma distancia, mismo tiempo (60 s).

---

### Experimento 2A — Benchmark de rendimiento MicroPython

**Mismo protocolo exacto que 1A.** Solo cambia el firmware.

**Setup:** Flashear MicroPython en la Pico, correr script de benchmark 60 segundos. 3 repeticiones.

**Datos a capturar:** Idénticos a 1A.

**Entregables:**
```
data/experiments/ld19_micropython/bench_py_rep1.txt
data/experiments/ld19_micropython/bench_py_rep2.txt
data/experiments/ld19_micropython/bench_py_rep3.txt
```

**Análisis que habilita:**
- Tabla comparativa directa C SDK vs. MicroPython para cada métrica
- Ratios de diferencia (factor ×N)
- Barras comparativas: frames/s, puntos/s, % error CRC
- Barras comparativas: tiempo CRC, tiempo parsing (escala logarítmica para que se vea la diferencia)

---

### Experimento 2B — Precisión del LD19 con MicroPython

**Mismo protocolo exacto que 1B.** Solo cambia el firmware. Mismas 5 distancias, misma pared.

**Hipótesis a verificar:** La implementación no debería afectar la precisión del sensor. Si los errores difieren entre C y MicroPython, indica pérdida de datos por desincronización UART.

**Entregables:**
```
data/experiments/ld19_micropython/precision/d020cm.csv
data/experiments/ld19_micropython/precision/d050cm.csv
data/experiments/ld19_micropython/precision/d100cm.csv
data/experiments/ld19_micropython/precision/d150cm.csv
data/experiments/ld19_micropython/precision/d200cm.csv
```

**Análisis que habilita:**
- Comparar error medio y RMSE entre C SDK y MicroPython por distancia
- Si son iguales: la implementación no introduce error en la medición
- Si difieren: la pérdida de frames en MicroPython afecta incluso la precisión reportada
- Esto conecta OBJ 2 y OBJ 3 de forma elegante

---

### Experimento 2C — Escaneo 3D de objeto de referencia con MicroPython

**Mismo objeto que 1C** (la caja de cartón con dimensiones ya medidas, no volver a medir).

**Objetivo:** Comparar la calidad del modelo 3D generado por MicroPython vs. C SDK sobre el mismo objeto. ¿Produce la misma geometría? ¿Con menor densidad de puntos?

**Setup:** Dispositivo completo con firmware MicroPython que soporte servo + transmisión. Posición idéntica a 1C.

**Datos a capturar:**
- Nube de puntos completa exportada
- Tiempo total de escaneo
- Número de puntos

**Entregables:**
```
data/experiments/ld19_scan/caja_micropython.json
```

**Análisis que habilita:**
- Comparación directa de nubes: densidad de puntos, cobertura angular, zonas con gaps
- Tabla: C SDK vs. MicroPython — puntos totales, tiempo escaneo, dimensiones reconstruidas vs. reales
- Capturas del visualizador para ambas nubes desde el mismo ángulo (comparación visual)
- Cierra el argumento del OBJ 3: no solo MicroPython es más lento en firmware, también produce modelos de menor calidad

---

## FASE 3 — TF-Mini S directo a Pico (sin servo)

**Prerrequisito:** Desarmar la Pico del dispositivo LD19. Conectar TF-Mini S directamente (UART a 115200 baud). Usar y adaptar `experiments/tf_poc/tf_poc.c`.

**Por qué sin servo es suficiente y metodológicamente correcto:**
> "Para aislar las características intrínsecas de cada sensor de las variables del sistema mecánico, la comparación de precisión se realizó en condición estática controlada. La diferencia en capacidad de cobertura 3D se establece a partir de las características operacionales de cada sensor: el LD19 cubre 360° por rotación propia; el TF-Mini S requiere posicionamiento mecánico externo para cada punto de medición."

---

### Experimento 3A — Benchmark de rendimiento del TF-Mini S

**Objetivo:** Caracterizar throughput, latencia y tasa de errores del TF-Mini S. Adaptar el firmware de `tf_poc.c` para que genere un reporte en el mismo formato que los del LD19.

**Métricas adicionales** respecto al LD19 (porque el TF-Mini S es más simple):
- Frames recibidos / válidos / con checksum inválido
- Lecturas/s efectivas
- Tiempo promedio / mín / máx por lectura (µs)
- Bytes/s

**Condiciones:** 60 segundos, 3 repeticiones, sensor a ~50 cm de pared plana.

**Entregables:**
```
experiments/tf_poc/bench_tf.c                      ← script adaptado (nuevo)
data/experiments/tf_poc/bench_tf_rep1.txt
data/experiments/tf_poc/bench_tf_rep2.txt
data/experiments/tf_poc/bench_tf_rep3.txt
```

**Análisis que habilita:**
- Tabla comparativa de throughput: TF-Mini S vs. LD19 (ambos con C SDK)
- Compara: lecturas/s, bytes/s, tasa de error
- Esto es parte central del OBJ 2

---

### Experimento 3B — Precisión del TF-Mini S a distancias conocidas

**Mismo protocolo que 1B.** Mismas 5 distancias (20, 50, 100, 150, 200 cm), misma pared, 300 lecturas por distancia.

**Datos a capturar:**
```
distancia_nominal_mm, lectura_sensor_mm, strength
```

**Entregables:**
```
data/experiments/tf_poc/precision/d020cm.csv
data/experiments/tf_poc/precision/d050cm.csv
data/experiments/tf_poc/precision/d100cm.csv
data/experiments/tf_poc/precision/d150cm.csv
data/experiments/tf_poc/precision/d200cm.csv
```

**Análisis que habilita** (corazón del OBJ 2):
- Error medio, RMSE, desviación estándar: TF-Mini S vs. LD19 por distancia
- Boxplot comparativo: distribución de lecturas por distancia, ambos sensores en la misma figura
- Línea comparativa: error vs. distancia para ambos sensores
- Línea comparativa: intensidad/strength vs. distancia para ambos sensores
- Responde: "¿cuál es más preciso y en qué rango?"
- Responde: "¿la señal del TF-Mini S (16 bits) realmente aporta más información que la del LD19 (8 bits)?"

---

## FASE 4 — Aplicación arqueológica en Huehuetenango (OBJ 4)

**Prerrequisito:** Volver a ensamblar el dispositivo LD19 + servo + Pico W + C SDK (firmware picoscan). Esta es la fase de mayor impacto de la tesis.

**Contexto:** El sistema está diseñado para escaneo esférico en espacios cerrados. Las pirámides de Huehuetenango ofrecen cámaras interiores, corredores y bóvedas que son el caso de uso ideal. Si no se permite el acceso al interior, el escaneo de una cara de la bóveda exterior o de un nicho también es válido — lo que importa es documentar la metodología y los resultados honestamente.

**Preparación antes de ir:**
- Cargar firmware picoscan y verificar que el sistema funciona
- Llevar laptop con el visualizador corriendo
- Cinta métrica para medir referencias en campo
- Cámara/celular para fotografiar el setup
- Batería externa si no hay corriente en el sitio
- Identificar al menos 2 espacios candidatos para escanear

---

### Experimento 4A — Escaneo del espacio arqueológico (posición única)

**Objetivo:** Producir el primer modelo 3D de un espacio arqueológico real con el sistema desarrollado.

**Setup:**
- Dispositivo en el interior o frente a una superficie arqueológica de interés
- Una posición fija, escaneo completo
- Medir con cinta al menos 2 dimensiones del espacio (ancho de corredor, altura de bóveda, etc.) para validación posterior

**Datos a capturar:**
- Nube de puntos completa (JSON)
- Tiempo total de escaneo
- Número de puntos
- Fotografías: del dispositivo en el sitio (setup), del espacio escaneado, del resultado en el visualizador
- Croquis o medidas del espacio con cinta

**Entregables:**
```
data/experiments/arqueologia/espacio_01.json
data/experiments/arqueologia/espacio_01_medidas.txt
data/experiments/arqueologia/fotos/
```

---

### Experimento 4B — Validación del modelo arqueológico

**Objetivo:** Verificar que el modelo 3D capturado es geométricamente coherente con el espacio real.

**Metodología:**
1. Del modelo 3D, identificar 2–3 dimensiones medibles (ancho de corredor, altura, profundidad de nicho)
2. Comparar con las medidas tomadas con cinta en campo
3. Calcular error absoluto y error porcentual

**Entregables:**
- Tabla: dimensión real vs. dimensión del modelo vs. error absoluto (mm) vs. error %
- Capturas del visualizador desde al menos 3 ángulos
- Si el error está dentro de ±30 mm (precisión nominal del LD19), el modelo es geométricamente válido

---

### Experimento 4C — Registro multi-posición del espacio arqueológico

**Objetivo:** Documentar un área más grande combinando 2–3 escaneos desde posiciones distintas. Es la demostración de que el sistema escala más allá de un solo punto de captura.

**Setup:**
- 2 o 3 posiciones del dispositivo en el mismo espacio, separadas entre sí
- En cada posición: escaneo completo
- Identificar un **elemento de referencia común** visible desde todas las posiciones (una piedra prominente, esquina de muro, marca en el suelo)
- Medir la distancia entre posiciones del dispositivo con cinta

**Datos a capturar:**
- Una nube de puntos por posición (JSON)
- Fotografías del setup desde cada posición
- Distancia medida entre posiciones
- Identificación del elemento de referencia común

**Entregables:**
```
data/experiments/arqueologia/multipos_01.json
data/experiments/arqueologia/multipos_02.json
data/experiments/arqueologia/multipos_03.json    ← si hay 3 posiciones
data/experiments/arqueologia/multipos_setup.jpg
data/experiments/arqueologia/multipos_notas.txt  ← posiciones, distancias, referencias
```

**Análisis que habilita:**
- Alineación manual de las nubes en el visualizador usando el elemento de referencia común
- Captura del modelo combinado
- Cálculo del área total documentada vs. área documentable por un solo escaneo
- Discusión: limitaciones del sistema para espacios grandes (tiempo de escaneo, alcance del sensor)

---

## Producibles totales: lo que entra al capítulo de resultados

### Tablas del capítulo 4

| # | Tabla | Datos de origen |
|---|-------|-----------------|
| T1 | Especificaciones técnicas LD19 vs. TF-Mini S | Datasheets |
| T2 | Benchmark C SDK: media ± SD de 3 repeticiones | 1A |
| T3 | Benchmark MicroPython: media ± SD de 3 repeticiones | 2A |
| T4 | Comparativa C SDK vs. MicroPython (todas las métricas, con factor ×N) | 1A + 2A |
| T5 | Precisión LD19: error medio, RMSE, SD por distancia | 1B |
| T6 | Precisión TF-Mini S: error medio, RMSE, SD por distancia | 3B |
| T7 | Comparativa de precisión LD19 vs. TF-Mini S | 1B + 3B |
| T8 | Comparativa de densidad de nube 3D: LD19-C vs. LD19-Python | 1C + 2C |
| T9 | Validación modelo 3D: dimensiones reales vs. modelo vs. error | 1C (objeto referencia) + 4B (artefacto) |
| T10 | Resumen aplicación arqueológica: posiciones, puntos, tiempo, error | 4A + 4B + 4C |

---

### Gráficas del capítulo 4

| # | Gráfica | Tipo | Datos de origen |
|---|---------|------|-----------------|
| G1 | Frames/s y Puntos/s: C SDK vs. MicroPython | Barras agrupadas | 1A + 2A |
| G2 | Tiempo de procesamiento por operación (CRC, parsing, UART): C vs. Python | Barras apiladas o agrupadas, escala log | 1A + 2A |
| G3 | Distribución de tasa de error (CRC, header, global): C vs. Python | Barras | 1A + 2A |
| G4 | Error de medición vs. distancia: LD19 vs. TF-Mini S | Líneas con banda de error | 1B + 3B |
| G5 | Distribución de lecturas por distancia: ambos sensores | Boxplot (2×5 cajas) | 1B + 3B |
| G6 | Intensidad de señal vs. distancia: LD19 vs. TF-Mini S | Líneas | 1B + 3B |
| G7 | Nube de puntos: objeto de referencia con C SDK (3 vistas) | Capturas de pantalla | 1C |
| G8 | Nube de puntos: objeto de referencia con MicroPython (3 vistas) | Capturas de pantalla | 2C |
| G9 | Comparación visual de densidad de nube: C SDK vs. MicroPython (misma escena) | Capturas lado a lado | 1C + 2C |
| G10 | Nube de puntos: espacio arqueológico posición única | Capturas de pantalla | 4A |
| G11 | Nube de puntos: registro multi-posición combinado | Captura de pantalla | 4C |
| G12 | Throughput TF-Mini S vs. LD19: lecturas/s, bytes/s | Barras | 1A + 3A |

---

### Scripts de análisis a generar (Python)

Después de tener todos los CSVs, hay que escribir estos scripts en `data/scripts/`:

| Script | Qué hace |
|--------|----------|
| `analizar_precision.py` | Carga todos los CSVs de 1B, 2B, 3B. Calcula error medio, RMSE, SD. Genera G4, G5, G6, T5, T6, T7 |
| `analizar_benchmark.py` | Carga los .txt de 1A, 2A, 3A. Parsea métricas. Genera G1, G2, G3, T2, T3, T4, T12 |
| `analizar_nubes.py` | Carga JSONs de nubes. Cuenta puntos, calcula cobertura angular. Genera T8 |

---

## Orden de ejecución (sin desarmado innecesario)

```
[Dispositivo armado: LD19 + servo + C SDK]
    1A  Benchmark C SDK (60 s × 3 reps)            ~30 min
    1B  Precisión LD19 con C (5 distancias × 300)  ~45 min
    1C  Escaneo 3D caja referencia (C SDK)          ~45 min
    1D  Registro multi-posición (2 escaneos)        ~45 min
    4A  Escaneo arqueológico — posición única    ─┐
    4B  Validación dimensional                    ├─ En Huehuetenango
    4C  Registro multi-posición arqueológico      ┘

[Sin desarmar — cambiar firmware a MicroPython]
    2A  Benchmark MicroPython (60 s × 3 reps)      ~30 min
    2B  Precisión LD19 con Python (5 distancias)   ~45 min
    2C  Escaneo 3D caja referencia (MicroPython)   ~45 min

[Desarmar Pico — conectar TF-Mini S]
    3A  Benchmark TF-Mini S (60 s × 3 reps)        ~30 min
    3B  Precisión TF-Mini S (5 distancias × 300)   ~45 min
```

**Tiempo total estimado en laboratorio:** ~6 horas en 2 sesiones.
**Tiempo en campo (Huehuetenango):** 3–4 horas incluyendo desplazamiento interno al sitio.

---

## Lo que el capítulo 4 va a poder afirmar con evidencia propia

**OBJ 1:** "El sistema integra captura, procesamiento y visualización en un pipeline completo. Un escaneo de referencia con dimensiones conocidas fue reconstruido con error de ±X mm."

**OBJ 2:** "El LD19 presenta un error medio de X mm (RMSE: Y mm) en el rango 20–200 cm. El TF-Mini S presenta un error medio de X mm (RMSE: Y mm) en el mismo rango. El LD19 genera 4,978 pts/s en modo continuo; el TF-Mini S genera 100 lecturas/s. La nube del LD19 tiene N veces mayor densidad para el mismo tiempo de escaneo."

**OBJ 3:** "El C SDK procesa 3× más frames/s que MicroPython. El tiempo de cálculo CRC es 240× mayor en MicroPython. La tasa de error CRC en MicroPython es X% vs. Y% en C SDK. La calidad del modelo 3D producido con MicroPython presenta Z% menos puntos y mayores gaps angulares."

**OBJ 4:** "El sistema documentó [espacio] en las pirámides de Huehuetenango en T segundos, generando N puntos. Mediante registro multi-posición desde 3 ubicaciones, se documentó un área de aproximadamente X m². Las dimensiones reconstruidas difieren de las físicas en ±Z mm."
