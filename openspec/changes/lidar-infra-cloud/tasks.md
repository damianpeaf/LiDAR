# Tasks: LiDAR Cloud Infrastructure

## Phase 1: External Services Setup

- [ ] 1.1 Crear Supabase project: `supabase init` + `supabase link --project-ref <ref>`
- [ ] 1.2 Crear `supabase/migrations/001_init.sql` con tablas `profiles`, `scans`, `examples` + RLS policies + trigger auto-insert profile en signup
- [ ] 1.3 Ejecutar `supabase db push` y verificar tablas en Supabase Studio
- [ ] 1.4 Crear bucket R2 en Cloudflare, habilitar acceso público para `examples/*`, privado para `scans/*`
- [ ] 1.5 Crear Railway project, agregar Redis plugin, configurar env vars del backend (`REDIS_URL`, `DEVICE_PASSWORD`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `R2_*`)
- [ ] 1.6 Instalar paquetes frontend: `@supabase/ssr @supabase/supabase-js` en `apps/visualizer`
- [ ] 1.7 Añadir a `services/lidar-server/requirements.txt`: `boto3`, `httpx`, `python-jose[cryptography]`

## Phase 2: Backend Auth + R2

- [ ] 2.1 Modificar `services/lidar-server/main.py`: extraer `?token=` del path de handshake y validar JWT via `GET /auth/v1/user` de Supabase con `Authorization: Bearer <token>`
- [ ] 2.2 Implementar autenticación de dispositivo: si primer mensaje es `{"type":"auth","password":"X"}`, comparar con `DEVICE_PASSWORD` env var; cerrar conexión si falla
- [ ] 2.3 Agregar estado `authenticated_web_clients: dict[ws, user_id]` y verificar auth antes de procesar `clear_scan`
- [ ] 2.4 Implementar `save_scan_to_r2(points, user_id)`: subir JSON a R2 (`boto3` S3-compatible), insertar en tabla `scans` via Supabase REST API
- [ ] 2.5 Manejar nuevo mensaje `{"type":"save_scan"}` en `handle_web_client_message`; responder con `save_response`
- [ ] 2.6 Crear `railway.toml` en raíz del proyecto con config para Python service

## Phase 3: Frontend Auth

- [ ] 3.1 Crear `apps/visualizer/lib/supabase/client.ts` (browser client) y `server.ts` (SSR con cookies)
- [ ] 3.2 Crear `apps/visualizer/middleware.ts`: redirigir `/app/*` a `/auth/login` si no hay sesión; a `/auth/pending` si `status='pending'`
- [ ] 3.3 Crear `apps/visualizer/app/auth/login/page.tsx`: form email+password con `supabase.auth.signInWithPassword`
- [ ] 3.4 Crear `apps/visualizer/app/auth/register/page.tsx`: form signup → `supabase.auth.signUp` → redirect a `/auth/pending`
- [ ] 3.5 Crear `apps/visualizer/app/auth/pending/page.tsx`: pantalla informativa con opción de logout

## Phase 4: Frontend Landing + Visualizer

- [ ] 4.1 Mover lógica actual de `app/page.tsx` a `app/app/page.tsx` (nueva ruta `/app`)
- [ ] 4.2 Reescribir `app/page.tsx` como landing: descripción del proyecto, botones Login/Register/Ver ejemplos, CTA al visualizer
- [ ] 4.3 Modificar `components/useLidar.ts`: añadir JWT de sesión Supabase al WS URL (`?token=<jwt>`); deshabilitar `clearScan`, `connect` y `save_scan` si no hay sesión aprobada
- [ ] 4.4 Agregar botón "Guardar escaneo" al visualizer que envía `{"type":"save_scan"}` y muestra `save_response`
- [x] 4.5 Implementar biblioteca de ejemplos: fetch de `supabase.from('examples').select()` con filtro `is_public=true` para anónimos vs todos para aprobados; reemplazar ejemplos hardcodeados actuales

## Phase 5: Env Vars + Deploy

- [ ] 5.1 Configurar env vars en Vercel: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_LIDAR_WS_URL` (URL de Railway)
- [ ] 5.2 Deploy Railway: `railway up` desde `services/lidar-server/`
- [ ] 5.3 Subir ejemplos actuales (archivos en `public/`) a R2 bucket bajo `examples/` e insertar registros en tabla `examples` con `is_public=true`
- [ ] 5.4 Verificar flujo E2E: registro → pending → aprobar en Studio → login → conectar device simulado → guardar escaneo → verificar en R2 + Supabase
