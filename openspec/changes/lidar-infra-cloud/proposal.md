# Proposal: LiDAR Cloud Infrastructure

## Intent

Llevar el sistema LiDAR a producción con autenticación, almacenamiento en nube y despliegue real. Actualmente el sistema sólo funciona en local sin auth, sin persistencia de escaneos y con una sola página sin estructura.

## Scope

### In Scope
- Landing page pública en Next.js (ruta `/`, visualizer a `/app`)
- Auth Supabase: registro → lista de espera → aprobación por admin
- Modo público: sólo cargar ejemplos; modo auth: todas las acciones + backend
- Backend Python: validación JWT Supabase para clientes web + password configurable para dispositivos LiDAR
- Deploy Python + Redis en Railway
- Cloudflare R2: bucket para escaneos y ejemplos
- Tabla `examples` en Supabase con flag `public` + RLS policies
- Guardar escaneos con metadata (puntos/seg, timestamps, estadísticas)
- Variables de entorno en Vercel + Railway

### Out of Scope
- App móvil
- Multi-tenant (múltiples dispositivos simultáneos con sesiones aisladas)
- Dashboard de admin propio (admin usa Supabase Studio)
- Real-time collaboration

## Approach

**Frontend**: Next.js App Router — `/` landing page estática, `/app` visualizer existente con guards. Supabase Auth via `@supabase/ssr`.

**Auth flow**: Register → perfil creado con `status='pending'` → admin en Supabase Studio cambia a `status='approved'` → usuario puede hacer login funcional.

**Backend dual-auth**: 
- Clientes web envían JWT Supabase en header WebSocket o handshake HTTP; backend valida con Supabase Admin SDK
- Dispositivos LiDAR envían password en primer mensaje; backend compara con `DEVICE_PASSWORD` env var

**Railway**: docker-compose existente adaptado para Railway (Python service + Redis plugin).

**R2**: Escaneos se suben como `scans/{id}.json` vía API REST de R2. Ejemplos en `examples/{id}.json`. URLs guardadas en Supabase.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/visualizer/app/` | Modified | Nueva estructura: `/` landing, `/app` visualizer |
| `apps/visualizer/app/auth/` | New | Páginas login, register, pending |
| `apps/visualizer/lib/supabase/` | New | Cliente Supabase + helpers de auth |
| `apps/visualizer/middleware.ts` | New | Guard de rutas protegidas |
| `services/lidar-server/main.py` | Modified | Auth dual: JWT web + password device |
| `services/lidar-server/` | Modified | R2 upload, scan metadata persistence |
| `supabase/` | New | Schema SQL, migrations, RLS policies |
| `railway.json` / `railway.toml` | New | Deploy config |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| WebSocket JWT handshake complejo | Med | Usar query param `?token=` en WS URL (estándar) |
| R2 CORS en upload directo | Low | Upload via backend Python, no directo desde browser |
| Railway Redis latency vs local | Low | Redis sólo para sesión de escaneo activa |
| Supabase RLS mal configurado expone datos | Med | Revisar con `EXPLAIN` + tests de política |

## Rollback Plan

- Frontend: revertir `app/page.tsx` al visualizer original, quitar middleware.ts
- Backend: quitar validación JWT (env var `AUTH_ENABLED=false`)
- Railway: bajar servicio (datos en Redis son efímeros)
- R2: bucket independiente, no afecta app si falla

## Dependencies

- Supabase project (CLI: `supabase link`)
- Cloudflare R2 bucket + API token
- Railway account + CLI
- Vercel project ya existente (asumido)

## Success Criteria

- [ ] Landing page accesible sin auth en producción
- [ ] Registro crea usuario con `status='pending'`, bloquea acceso hasta aprobación
- [ ] Dispositivo LiDAR con password correcta puede conectar; sin password → rechazado
- [ ] Cliente web autenticado y aprobado puede interactuar con backend
- [ ] Escaneo guardado en R2 con metadata en Supabase
- [ ] Ejemplos públicos visibles sin login; ejemplos privados sólo con auth aprobada
- [ ] Deploy en Railway responde y acepta conexiones WebSocket
