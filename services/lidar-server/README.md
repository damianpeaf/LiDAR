# lidar-server

Servicio Python que recibe datos LiDAR, los transforma a coordenadas cartesianas, los persiste en Redis y los retransmite a clientes web por WebSocket.

## Responsabilidades

- aceptar conexiones desde firmware Pico
- aceptar clientes web
- almacenar puntos en Redis
- retransmitir nuevos puntos
- limpiar el escaneo actual bajo demanda

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Dependencias

- Python 3.12+
- Redis accesible por `REDIS_URL`

## Artefactos históricos movidos

Los reportes de performance viven ahora en:

- `../../data/services/lidar-server/performance_reports/`

## Archivos clave

- `main.py` — servidor WebSocket principal
- `_main.py` — implementación previa basada en Flask
- `parse.py` — helpers de parsing y pruebas manuales
- `Dockerfile` — contenedor mínimo de desarrollo
