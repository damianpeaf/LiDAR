# Visualizer

Aplicación Next.js para visualizar en 3D la nube de puntos LiDAR en tiempo real.

## Rol en la arquitectura

- consume el stream WebSocket del servicio `services/lidar-server`
- renderiza la nube de puntos con `react-three-fiber`
- permite exportar / importar JSON
- usa `public/puntos.json` como archivo local de compatibilidad

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
- `public/` — assets públicos; `puntos.json` se usa como archivo local de compatibilidad

## Datasets relacionados

Snapshots y JSON auxiliares disponibles en:

- `../../data/apps/visualizer/public/`
- `../../data/apps/visualizer/app-data/`

## Deploy

El proyecto Vercel `lidar` usa `apps/visualizer` como Root Directory.

## Notas

- Si cambiás `public/puntos.json`, revisá primero las rutas que lo leen o escriben.
- Los archivos en `data/` son artefactos de referencia y muestras de prueba.
