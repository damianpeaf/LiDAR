# Runtime Architecture

```mermaid
flowchart LR
    Sensor[LiDAR sensor] --> Pico[firmware/picoscan\nPico W]
    Servo[servo motor] --> Pico
    Pico -->|WebSocket / batched points| Server[services/lidar-server]
    Redis[(Redis)] <--> Server
    Server -->|initial_state / new_points / clear events| Web[apps/visualizer]
    Web -->|clear_scan| Server
    Web -->|reads/writes local compatibility file| Puntos[apps/visualizer/public/puntos.json]
```

## Notas

- `puntos.json` sigue en `apps/visualizer/public/` por compatibilidad actual.
- Los snapshots auxiliares ya no viven dentro del runtime principal; fueron movidos a `data/`.
