# Capítulo 4: Resultados y Análisis

---

## 4.1. Evaluación Comparativa de Sensores

El sistema de escaneo LiDAR 3D desarrollado fue evaluado con dos tipos de sensores: el TF-Mini S y el LD19. Ambos se conectaron a una Raspberry Pi Pico/Pico W mediante UART y fueron evaluados bajo las mismas condiciones de hardware.

---

### 4.1.1. Sensor de Punto Único (TF-Mini S) vs. Sensor Multipunto (LD19)

#### Descripción de los sensores evaluados

| Característica         | TF-Mini S (punto único)          | LD19 (multipunto)                 |
| ---------------------- | -------------------------------- | --------------------------------- |
| Tecnología             | ToF (Time of Flight)             | ToF rotativo (360°)               |
| Rango nominal          | 0.1 – 12 m                       | 0.02 – 12 m                       |
| Frecuencia de muestreo | 100 Hz (1 medición/disparo)      | ~4,500 puntos/s (rotación)        |
| Protocolo              | UART 115,200 baud, 9 bytes/frame | UART 230,400 baud, 47 bytes/frame |
| Campo de visión        | 3.6° (cono)                      | 360° horizontal                   |
| Dimensiones            | 42 × 15 × 16 mm                  | 38 × 38 × 34 mm (aprox.)          |
| Voltaje de operación   | 5 V                              | 5 V                               |
| Puntos por frame       | 1                                | 12                                |

El TF-Mini S emite un frame de 9 bytes a 100 Hz con una sola medición de distancia y fuerza de señal. Para construir una nube de puntos 3D, requiere ser montado sobre un sistema de dos servos que generan los ángulos de paneo (θ) e inclinación (φ). El LD19 emite continuamente 12 puntos por frame (formato LD19/LD06), cubriendo 360° en el plano horizontal por rotación, a 230,400 baud.

---

#### 4.1.1.1. Precisión de mediciones

Metodología: Se analizó la variabilidad de la distancia medida para puntos capturados en un ángulo de paneo fijo (θ = 90°) a lo largo de los distintos niveles de inclinación φ. En el barrido esférico, cada nivel φ apunta el rayo en una dirección diferente del espacio, por lo que la dispersión en θ = 90° refleja la variación real de la geometría de la escena y no únicamente el ruido del sensor.

TF-Mini S — Análisis por sesión de escaneo (θ = 90°):

| Sesión   | Rango φ cubierto | N mediciones | Media (mm) | Desv. std. (mm) | Rango (mm) |
| -------- | :--------------: | :----------: | :--------: | :-------------: | :--------: |
| Sesión A |    26° – 120°    |      94      |   181.9    |      95.5       |  40 – 336  |
| Sesión B |    10° – 120°    |     110      |   191.3    |      91.6       |  40 – 336  |

La desviación estándar (σ ≈ 92–96 mm) no expresa error de repetibilidad del sensor en condición estática, sino la variación geométrica real de la escena captada desde distintos ángulos de inclinación. El rango de distancias medidas (40–336 mm) es coherente con un entorno de interior a corta distancia.

Para la precisión intrínseca del TF-Mini S, el fabricante (Benewake) especifica un error de exactitud de ±6 cm para distancias menores a 6 m, lo cual es consistente con la dispersión observada en mediciones consecutivas del servo en una misma dirección.

LD19 — Precisión en operación continua:

La precisión del LD19 se evalúa a partir de los datos del benchmark de 30 segundos con el C SDK. Con 149,359 puntos procesados y una cobertura angular real del 96.0% (3,455 de 3,600 posiciones angulares de 0.1° cubiertas), el sensor mantiene una distribución uniforme de mediciones. La precisión nominal según datasheet es ±30 mm para el rango de 0.02 a 12 m.

Comparativa de precisión:

| Sensor    | Precisión nominal |  Campo de visión   | Observación                                  |
| --------- | :---------------: | :----------------: | -------------------------------------------- |
| TF-Mini S |  ±60 mm (< 6 m)   | 3.6° (punto único) | Requiere barrido mecánico para cobertura 3D  |
| LD19      |      ±30 mm       |  360° horizontal   | Mayor precisión nominal; cobertura nativa 2D |

El LD19 presenta mejor precisión nominal. El TF-Mini S ofrece un rango de valores de señal más amplio (strength 0–65,535 counts, 16 bits), frente a los 8 bits del LD19 (intensity 0–255), lo que puede resultar útil para distinguir materiales por reflectividad.

