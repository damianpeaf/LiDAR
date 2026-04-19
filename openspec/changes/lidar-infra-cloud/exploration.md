## Exploration: ejemplos desde Supabase

### Current State
Los “Ejemplos” hoy no salen de Supabase. La UI los define hardcodeados en `apps/visualizer/components/Info.tsx` como items fijos del dropdown, cada uno con un `r2_url` público. Al hacer click, `apps/visualizer/components/useLidar.ts` llama `importFromURL(url)`, que pega contra `GET /api/examples?url=...` en `apps/visualizer/app/api/examples/route.ts`; esa route valida el host permitido y descarga el JSON del R2 para luego cargar los puntos en memoria del visualizer. En paralelo, ya existe la base Supabase para este cambio: `supabase/migrations/001_init.sql` crea `profiles`, `examples` y `scans`, y la policy de `examples` ya resuelve público vs aprobado vía RLS.

### Affected Areas
- `apps/visualizer/components/Info.tsx` — hoy renderiza la biblioteca de ejemplos hardcodeada; debe pasar a renderizar metadata dinámica.
- `apps/visualizer/components/useLidar.ts` — ya conoce sesión/permisos e importa ejemplos por URL; es el mejor lugar para consultar Supabase y exponer la lista al componente.
- `apps/visualizer/app/api/examples/route.ts` — hoy sigue siendo útil como proxy seguro para descargar el JSON real desde `r2_url`.
- `supabase/migrations/001_init.sql` — ya define la tabla `examples` y las RLS policies relevantes; sólo habría que tocarla si se decide agregar campos como orden/display.
- `apps/visualizer/lib/supabase/client.ts` — cliente browser existente para hacer `select()` sobre `examples` respetando RLS.
- `apps/visualizer/public/puntos.json` / `app/api/lidar-data/route.ts` / `lib/actions.ts` — archivo local de compatibilidad; no es la biblioteca de ejemplos y conviene no mezclarlo con este flujo.

### Approaches
1. **Query browser a Supabase + mantener proxy actual de descarga** — pedir metadata de `examples` desde el cliente y seguir cargando el JSON final vía `/api/examples?url=...`.
   - Pros: reutiliza `createClient()`, respeta RLS automáticamente, requiere pocos cambios, mantiene el flujo actual de importación.
   - Cons: necesita estado/loading en UI; el orden visual queda atado a `created_at`/`name` salvo que se agregue un campo específico.
   - Effort: Low

2. **Crear endpoint propio que consulte Supabase y devuelva metadata filtrada** — la UI ya no habla directo con Supabase para ejemplos.
   - Pros: centraliza lógica y shape de respuesta; útil si mañana cambia la fuente o se agregan transforms.
   - Cons: duplica lógica que RLS ya resuelve; si usa service role es fácil filtrar mal y exponer privados; más moving parts.
   - Effort: Medium

### Recommendation
Recomiendo **Approach 1**: consultar `examples` desde el browser con el cliente Supabase existente y dejar `app/api/examples/route.ts` sólo para bajar el JSON del `r2_url`. Y te digo por qué: la policy actual de `examples` ya hace el trabajo fino. Un anónimo con anon key sólo ve `is_public = true`; un usuario autenticado y aprobado ve todo. O sea, si usás `supabase.from('examples').select(...)`, la visibilidad correcta cae “gratis” por RLS. No hace falta meter un backend intermedio para metadata salvo que quieras una capa extra por motivos de producto, no por necesidad técnica.

### Risks
- **Orden/curaduría**: la tabla no tiene `display_order`; pasar de hardcode a DB puede cambiar el orden percibido.
- **Dependencia del host permitido**: si `r2_url` apunta a otro dominio distinto del whitelist actual del proxy, la carga va a fallar.
- **Ambigüedad de fuentes**: `public/puntos.json` es compatibilidad local, no ejemplos; si se mezcla con la migración se va a contaminar el modelo mental.
- **Estado de aprobación duplicado**: hoy `useLidar.ts` ya consulta `profiles`; hay que evitar hacer lógica distinta para UI y para query de ejemplos.

### Ready for Proposal
Yes — la implementación está clara. Lo único a definir antes de tocar schema es si alcanza con ordenar por `created_at`/`name` o si querés agregar un campo explícito de orden para preservar la curaduría actual del dropdown.
