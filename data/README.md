# Data

Centraliza datasets, snapshots, reportes y artefactos movibles del repo.

## Principios

- mantener trazabilidad por origen
- no mezclar runtime activo con artefactos de referencia
- no romper nombres históricos innecesariamente

## Estructura

- `apps/visualizer/` — snapshots y JSON auxiliares del visualizador
- `services/lidar-server/` — reportes de performance del backend
- `experiments/ld19c/` — reportes derivados de experimentos históricos

## Excepción importante

`../apps/visualizer/public/puntos.json` no vive acá porque sigue siendo parte activa del runtime actual.