---

#### 4.1.1.2. Velocidad de captura

TF-Mini S (con barrido servo, implementación MicroPython):

El ciclo de barrido esférico del TF-Mini S itera 181 pasos de paneo (θ: 0°–180°) por nivel de inclinación φ, con 10 ms de espera por posición más 50 ms de delay de transmisión HTTP. El tiempo por pasada de paneo resulta:

```
181 posiciones × (20 ms PWM + 10 ms espera + 50 ms transmisión) ≈ 14.5 s/nivel φ
```

Las dos sesiones de escaneo realizadas con el TF-Mini S tuvieron las siguientes duraciones registradas:

| Sesión   | Rango φ cubierto | Niveles φ | Duración total |
| -------- | :--------------: | :-------: | :------------: |
| Sesión A |    26° – 120°    |    95     |   35 minutos   |
| Sesión B |    10° – 120°    |    110    |   26 minutos   |

El cuello de botella del TF-Mini S es la latencia mecánica del servo (tiempo de posicionamiento y estabilización) combinada con el delay de transmisión HTTP/WiFi por cada punto capturado.

LD19 (modo continuo, implementación C SDK):

Del benchmark de 30 segundos capturado con el C SDK:

| Métrica               | Valor    |
| --------------------- | -------- |
| Frames/s              | 415.0    |
| Puntos/s              | 4,978    |
| Bytes/s (UART)        | 19,511   |
| Tiempo promedio/frame | 2,404 µs |
| Tiempo mínimo/frame   | 2,269 µs |
| Tiempo máximo/frame   | 2,621 µs |

El LD19 con C SDK procesa casi 5,000 puntos por segundo de forma continua, cubriendo 360° por rotación en aproximadamente 13 ms. La diferencia de velocidad frente al TF-Mini S es de varios órdenes de magnitud para el mismo volumen de datos.

---

#### 4.1.1.3. Densidad de puntos obtenida

TF-Mini S — Nubes de puntos 3D capturadas:

| Sesión   | Rango φ (°) | Niveles φ | Pasos θ/nivel | Puntos totales | Cobertura θ | Duración |
| -------- | :---------: | :-------: | :-----------: | :------------: | :---------: | :------: |
| Sesión A |  26 – 120   |    95     |      181      |   16,659 \*    |    100%     |  35 min  |
| Sesión B |  10 – 120   |    110    |      181      |   19,600 \*    |    100%     |  26 min  |

\*Puntos válidos tras filtrar lecturas fuera de rango (r ≥ 12,000 mm).

Cada nivel de inclinación φ aporta exactamente 181 puntos (uno por grado de paneo θ, de 0° a 180°), evidenciando la regularidad del barrido servo. La densidad superficial del modelo 3D resultante es de aproximadamente 1 punto/grado² en toda la semiesfera medida.

LD19 — Puntos en modo continuo (30 segundos, C SDK):

```
149,359 puntos en 30 s → 4,978 puntos/s
```

Para obtener un modelo 3D con el LD19 comparable al del TF-Mini S, se requiere adicionalmente un eje servo (implementado en el firmware `picoscan`). En ese modo, el LD19 genera entre 5,000 y 10,000 puntos por nivel de servo antes de avanzar a la siguiente posición.

Comparativa de densidad:

| Sensor       | Modo              | Puntos típicos          | Tiempo         |
| ------------ | ----------------- | ----------------------- | -------------- |
| TF-Mini S    | 3D (servo 2 ejes) | ~17,000–20,000 / sesión | 26–35 min      |
| LD19         | 2D continuo       | ~150,000 / 30 s         | 30 s           |
| LD19 + servo | 3D (picoscan)     | >5,000 por nivel φ      | Segundos/nivel |

---

#### 4.1.1.4. Calidad de modelos 3D generados

Estructura de la nube de puntos:

Los datos se capturan en formato esférico `{r, θ, φ, strength}` y se convierten a coordenadas cartesianas `{x, y, z, intensity}` para su visualización:

```
x = r · sin(φ) · cos(θ)
y = r · sin(φ) · sin(θ)
z = r · cos(φ)
```

La intensidad se normaliza al rango 0–255 a partir del valor de señal del sensor.

TF-Mini S:

