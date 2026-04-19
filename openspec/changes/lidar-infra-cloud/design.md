# Design: LiDAR Cloud Infrastructure

## Technical Approach

Extender el stack existente (Next.js 15 + Python asyncio websockets + Redis) con auth Supabase, deploy Railway, y storage R2. El backend detecta tipo de cliente por primer mensaje; web clients incluyen JWT en query param del handshake WS.

## Architecture Decisions

| Decision | Choice | Rejected | Rationale |
|----------|--------|----------|-----------|
| WS auth method | `?token=` query param | HTTP headers | Browsers no pueden enviar headers custom en WS handshake |
| Device auth timing | Primer mensaje JSON `{"type":"auth","password":"..."}` | Auth en handshake HTTP | Dispositivos Pico no soportan headers HTTP custom |
| Client detection | Primer mensaje determina tipo (device vs web) | URL paths separados | Minimal change; backward compatible con binario del Pico |
| R2 upload | Backend Python via boto3-compatible S3 | Direct browser upload | Evita exponer R2 credentials al browser; simplifica CORS |
| Supabase client | `@supabase/ssr` con cookies | `@supabase/supabase-js` solo | App Router requiere SSR cookies para session en server components |
| Railway Redis | Plugin nativo Railway | Redis externo | Misma red privada = 0 latencia adicional |
| Examples table | Supabase (no R2) | Solo R2 metadata | RLS nativo + queries estructuradas; R2 sólo tiene el JSON de puntos |

## Data Flow

```
Device (Pico W)                    Python Backend (Railway :3000)
  │                                    │
  ├─ WS connect                        │
  ├─ {"type":"auth","password":"X"} ──→ validate vs DEVICE_PASSWORD env
  ├─ binary batch ─────────────────── → parse → cartesian → Redis + broadcast
  │                                    │
Web Client (Vercel)                   │
  ├─ WS connect: ws://host?token=JWT   │
  │  ─────────────────────────────── → validate JWT via Supabase Admin
  ├─ {"type":"register","client":"web"} → add to web_clients set
  ├─ {"type":"clear_scan"} ──────────→ require auth + approved status
  ├─ {"type":"save_scan"} ────────── → upload R2 + insert scans table
  │                                    │
  └─ recv new_points ←────────────────┘

Supabase DB:
  profiles(id, status)  ← RLS: owner-only read
  scans(id, user_id, r2_url, point_count, pps, duration, created_at)
  examples(id, name, description, r2_url, is_public, created_at)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `apps/visualizer/app/page.tsx` | Modify | Landing page (reemplaza wrapper del visualizer) |
| `apps/visualizer/app/app/page.tsx` | Create | Visualizer movido a `/app` |
| `apps/visualizer/app/auth/login/page.tsx` | Create | Página login |
| `apps/visualizer/app/auth/register/page.tsx` | Create | Página registro |
| `apps/visualizer/app/auth/pending/page.tsx` | Create | Pantalla espera aprobación |
| `apps/visualizer/middleware.ts` | Create | Guard: `/app` requiere sesión; redirige según status |
| `apps/visualizer/lib/supabase/client.ts` | Create | Browser Supabase client |
| `apps/visualizer/lib/supabase/server.ts` | Create | Server Supabase client (SSR cookies) |
| `apps/visualizer/components/useLidar.ts` | Modify | Añadir `?token=` al WS URL; gating de acciones |
| `services/lidar-server/main.py` | Modify | Auth dual + R2 upload + scan metadata |
| `services/lidar-server/requirements.txt` | Modify | Añadir `boto3`, `PyJWT`, `httpx` |
| `supabase/migrations/001_init.sql` | Create | Tables + RLS policies |
| `railway.toml` | Create | Deploy config para Python service |

## Interfaces / Contracts

```python
# Backend: primer mensaje device
{"type": "auth", "password": "<DEVICE_PASSWORD>"}

# Backend: primer mensaje web (+ ?token=JWT en URL)
{"type": "register", "client": "web"}

# Backend: nuevo mensaje de guardar escaneo
{"type": "save_scan"}
# Respuesta: {"type": "save_response", "success": bool, "scan_id": str}
```

```sql
-- profiles (vinculado a auth.users)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved'))
);

-- examples
CREATE TABLE examples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL, description TEXT,
  r2_url TEXT NOT NULL, is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- scans
CREATE TABLE scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users NOT NULL,
  r2_url TEXT NOT NULL, point_count INT,
  points_per_second FLOAT, duration_seconds FLOAT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Manual | Auth flow completo (register → pending → approve → login) | Supabase Studio + browser |
| Manual | Device auth (password correcta/incorrecta) | Script Python de prueba |
| Manual | RLS policies | Queries con `anon` key vs `service_role` key |
| Manual | R2 upload + metadata save | Guardar escaneo y verificar en bucket |

## Migration / Rollout

1. Crear Supabase project → `supabase link` → push migration
2. Crear R2 bucket → configurar CORS policy
3. Deploy Railway (Python + Redis plugin) → configurar env vars
4. Deploy Vercel con nuevas env vars Supabase
5. Verificar conexión E2E antes de anunciar

## Open Questions

- [ ] ¿El JWT de Supabase se verifica con la librería `python-jose` o con una llamada HTTP a Supabase `/auth/v1/user`? (Recomiendo: HTTP call para evitar manejar JWKS localmente)
- [ ] ¿Los ejemplos actuales en `/public/` se migran a R2 manualmente o vía script?
