# Storage Specification

## Purpose

Persistencia de escaneos en Cloudflare R2 y biblioteca de ejemplos en Supabase.

## Requirements

### Requirement: Scan Cloud Save

El sistema MUST permitir a usuarios autenticados guardar el escaneo activo. El escaneo MUST subirse a R2 como `scans/{uuid}.json` y registrarse en la tabla `scans` con metadata.

#### Scenario: Save scan

- GIVEN usuario aprobado con puntos en el visualizer
- WHEN presiona "Guardar escaneo"
- THEN el JSON de puntos se sube a R2 y se crea registro en `scans` con `{user_id, r2_url, point_count, points_per_second, duration_seconds, created_at}`

#### Scenario: Save scan without auth

- GIVEN un usuario no autenticado
- WHEN intenta guardar
- THEN la acción es bloqueada con mensaje "Requiere cuenta aprobada"

### Requirement: Examples Library

La tabla `examples` MUST existir con campos `{id, name, description, r2_url, is_public, created_at}`. Las RLS policies MUST permitir lectura de ejemplos `is_public=true` a anónimos y todos los ejemplos a usuarios aprobados.

#### Scenario: Public user loads examples

- GIVEN visitante sin sesión
- WHEN carga la biblioteca de ejemplos
- THEN sólo ve ejemplos con `is_public=true`

#### Scenario: Approved user loads examples

- GIVEN usuario con `status='approved'`
- WHEN carga la biblioteca
- THEN ve todos los ejemplos (públicos y privados)

#### Scenario: Unauthorized insert

- GIVEN cualquier usuario web (público o autenticado)
- WHEN intenta INSERT/UPDATE/DELETE en `examples`
- THEN Supabase RLS rechaza la operación

### Requirement: RLS Security

MUST habilitar Row Level Security en todas las tablas (`profiles`, `scans`, `examples`). Usuarios MUST sólo leer/escribir sus propios registros en `scans`. `profiles` MUST ser leído sólo por el propio usuario y el service role.

#### Scenario: User reads another's scan

- GIVEN usuario A autenticado
- WHEN consulta `scans` de usuario B
- THEN RLS retorna 0 filas