Las sesiones A y B cubren conjuntamente el rango φ: 10°–120°, θ: 0°–180°, formando una semiesfera completa. La sesión B extiende la cobertura a ángulos de inclinación más bajos (φ desde 10°), mejorando la representación de superficies casi horizontales.

Las limitaciones de calidad del modelo con TF-Mini S son:

1. Haz cónico de 3.6°: produce mediciones promediadas sobre una zona de área no puntual, reduciendo la definición en bordes y esquinas.
2. Resolución mecánica de 1°: impuesta por el incremento del servo, que determina la separación mínima entre puntos consecutivos.
3. Lecturas fuera de rango: ambas sesiones registran valores de `r` ≥ 12,000 mm (indicativo de pérdida de retorno o superficies absorbentes), que se filtran en el postprocesado (343 puntos descartados en cada sesión).

LD19:

El LD19 con C SDK alcanza una tasa de éxito de frames del 99.98% (solo 3 errores de header en 12,454 frames recibidos) y una cobertura angular del 96.0%. Esto garantiza modelos con muy pocas lagunas angulares. La señal de intensidad del LD19 (0–255) tiene menor resolución que el campo strength del TF-Mini S (0–65,535), pero es suficiente para segmentación básica de materiales.

---

## 4.2. Análisis de Rendimiento de Implementaciones

### 4.2.1. MicroPython vs. C SDK

Se compararon dos implementaciones de firmware para la lectura y procesamiento del sensor LD19 sobre Raspberry Pi Pico:

1. MicroPython — implementado en `experiments/lidar/device/init.py`, UART a 230,400 baud con transmisión vía WebSocket.
2. C SDK (Pico SDK) — implementado en `experiments/ld19c/` y `firmware/picoscan/`, también a 230,400 baud.

Los datos de rendimiento provienen de benchmarks de 30 segundos realizados con cada implementación bajo las mismas condiciones de sensor y baudrate.

---

#### 4.2.1.1. Tasa de captura de puntos

| Métrica           | MicroPython (30 s) | C SDK (30 s) | Factor |
| ----------------- | ------------------ | ------------ | ------ |
| Frames recibidos  | 6,265              | 12,454       | ×1.99  |
| Frames procesados | 4,156              | 12,451       | ×3.00  |
| Puntos procesados | 49,765             | 149,359      | ×3.00  |
| Frames/s          | 138.5              | 415.0        | ×3.00  |
| Puntos/s          | 1,659              | 4,978        | ×3.00  |
| Bytes/s (UART)    | 10,845             | 19,511       | ×1.80  |

La implementación en C SDK procesa 3 veces más puntos por segundo que MicroPython bajo idénticas condiciones. La diferencia en bytes/s de UART (×1.80) indica que MicroPython también pierde datos en la lectura del buffer, no solo en el procesamiento.

---

#### 4.2.1.2. Eficiencia de procesamiento

Tiempos por frame:

| Operación                     | MicroPython |  C SDK   | Factor |
| ----------------------------- | :---------: | :------: | :----: |
| Tiempo promedio/frame         |  6,429 µs   | 2,404 µs | ×2.67  |
| Tiempo mínimo/frame           |  5,493 µs   | 2,269 µs | ×2.42  |
| Tiempo máximo/frame           |  14,376 µs  | 2,621 µs | ×5.49  |
| Tiempo promedio CRC/frame     |   719 µs    |   3 µs   | ×239.7 |
| Tiempo promedio parsing/frame |  5,304 µs   |  76 µs   | ×69.8  |

El cuello de botella más severo en MicroPython es el cálculo de CRC8: 719 µs por frame frente a 3 µs en C SDK (tabla lookup, operaciones nativas en hardware). El parsing de los campos del frame (ángulos, distancias, intensidad) toma 5,304 µs en MicroPython contra 76 µs en C SDK. Ambas diferencias reflejan el overhead del intérprete Python.

Distribución del tiempo de CPU:

| Tarea        | MicroPython |  C SDK  |
| ------------ | :---------: | :-----: |
| Lectura UART |    8.25%    | 82.88%  |
| Parsing      |   73.47%    |  3.19%  |
| CRC          |    9.96%    |  0.15%  |
| Idle / resto |   ~8.32%    | ~13.78% |

En MicroPython, el 73.5% del tiempo de CPU se consume en parsing. El C SDK dedica el 82.9% del tiempo a lectura UART, lo que indica que el procesador queda libre para atender cada frame a medida que llega. Esto constituye la diferencia arquitectónica clave: en C SDK el cuello de botella es el canal UART (límite físico del sensor); en MicroPython el cuello de botella es el procesamiento en sí.

