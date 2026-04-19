# Auth Specification

## Purpose

Control de acceso en dos capas: clientes web via Supabase Auth, dispositivos LiDAR via password configurable.

## Requirements

### Requirement: User Registration with Waitlist

El sistema MUST crear un perfil con `status='pending'` al registrarse. El usuario MUST NOT poder acceder a funciones autenticadas hasta que el admin cambie `status='approved'` en Supabase Studio.

#### Scenario: Successful registration

- GIVEN un email válido no registrado
- WHEN el usuario completa el formulario de registro
- THEN se crea una cuenta en Supabase Auth Y un registro en `profiles` con `status='pending'`
- AND se muestra la página "pendiente de aprobación"

#### Scenario: Login while pending

- GIVEN un usuario registrado con `status='pending'`
- WHEN intenta hacer login con credenciales válidas
- THEN ve una pantalla informando que aún no fue habilitado

#### Scenario: Login after approval

- GIVEN un usuario con `status='approved'`
- WHEN hace login con credenciales válidas
- THEN es redirigido a `/app` con acceso completo

### Requirement: Web Client JWT Validation

El backend Python MUST validar el JWT de Supabase enviado como query param `?token=` en el handshake WebSocket. Solicitudes sin token válido MUST NOT acceder a operaciones que afectan el backend.

#### Scenario: Authenticated web client connects

- GIVEN un JWT válido de un usuario `approved`
- WHEN el cliente se conecta al WebSocket con `?token={jwt}`
- THEN la conexión es aceptada y se permite operar

#### Scenario: Unauthenticated connection attempt

- GIVEN una conexión WebSocket sin token o con token inválido
- WHEN intenta enviar un comando (`clear_scan`, `connect`)
- THEN el servidor rechaza el comando con error `401`

### Requirement: Device Password Authentication

El backend MUST aceptar conexiones de dispositivos LiDAR sólo si el primer mensaje contiene la password que coincide con `DEVICE_PASSWORD` env var.

#### Scenario: Device with correct password

- GIVEN `DEVICE_PASSWORD=abc123` en el servidor
- WHEN el dispositivo envía `{"type":"auth","password":"abc123"}` como primer mensaje
- THEN la conexión es aceptada y se procesan datos de escaneo

#### Scenario: Device with wrong password

- GIVEN cualquier password incorrecta o ausente
- WHEN el dispositivo intenta autenticarse
- THEN el servidor cierra la conexión inmediatamente
