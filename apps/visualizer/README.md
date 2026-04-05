# Visualizer

Aplicación Next.js para visualizar en 3D la nube de puntos LiDAR en tiempo real.

## Rol en la arquitectura

- consume el stream WebSocket del servicio `services/lidar-server`
- renderiza la nube de puntos con `react-three-fiber`
- permite exportar / importar JSON
- conserva `public/puntos.json` como artefacto activo del flujo actual

## Desarrollo local

```bash
pnpm install
pnpm dev
```

Por defecto, la UI intenta conectarse a:

```text
ws://localhost:3000
```

## Estructura interna

- `app/` — rutas y layout de Next.js
- `components/` — UI y visualización 3D
- `lib/` — acciones server-side auxiliares
- `public/` — assets públicos; `puntos.json` permanece acá por compatibilidad

## Datasets relacionados

Los snapshots auxiliares se movieron a:

- `../../data/apps/visualizer/public/`
- `../../data/apps/visualizer/app-data/`

## Deploy

El proyecto Vercel `lidar` usa `apps/visualizer` como Root Directory.

## Notas

- No mover `public/puntos.json` sin antes cambiar las rutas activas que lo usan.
- Los archivos en `data/` son artefactos de referencia, no parte del runtime principal.
