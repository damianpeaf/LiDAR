# LiDAR

![Repository status](https://img.shields.io/badge/status-reorganized-0a66c2)
![Firmware](https://img.shields.io/badge/firmware-Raspberry%20Pi%20Pico%20W-6f42c1)
![Frontend](https://img.shields.io/badge/frontend-Next.js-111111)
![Backend](https://img.shields.io/badge/backend-Python%20WebSockets-3776ab)
![Vercel](https://img.shields.io/badge/vercel-apps%2Fvisualizer-000000)

Proyecto de investigación y desarrollo de captura LiDAR orientado a escaneo 3D de bajo costo para trabajo de campo y visualización en tiempo real.

## Índice

- [Resumen](#resumen)
- [Línea principal del repo](#línea-principal-del-repo)
- [Quick start](#quick-start)
- [Estructura](#estructura)
- [Arquitectura](#arquitectura)
- [Datasets y artefactos](#datasets-y-artefactos)
- [Deploy en Vercel](#deploy-en-vercel)
- [Histórico y experimentos](#histórico-y-experimentos)
- [Contribución](#contribución)
- [Seguridad](#seguridad)
- [Licencia](#licencia)
- [Cómo citar](#cómo-citar)

## Resumen

El repo quedó reorganizado para separar con claridad:

- **producto actual**
- **experimentos históricos**
- **datasets / reportes / snapshots**
- **documentación para publicación open source**

La línea activa hoy está compuesta por:

- `firmware/picoscan`
- `services/lidar-server`
- `apps/visualizer`

## Línea principal del repo

### `firmware/picoscan`
Firmware para Raspberry Pi Pico W que captura datos del sensor, controla el barrido y transmite puntos.

### `services/lidar-server`
Servicio Python con WebSockets y Redis para recibir, persistir y retransmitir la nube de puntos.

### `apps/visualizer`
Aplicación Next.js para visualización interactiva de la nube de puntos y operación manual desde web.

## Quick start

La forma más simple de probar la línea principal hoy es levantar primero la infraestructura base con Docker.

### 1) Infraestructura base con Docker

```bash
docker compose up --build
```

Esto levanta:

- `redis` en `localhost:6379`
- `lidar-server` en `ws://localhost:3000`

> El `docker-compose.yml` histórico de `experiments/lidar/` se conserva solo como referencia legacy. El compose de la raíz es el recomendado para la línea principal actual.

### 2) Frontend

```bash
cd apps/visualizer
pnpm install
pnpm dev
```

La app espera un WebSocket en `ws://localhost:3000`.

### 3) Backend sin Docker (alternativa)

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

Los artefactos movibles fueron centralizados en `data/` manteniendo trazabilidad por origen.

Ejemplos:

- `data/services/lidar-server/performance_reports/`
- `data/experiments/ld19c/report.txt`
- `data/apps/visualizer/public/`
- `data/apps/visualizer/app-data/`

### Excepción intencional

`apps/visualizer/public/puntos.json` **no se movió** porque sigue siendo una ruta activa hardcodeada en el flujo actual.

## Deploy en Vercel

El proyecto Vercel `lidar` quedó actualizado para usar:

- **Root Directory:** `apps/visualizer`

Comando de verificación:

```bash
vercel project inspect lidar
```

## Histórico y experimentos

Todo el material no perteneciente a la línea principal vive en [`experiments/`](./experiments/README.md).

Se preservaron nombres históricos para no romper trazabilidad, incluyendo typos existentes como `integraton_poc`.

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