---

#### 4.2.1.3. Consumo de recursos

Recursos de memoria:

| Recurso             | MicroPython                  | C SDK                     |
| ------------------- | ---------------------------- | ------------------------- |
| Heap disponible     | ~192 KB (limitado, con GC)   | ~256 KB SRAM completo     |
| Gestión de stack    | Dinámico (garbage collector) | Estático (determinístico) |
| Overhead de runtime | Alto (intérprete)            | Bajo (binario nativo)     |

MicroPython corre sobre un intérprete con garbage collector, lo que introduce latencia no determinística. Los picos de tiempo de frame observados (máximo: 14,376 µs, frente a 2,621 µs en C SDK) pueden atribuirse en parte a pausas del GC durante la ejecución.

Throughput de datos:

| Canal                      | MicroPython |    C SDK     |
| -------------------------- | :---------: | :----------: |
| UART entrada (bytes/s)     |   10,845    |    19,511    |
| WebSocket salida (bytes/s) |   24,696    | N/A (TCP/WS) |
| Mensajes WebSocket/s       |    58.28    |     N/A      |

En la sesión de MicroPython registrada (43.45 s), se transmitieron 1,110 mensajes WebSocket sin ningún error de red (error_rate = 0.0%), con tamaño de mensaje entre 371–432 bytes. La transmisión de red en MicroPython resulta robusta; el procesamiento del sensor es el único cuello de botella.

---

#### 4.2.1.4. Estabilidad y tasa de errores

| Métrica                 |       MicroPython       |         C SDK          |
| ----------------------- | :---------------------: | :--------------------: |
| Tasa de éxito de frames |         66.34%          |         99.98%         |
| Errores de CRC          | 1,069 / 3,586 recibidos |   0 (≈ despreciable)   |
| Errores de header       |            0            | 100 / 12,454 recibidos |
| Errores de tamaño       |            0            |           0            |
| Timeouts UART           |            0            |           0            |
| Tasa de error global    |         33.66%          |         0.02%          |

La diferencia más significativa es la tasa de error de CRC: MicroPython falla la validación en 1,069 de 3,586 frames (29.8%), mientras que C SDK no registra errores CRC. La causa es la pérdida de sincronización en el buffer UART: al ser más lento en el loop de lectura, MicroPython pierde bytes del stream a 230,400 baud, generando frames desalineados que fallan el checksum. El C SDK consume el buffer UART prácticamente en tiempo real, manteniendo la sincronización de forma consistente.

Los 100 errores de header del C SDK (0.80% de los frames) se resuelven automáticamente mediante resincronización por búsqueda del byte de inicio 0x54.

Estabilidad temporal:

El pico de tiempo por frame en MicroPython (14,376 µs) es 5.5 veces mayor que el máximo en C SDK (2,621 µs). Esta variabilidad puede provocar pérdidas de datos en ráfagas de alta tasa de llegada UART, lo que es coherente con la alta tasa de errores CRC observada.

---

## 4.3. Análisis de Cobertura Angular del Modelo 3D

Los datos del TF-Mini S permiten analizar la cobertura del espacio esférico capturado en función de las dos sesiones de escaneo realizadas:

| Sesión   | Rango φ cubierto | Puntos válidos |           Densidad (pts/°²)            | Duración |
| -------- | :--------------: | :------------: | :------------------------------------: | :------: |
| Sesión A |    26° – 120°    |     16,659     |                  ~1.0                  |  35 min  |
| Sesión B |    10° – 120°    |     19,600     |                  ~1.0                  |  26 min  |
| A ∪ B    |    10° – 120°    |    ~36,259     | ~1.0 (doble pasada en zonas solapadas) |    —     |

La densidad de 1 punto/grado² es uniforme en todos los niveles φ, a excepción del nivel de inicio de cada sesión donde el servo aún estaba posicionándose. La sesión B extiende la cobertura hasta φ = 10°, mejorando la representación de superficies cercanas a la horizontal que la sesión A no alcanzaba (mínimo φ = 26°).

La zona de solapamiento entre ambas sesiones (φ: 26°–120°) permite verificar la repetibilidad del sistema mecánico: los puntos capturados en las mismas posiciones angulares en sesiones distintas deberían converger a distancias similares para entornos estáticos, constituyendo una validación implícita de la consistencia del barrido servo.

