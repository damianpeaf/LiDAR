# LiDAR

![Repository status](https://img.shields.io/badge/status-research%20prototype-0a66c2)
![Firmware](https://img.shields.io/badge/firmware-Raspberry%20Pi%20Pico%20W-6f42c1)
![Frontend](https://img.shields.io/badge/frontend-Next.js-111111)
![Backend](https://img.shields.io/badge/backend-Python%20WebSockets-3776ab)
![Vercel](https://img.shields.io/badge/vercel-apps%2Fvisualizer-000000)

Proyecto de investigación y desarrollo de captura LiDAR orientado a escaneo 3D de bajo costo para trabajo de campo y visualización en tiempo real.

Stack principal:

- firmware en Raspberry Pi Pico W
- backend Python + Redis
- visualizador web en Next.js

## Índice

- [Quick start](#quick-start)
- [Qué incluye](#qué-incluye)
- [Estructura](#estructura)
- [Arquitectura](#arquitectura)
- [Datasets y artefactos](#datasets-y-artefactos)
- [Contribución](#contribución)
- [Seguridad](#seguridad)
- [Licencia](#licencia)
- [Cómo citar](#cómo-citar)

## Quick start

La forma más simple de probar el sistema es levantar backend + Redis con Docker y luego abrir el visualizador.

### Requisitos

- Docker y Docker Compose
- Node.js 20+
- pnpm

### 1) Backend + Redis

```bash
docker compose up --build
```

Esto expone:

- `redis` en `localhost:6379`
- `lidar-server` en `ws://localhost:3000`

### 2) Frontend

```bash
cd apps/visualizer
pnpm install
pnpm dev
```

La app espera un WebSocket en `ws://localhost:3000`.

Abrí luego `http://localhost:3000` en el navegador.

### 3) Backend sin Docker (opcional)

```bash
cd services/lidar-server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Requiere Redis disponible en `redis://localhost:6379/0` o configurar `REDIS_URL`.

### 4) Firmware

Ver instrucciones en [`firmware/picoscan/README.md`](./firmware/picoscan/README.md).

## Qué incluye

- `apps/visualizer` — visualizador web en Next.js
- `services/lidar-server` — servidor WebSocket y persistencia temporal en Redis
- `firmware/picoscan` — firmware para Raspberry Pi Pico W
- `data/` — snapshots y reportes de ejemplo
- `docs/` — diagramas y documentación técnica
- `experiments/` — prototipos y pruebas anteriores

Si querés empezar rápido, concentrate en:

- `docker-compose.yml`
- `apps/visualizer/`
- `services/lidar-server/`

## Estructura

```text
.
├── apps/
│   └── visualizer/
├── services/
│   └── lidar-server/
├── firmware/
│   └── picoscan/
├── experiments/
│   ├── integration_poc/
│   ├── integraton_poc/
│   ├── ld19/
│   ├── ld19c/
│   ├── lidar/
│   ├── main/
│   ├── motors_poc/
│   ├── servo_poc/
│   ├── stepper_poc/
│   ├── tf_poc/
│   └── wstest/
├── data/
│   ├── apps/
│   ├── experiments/
│   └── services/
├── docs/
├── .github/
├── CONTRIBUTING.md
├── LICENSE
└── SECURITY.md
```

Ver mapa detallado en [`docs/repo-map.md`](./docs/repo-map.md).

## Arquitectura

Flujo principal:

1. `firmware/picoscan` captura y empaqueta puntos.
2. `services/lidar-server` procesa, persiste y retransmite vía WebSocket.
3. `apps/visualizer` consume el stream y renderiza la nube de puntos.

Documentación relacionada:

- [`docs/runtime-architecture.md`](./docs/runtime-architecture.md)
- [`docs/evolution-lineage.md`](./docs/evolution-lineage.md)

## Datasets y artefactos

La carpeta `data/` reúne snapshots, reportes y archivos auxiliares organizados por origen.

Ejemplos:

- `data/services/lidar-server/performance_reports/`
- `data/experiments/ld19c/report.txt`
- `data/apps/visualizer/public/`
- `data/apps/visualizer/app-data/`

### Archivo usado por la aplicación

`apps/visualizer/public/puntos.json` forma parte del flujo de la aplicación web y se mantiene junto al frontend.

## Siguiente paso recomendado

1. `docker compose up --build`
2. `cd apps/visualizer && pnpm install && pnpm dev`
3. abrir `http://localhost:3000`

## Contribución

Leé [`CONTRIBUTING.md`](./CONTRIBUTING.md) antes de abrir issues o PRs.

## Seguridad

Leé [`SECURITY.md`](./SECURITY.md) para divulgación responsable y consideraciones sobre artefactos históricos.

## Licencia

Este repo incluye una licencia **conservadora y temporal** en [`LICENSE`](./LICENSE).

No asumí una licencia permisiva sin confirmación explícita del autor. Si el proyecto va a publicarse formalmente como open source, conviene reemplazarla por una licencia aprobada por OSI (por ejemplo MIT, BSD-3-Clause o Apache-2.0) antes del lanzamiento público.

## Cómo citar

Si necesitás citar este trabajo mientras no exista DOI o paper publicado, usá una referencia descriptiva al repositorio y a la tesis/proyecto asociado. Ejemplo:

```text
Damian Peña. LiDAR: low-cost LiDAR scanning research repository. GitHub repository.
```
