# Experimento NET1 — Comparativa de transmisión de datos por red

**Objetivo:** medir de forma reproducible la transmisión de datos LiDAR hacia el servidor para completar la Tabla 4 de `docs/resultados/README.md`.

**Responde a:** comparación MicroPython vs. SDK de C en la capa de red, separada del benchmark de parsing/UART.

## Setup

- Sensor: LD19 conectado a Pico W.
- Servidor: `services/lidar-server/main.py` corriendo en la misma red WiFi.
- Artefacto del server: `data/services/lidar-server/network_telemetry.csv`.
- Artefacto del firmware C: log serial con líneas `EXP|...|component=telemetry|event=summary`.
- Duración sugerida: 60 s por implementación.
- Repeticiones sugeridas: 3 por implementación si el tiempo alcanza; si no, registrar una corrida y marcarla como exploratoria.

## Qué mide

La unidad primaria es el mensaje recibido por el servidor:

- MicroPython: mensaje WebSocket JSON/texto con `points`.
- SDK de C: lote binario WebSocket con header `PS` y registros compactos de puntos.

El server acumula por corrida:

- duración efectiva desde el primer mensaje de sensor;
- unidades recibidas;
- bytes de payload recibidos por el server;
- bytes estimados de trama WebSocket cliente a servidor (`payload + header + máscara`);
- throughput de entrada en bytes/s;
- tamaño medio por unidad;
- puntos parseados y procesados;
- fallas de parseo, Redis y broadcast.

El firmware C además acumula:

- `batches_sent`;
- `batch_failures`;
- `payload_bytes_sent`;
- `websocket_frame_bytes_sent`;
- throughput de payload y de trama WebSocket.

## Procedimiento

1. Borrar o renombrar `data/services/lidar-server/network_telemetry.csv` antes de cada corrida para que el CSV represente una sola medición.
2. Levantar Redis y el server con el procedimiento de `services/lidar-server/README.md`.
3. Iniciar captura del log serial del Pico.
4. Ejecutar la implementación correspondiente durante 60 s.
5. Detener la captura y guardar el log crudo.
6. Tomar la última fila del CSV del server como resumen de la corrida.
7. Para SDK de C, tomar también la línea `EXP|...|event=summary` del firmware y contrastar `payload_bytes_sent` contra `sensor_bytes` del server.

## CSV resumen sugerido

```csv
implementacion,repeticion,duracion_s,tipo_unidad,unidades_transmitidas,bytes_payload_server,bytes_ws_server_estimados,throughput_payload_server_bytes_s,throughput_ws_server_estimado_bytes_s,tamano_medio_payload_server_bytes,bytes_payload_firmware,bytes_ws_firmware,errores_o_intentos_fallidos,fuente
MicroPython,1,0,Mensaje WebSocket JSON,0,0,0,0,0,0,,,0,data/services/lidar-server/network_telemetry.csv
SDK de C,1,0,Lote binario WebSocket,0,0,0,0,0,0,0,0,0,data/services/lidar-server/network_telemetry.csv + log EXP
```

## Entregables

```text
data/experiments/red/micropython_network_rep1.csv
data/experiments/red/micropython_network_rep1_serial.txt
data/experiments/red/c_sdk_network_rep1.csv
data/experiments/red/c_sdk_network_rep1_serial.txt
data/experiments/red/network_summary.csv
```

## Fórmulas

- `throughput_payload_server_bytes_s = sensor_bytes / duration_s`
- `throughput_ws_server_estimado_bytes_s = estimated_ws_frame_bytes / duration_s`
- `tamano_medio_payload_server_bytes = sensor_bytes / sensor_units`
- `errores_o_intentos_fallidos = parse_failures + redis_failures + broadcast_failures` para server
- En SDK de C, reportar también `batch_failures` porque mide intentos de envío fallidos desde el dispositivo.

## Criterio para Tabla 4

Usar `estimated_ws_frame_bytes` como comparación principal si ambas implementaciones pasan por el server actualizado. Usar `sensor_bytes` solo cuando se quiera comparar payload de aplicación, y `payload_bytes_firmware` cuando se quiera aislar el payload útil del SDK de C.

## Checklist

- [ ] Corrida MicroPython guardada.
- [ ] Corrida SDK de C guardada.
- [ ] Última fila de cada CSV copiada a `network_summary.csv`.
- [ ] Tabla 4 completada con `duration_s`, `sensor_units`, `sensor_bytes`, `estimated_ws_frame_bytes`, `throughput_bytes_s`, `estimated_ws_throughput_bytes_s`, `mean_bytes_unit` y errores.
