# Contributing

Gracias por querer aportar.

## Antes de contribuir

1. Abrí un issue si el cambio es grande o cambia arquitectura.
2. Confirmá si el cambio afecta la línea principal o material histórico.
3. No muevas datasets/runtime activos sin justificar compatibilidad.

## Reglas de este repo

- no borrar material histórico
- preservar nombres históricos cuando aportan trazabilidad
- preferir cambios pequeños y revisables
- documentar cambios estructurales en `README.md` o `docs/`
- usar Mermaid para diagramas en Markdown

## Convenciones prácticas

- línea principal: `apps/visualizer`, `services/lidar-server`, `firmware/picoscan`
- histórico: `experiments/`
- artefactos movibles: `data/`

## Pull Requests

Incluí:

- contexto del problema
- alcance del cambio
- riesgos o compatibilidades a revisar
- screenshots o logs si tocás visualización o streaming

Usá el template de PR incluido en `.github/pull_request_template.md`.
