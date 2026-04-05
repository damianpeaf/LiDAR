# Data

Datasets, snapshots, reportes y artefactos auxiliares organizados por origen.

## Principios

- mantener trazabilidad por origen
- no mezclar runtime activo con artefactos de referencia
- conservar contexto y procedencia de cada archivo

## Estructura

- `apps/visualizer/` — snapshots y JSON auxiliares del visualizador
- `services/lidar-server/` — reportes de performance del backend
- `experiments/ld19c/` — reportes derivados de pruebas con LD19C

## Archivo fuera de esta carpeta

`../apps/visualizer/public/puntos.json` se mantiene junto al frontend porque la aplicación lo usa directamente.
