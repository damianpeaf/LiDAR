# Visualizer

Aplicación Next.js para visualizar en 3D la nube de puntos LiDAR en tiempo real.

## Rol en la arquitectura

- consume el stream WebSocket del servicio `services/lidar-server`
- renderiza la nube de puntos con `react-three-fiber`
- permite exportar / importar JSON

## Desarrollo local

```bash
pnpm install
pnpm dev
```

Por defecto, la UI intenta conectarse a:

```text
ws://localhost:3000
```

## Datasets relacionados

Archivos de ejemplo disponibles en:

- `../../data/apps/visualizer/public/`
- `../../data/apps/visualizer/app-data/`

## Notas

- `public/puntos.json` se usa como archivo local de compatibilidad.
- Los archivos en `data/` son artefactos de referencia y muestras de prueba.
