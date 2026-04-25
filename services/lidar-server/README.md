# lidar-server

Servicio Python que recibe datos LiDAR, los transforma a coordenadas cartesianas, los persiste en Redis y los retransmite a clientes web por WebSocket.

## Desarrollo local

### Opción recomendada

```bash
docker compose up --build
```

Eso levanta Redis y el servidor WebSocket en `localhost:3000`.

### Opción manual

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Dependencias

- Python 3.12+
- Redis accesible por `REDIS_URL`

## Puertos

- `3000` — WebSocket server
- `6379` — Redis (si usás Docker Compose desde la raíz)

## Reportes y artefactos

Archivos relacionados disponibles en:

- `../../data/services/lidar-server/performance_reports/`
- `../../data/services/lidar-server/network_telemetry.csv` — telemetría acumulada de unidades, payload recibido y bytes estimados de trama WebSocket para la Tabla 4.

La ruta del CSV de red puede sobrescribirse con `NETWORK_TELEMETRY_CSV`.

## Archivos clave

- `main.py` — servidor WebSocket principal
- `parse.py` — helpers de parsing y pruebas manuales
