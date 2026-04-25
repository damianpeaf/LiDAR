### Tabla 1. Comparativa general de tasa de puntos recopilados

| Enfoque | Sensor | Implementacion | Tipo de prueba | Duracion (s) | Puntos recopilados | Puntos/s |
|---|---|---|---|---:|---:|---:|
| Punto unico | TF-Mini S | Python/MicroPython | Escaneo exploratorio | 1,500 aprox. | 19,943 | 13.3 aprox. |
| Multipunto | LD19 | SDK de C | Captura volumétrica (datos útiles) | 318.779 | 64,205 | 201.41 útiles/s |
| Multipunto | LD19 | MicroPython | Benchmark de lectura | 30.00 | 49,765 | 1,659 |
| Multipunto | LD19 | SDK de C | Benchmark de lectura | 60.00 | 296,576 promedio | 4,942.93 promedio |

Notas:
- La comparacion separa el tipo de prueba para no mezclar escaneo 3D con benchmark de lectura.
- El tiempo del TF-Mini S debe presentarse como aproximado si no existe cronometraje formal.
- La fila de LD19 MicroPython proviene de una prueba historica; puede reemplazarse por una nueva prueba equivalente si se decide repetirla.

### Figura 1. Nube de puntos obtenida con TF-Mini S en interior

Notas:
- Mostrar una vista frontal o isometrica de la nube exploratoria.
- El pie de figura debe indicar que corresponde a una prueba temprana con sensor de punto unico.
- Debe verse la diferencia de densidad/cobertura frente a las nubes finales con LD19.

### Tabla 2. Analisis estadistico de la nube exploratoria TF-Mini S

| Metrica | Valor |
|---|---:|
| Puntos totales | 19,943 |
| Rango X (mm) | PENDIENTE |
| Rango Y (mm) | PENDIENTE |
| Rango Z (mm) | PENDIENTE |
| Volumen de caja envolvente (m3) | PENDIENTE |
| Densidad global (puntos/m3) | PENDIENTE |
| Distancia mediana al vecino mas cercano (mm) | PENDIENTE |
| Desviacion estandar de distancia al vecino mas cercano (mm) | PENDIENTE |
| Coeficiente de variacion de densidad por voxel | PENDIENTE |
| Intensidad media | PENDIENTE |
| Intensidad desv. est. | PENDIENTE |

Notas:
- Calcular con Python a partir de coordenadas XYZ e intensidad.
- Usar una grilla voxel fija para medir uniformidad de cobertura.
- En CloudCompare se puede complementar con `Compute geometric features` o densidad por octree.
- Esta tabla reemplaza juicios cualitativos como irregular/parcial con medidas de cobertura y densidad.

### Tabla 3. Benchmark comparativo de procesamiento LD19: MicroPython vs SDK de C

| Metrica | MicroPython | SDK de C |
|---|---:|---:|
| Corridas disponibles | 1 historica | 3 |
| Duracion base | 30.00 s | 60.00 s |
| Frames/s | 138.5 | 415.06 ± 0.09 |
| Puntos/s | 1,659 | 4,942.93 ± 0.41 |
| Bytes/s UART | 10,845 | 19,508.80 ± 4.75 |
| Error global | 33.66% | 0.106% ± 0.055% |
| CRC errors | PENDIENTE | 0 |
| Tiempo promedio por frame | 6,429 us | 2,073 us aprox. |
| Tiempo promedio de parsing | 5,304 us | 57 us aprox. |

Notas:
- Esta tabla debe aparecer antes de presentar el SDK de C como solucion final.
- Si se repite MicroPython con el mismo protocolo de 60 s, reemplazar la fila historica por media ± desviacion estandar.
- La comparacion central es tasa de puntos, tasa de errores y tiempo por frame.

### Tabla 4. Comparativa de transmision de datos por red

| Implementacion | Duracion (s) | Tipo de unidad transmitida | Unidades transmitidas (n) | Bytes transmitidos | Throughput (bytes/s) | Tamano medio (bytes/unidad) | Errores o intentos fallidos |
|---|---:|---|---:|---:|---:|---:|---:|
| MicroPython | 43.45 | Mensaje WebSocket | 1,110 | 461,477 | 10,622 | 415.75 | 0 errores |
| SDK de C | 318.779 | Lote binario | 668 | 325,944 utiles | 1,022 utiles/s | 487.94 | 9,942 intentos TCP fallidos |

Notas:
- La unidad de comparacion principal es bytes/s.
- La fila SDK de C usa bytes utiles de payload enviados durante el escaneo sectorial del prisma.
- La red funciono para visualizacion, pero la telemetria local queda como fuente cuantitativa mas confiable bajo carga.

### Tabla 5. Precision por distancia controlada con LD19 y SDK de C

