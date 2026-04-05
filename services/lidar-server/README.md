# lidar-server

Servicio Python que recibe datos LiDAR, los transforma a coordenadas cartesianas, los persiste en Redis y los retransmite a clientes web por WebSocket.

## Responsabilidades

- aceptar conexiones desde firmware Pico
- aceptar clientes web
- almacenar puntos en Redis
- retransmitir nuevos puntos
- limpiar el escaneo actual bajo demanda

## Desarrollo local

### Opción recomendada: Docker Compose desde la raíz del repo

```bash
docker compose up --build
```

Eso levanta Redis + `lidar-server` con la configuración esperada por el visualizador.

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

Reportes de performance disponibles en:

- `../../data/services/lidar-server/performance_reports/`

## Archivos clave

- `main.py` — servidor WebSocket principal
- `_main.py` — implementación previa basada en Flask
- `parse.py` — helpers de parsing y pruebas manuales
- `Dockerfile` — imagen ejecutable del servicio principal
