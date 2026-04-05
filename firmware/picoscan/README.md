# picoscan

Firmware principal de la línea activa para Raspberry Pi Pico W.

## Responsabilidades

- leer datos LiDAR por UART
- controlar el servo para barrido vertical
- agrupar puntos
- transmitirlos al backend por red

## Archivos clave

- `picoscan.cpp` — loop principal de la aplicación
- `lidar.cpp` / `lidar.hpp` — parsing del sensor
- `servo_controller.*` — control del servo
- `tcp_client.*` y `ws.*` — conectividad y framing
- `wifi_manager.*` — conexión Wi‑Fi

## Build manual

No ejecutado en esta reorganización. Flujo esperado:

```bash
mkdir build
cd build
cmake ..
cmake --build .
```

## Hardware esperado

- Raspberry Pi Pico W
- sensor LiDAR compatible
- servo para barrido vertical

## Advertencias

- Revisá credenciales o direcciones hardcodeadas antes de publicar o desplegar hardware real.
- El repo no reescribe historia ni purga secretos históricos automáticamente.