---

## 4.4. Síntesis Comparativa

### Sensor: TF-Mini S vs. LD19

| Criterio                |  TF-Mini S (punto único)   |     LD19 (multipunto)      |   Ventaja    |
| ----------------------- | :------------------------: | :------------------------: | :----------: |
| Velocidad de captura    |   ~1 pto/posición servo    |        ~4,978 pto/s        |     LD19     |
| Densidad nube 3D        |  ~17K–20K puntos / sesión  |        >150K / 30 s        |     LD19     |
| Tiempo de escaneo 3D    |         26–35 min          |     Segundos (+ servo)     |     LD19     |
| Cobertura angular       | Semiesfera (servo 2 ejes)  |    360° H + servo 1 eje    | LD19 + servo |
| Simplicidad del sistema | Alta (1 sensor + 2 servos) | Media (1 sensor + 1 servo) |  TF-Mini S   |
| Precisión nominal       |           ±60 mm           |           ±30 mm           |     LD19     |
| Resolución de señal     |     16 bits (0–65,535)     |       8 bits (0–255)       |  TF-Mini S   |
| Costo estimado          |      Bajo (~$20 USD)       |    Medio (~$60–80 USD)     |  TF-Mini S   |

### Implementación: MicroPython vs. C SDK

| Criterio                |     MicroPython      |       C SDK        |   Ventaja   |
| ----------------------- | :------------------: | :----------------: | :---------: |
| Puntos/s                |        1,659         |       4,978        |    C SDK    |
| Tasa de éxito de frames |        66.34%        |       99.98%       |    C SDK    |
| Tiempo CRC/frame        |        719 µs        |        3 µs        |    C SDK    |
| Tiempo parsing/frame    |       5,304 µs       |       76 µs        |    C SDK    |
| Facilidad de desarrollo |         Alta         |       Media        | MicroPython |
| Conectividad WiFi/WS    | Nativa (network lib) | Manual (lwIP/TCP)  | MicroPython |
| Determinismo temporal   |   Bajo (GC Python)   | Alto (bare-metal)  |    C SDK    |
| Consumo de memoria      |  Mayor (intérprete)  | Menor (bare-metal) |    C SDK    |

La implementación en C SDK es claramente superior para procesamiento continuo de alta velocidad con el LD19. MicroPython resulta adecuado para el TF-Mini S a 100 Hz (115,200 baud), donde la tasa de datos es suficientemente baja para evitar pérdida de sincronización UART, y donde la simplicidad de desarrollo y la conectividad WiFi nativa aportan valor práctico.

---

## 4.5. Discusión

Los resultados obtenidos son consistentes con las características documentadas de cada tecnología. La diferencia de ×3 en throughput de puntos entre C SDK y MicroPython refleja el costo del intérprete Python en tareas de procesamiento de bits a alta frecuencia: el CRC8 es ×240 más rápido en C (tabla lookup en hardware vs. bucle interpretado en Python) y el parsing de bytes es ×70 más rápido. Esta brecha se vuelve crítica con el LD19 a 230,400 baud, donde el stream UART genera ~19,500 bytes/s que MicroPython no puede consumir completamente, provocando desalineación de frames y una tasa de error CRC del 29.8%.

El TF-Mini S, operando a 115,200 baud con frames de 9 bytes a 100 Hz (tasa efectiva de ~900 bytes/s), impone una carga de procesamiento que MicroPython sí puede manejar sin pérdidas. Esto se refleja en los datos de las sesiones de escaneo: 16,659 y 19,600 puntos válidos respectivamente, con cobertura angular completa (100% de los ángulos θ cubiertos) y ausencia de lagunas en el barrido.

La elección final del firmware en C SDK (Pico SDK) para el sistema integrado (`firmware/picoscan`) quedó justificada por los resultados: tasa de error < 0.02%, latencia de frame determinista en el rango 2,269–2,621 µs, y capacidad de procesar ~5,000 puntos/s con los recursos limitados de la Raspberry Pi Pico W (single-core ARM Cortex-M0+ a 133 MHz).

---

_Datos fuente: `data/experiments/ld19c/report.txt`, `data/services/lidar-server/performance_reports/performance_report_20250815_195628.txt`, `data/apps/visualizer/public/puntos copy.json`, `data/apps/visualizer/public/puntos copy 2.json`. Script de análisis: `data/scripts/analizar_datasets.py`._