| Distancia real (mm) | Lecturas | Media (mm) | Mediana (mm) | Desv. est. (mm) | RMSE (mm) | Error medio abs. (mm) | Error relativo (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 550 | 302 | 546.626 | 546.0 | 1.389 | 3.648 | 3.381 | 0.615 |
| 800 | 311 | 798.543 | 798.0 | 0.789 | 1.656 | 1.469 | 0.184 |
| 1100 | 309 | 1093.249 | 1093.0 | 1.309 | 6.876 | 6.751 | 0.614 |
| 1400 | 309 | 1394.178 | 1394.0 | 1.611 | 6.040 | 5.822 | 0.416 |

Notas:
- La dispersion fue baja en todas las distancias medidas.
- El error relativo se mantuvo por debajo de 1% en el rango evaluado.
- La distancia maxima fue limitada por el espacio disponible de laboratorio.

### Figura 2. Distribucion del error por distancia

Notas:
- Usar boxplot del error `lectura - distancia real` para 550, 800, 1100 y 1400 mm.
- Esta figura es mas informativa que una barra simple porque muestra dispersion, sesgo y outliers.

### Figura 3. Nube de puntos cruda del prisma de referencia en el visualizador

Notas:
- Mostrar vista frontal, superior o isometrica.
- Debe verse el prisma separado de la pared o al menos identificable dentro del sector capturado.

### Tabla 6. Parametros y metricas del escaneo del prisma

| Metrica | Valor |
|---|---:|
| Alto real | 88 mm |
| Largo real | 133 mm |
| Profundidad real | 92 mm |
| Ventana horizontal | 180° a 195° |
| Barrido vertical | 0° a 30° |
| Pasadas del servo | 5 |
| Duracion | 318.779 s |
| Puntos utiles | 64,205 |
| Frames validos | 127,189 |
| Errores CRC | 11 |
| Tasa de error | 0.047% |
| Distancia mediana | 503 mm |

Notas:
- Esta tabla describe el escaneo controlado del objeto de referencia.
- El conteo de puntos corresponde solo a la ventana angular usada para el prisma.

### Figura 4. Malla del prisma generada en CloudCompare

Notas:
- Mostrar malla o superficie generada desde la nube sectorial.
- Idealmente acompanar con una vista de la nube original para contraste.

### Tabla 7. Validacion dimensional del prisma

| Dimension | Real (mm) | Medida en modelo (mm) | Error abs. (mm) | Error (%) | Claridad |
|---|---:|---:|---:|---:|---|
| Alto | 88 | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
| Largo | 133 | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
| Profundidad | 92 | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |

Notas:
- Medir en CloudCompare sobre el modelo final.
- La columna claridad puede ser: clara, regular o difusa.

### Figura 5. Nube de puntos cruda de la Escalera del Gran Palacio de Iximche

Notas:
- Mostrar captura directa de la nube antes de mallado.
- Usar una vista donde se entienda la geometria principal.

### Tabla 8. Analisis estadistico de la nube de la Escalera del Gran Palacio

| Metrica | Valor |
|---|---:|
| Puntos totales | PENDIENTE |
| Rango X (m) | PENDIENTE |
| Rango Y (m) | PENDIENTE |
| Rango Z (m) | PENDIENTE |
| Volumen de caja envolvente (m3) | PENDIENTE |
| Densidad global (puntos/m3) | PENDIENTE |
| Distancia mediana al vecino mas cercano (mm) | PENDIENTE |
| Intensidad media | PENDIENTE |

### Figura 6. Malla de la Escalera del Gran Palacio generada en CloudCompare

Notas:
- Mostrar el resultado mallado.
- Si aplica, mostrar una comparacion nube/malla.

### Figura 7. Nube de puntos cruda del Juego de Pelota, Estructura 8

Notas:
- Mostrar la nube cruda en el visualizador.
- Si hay dos posiciones, presentar una vista combinada o dos subfiguras.

### Tabla 9. Analisis estadistico de la nube del Juego de Pelota, Estructura 8

| Metrica | Valor |
|---|---:|
| Puntos totales | PENDIENTE |
| Rango X (m) | PENDIENTE |
| Rango Y (m) | PENDIENTE |
| Rango Z (m) | PENDIENTE |
| Volumen de caja envolvente (m3) | PENDIENTE |
| Densidad global (puntos/m3) | PENDIENTE |
| Distancia mediana al vecino mas cercano (mm) | PENDIENTE |
| Intensidad media | PENDIENTE |

### Figura 8. Malla del Juego de Pelota, Estructura 8 generada en CloudCompare

Notas:
- Mostrar una vista donde se aprecie el volumen o superficie reconstruida.

### Figura 9. Nube de puntos cruda de la Pared de la Estructura 38

Notas:
- Mostrar la nube cruda antes de procesamiento.
- Si hay dos capturas, usar subfiguras.

### Tabla 10. Analisis estadistico de la nube de la Pared de la Estructura 38

| Metrica | Valor |
|---|---:|
| Puntos totales | PENDIENTE |
| Rango X (m) | PENDIENTE |
| Rango Y (m) | PENDIENTE |
| Rango Z (m) | PENDIENTE |
| Volumen de caja envolvente (m3) | PENDIENTE |
| Densidad global (puntos/m3) | PENDIENTE |
| Distancia mediana al vecino mas cercano (mm) | PENDIENTE |
| Intensidad media | PENDIENTE |

### Figura 10. Malla de la Pared de la Estructura 38 generada en CloudCompare

Notas:
- Mostrar malla o superficie procesada.

### Figura 11. Flujo visual nube-malla en CloudCompare

Notas:
- Usar como figura de apoyo si se quiere mostrar el procesamiento, no como tabla de resultados.
- Subfiguras sugeridas: nube original, nube limpia, malla generada, resultado final.

### Pendientes

Notas:
- Elegir la imagen final del dataset TF-Mini S.
- Confirmar si el tiempo de 25 min del TF-Mini S se presentara como aproximado de bitacora.
- Tomar o reutilizar una prueba minima MicroPython si se quiere reforzar la tabla comparativa.
- Generar capturas finales del prisma.
- Medir dimensiones del prisma en CloudCompare.
- Contar puntos y estadisticas de cada nube arqueologica final.
- Generar figuras finales nube/malla para Iximche.
