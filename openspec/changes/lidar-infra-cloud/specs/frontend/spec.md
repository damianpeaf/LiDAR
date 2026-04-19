# Frontend Specification

## Purpose

Estructura de rutas Next.js con landing pública, visualizer y páginas de auth.

## Requirements

### Requirement: Public Landing Page

La ruta `/` MUST ser accesible sin autenticación. MUST explicar el proyecto, mostrar enlace a ejemplos y opciones de login/registro.

#### Scenario: Unauthenticated visitor

- GIVEN un visitante sin sesión
- WHEN navega a `/`
- THEN ve la landing con descripción del proyecto, CTA a ejemplos y botones Login/Register

#### Scenario: Authenticated user visits landing

- GIVEN usuario con sesión activa
- WHEN navega a `/`
- THEN ve la landing con botón "Ir al Visualizer" en lugar de Login/Register

### Requirement: Protected Visualizer Route

La ruta `/app` MUST redirigir a `/auth/login` si no hay sesión. Si hay sesión con `status='pending'`, MUST redirigir a `/auth/pending`.

#### Scenario: Direct access unauthenticated

- GIVEN un visitante sin sesión
- WHEN intenta acceder a `/app`
- THEN es redirigido a `/auth/login`

### Requirement: Public vs Authenticated Visualizer Mode

El visualizer en `/app` MUST mostrar sólo "Cargar ejemplos" en modo público. Las acciones `clear_scan`, `connect`, y cualquier operación WebSocket MUST requerir sesión aprobada.

#### Scenario: Unauthenticated user in visualizer (si llega)

- GIVEN un usuario sin auth que carga `/app` directamente
- WHEN los botones de acción son renderizados
- THEN sólo "Cargar ejemplo" es habilitado; el resto muestra tooltip "Requiere cuenta aprobada"

### Requirement: Auth Pages

El sistema MUST proveer páginas en `/auth/login`, `/auth/register`, `/auth/pending`.

#### Scenario: Register redirects to pending

- GIVEN formulario de registro completado
- WHEN se envía
- THEN se crea el perfil y se redirige a `/auth/pending`
