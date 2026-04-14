# PicoScan — Master Plan

> Documento maestro único para retomar el proyecto en cualquier momento.
> Consolida contexto del firmware, arquitectura objetivo, RFC de campo, roadmap de performance y estado de avance.

---

## 1. Estado del documento

- **Estado**: activo
- **Fuente de verdad**: este archivo
- **Última actualización conceptual**: roadmap consolidado + avance de servo no bloqueante + UART RX por IRQ/ring buffer + parser incremental LiDAR + cola TX de puntos en ring buffer + rollout inicial de batches binarios coordinados firmware/backend

---

## 2. Propósito del sistema

PicoScan es un firmware para **Raspberry Pi Pico W** que:

- captura datos LiDAR por UART;
- mueve un servo para barrido vertical;
- construye un escaneo 3D por posiciones;
- transmite puntos al backend por red;
- en la arquitectura objetivo, también podrá configurarse y controlarse en campo sin reflashear.

---

## 3. Situación actual resumida

### Lo que ya existe

- lectura de frames LiDAR desde UART;
- parseo y validación básica de puntos;
- control de servo para barrido vertical;
- cliente TCP/WebSocket para transmisión;
- batching de puntos;
- firmware funcional como base de laboratorio.

### Limitaciones actuales

- captura UART todavía simple;
- movimiento del servo con espera bloqueante;
- envío LiDAR en texto, no binario;
- pipeline poco desacoplado entre captura, procesamiento y red;
- configuración de campo todavía no implementada;
- credenciales / servidor históricamente hardcodeados;
- máquina de estados global todavía no formalizada.

---

## 4. Objetivo técnico global

Llegar a un firmware que sea:

- **rápido** en captura y envío;
- **no bloqueante** en sus caminos críticos;
- **robusto** frente a caídas de red y reinicios;
- **configurable en campo** sin recompilar;
- **controlable remotamente**;
- **mantenible** a medida que crezca.

---

## 5. Arquitectura objetivo recomendada

La dirección recomendada es una arquitectura:

### **event-driven + non-blocking + buffered pipeline**

### Componentes objetivo

1. **LiDAR Ingest**
   - UART por IRQ;
   - ring buffer RX;
   - parser incremental de frames.

2. **Scan Controller**
   - coordina adquisición;
   - aplica defaults y overrides runtime;
   - decide cuándo arrancar, pausar, reanudar o detener barridos.

3. **Servo Controller no bloqueante**
   - máquina de estados para movimiento y settling;
   - sin `sleep` en hot path.

4. **Point Pipeline**
   - cola desacoplada de puntos;
   - batching explícito;
   - backpressure.

5. **Cloud Client**
   - WebSocket para control y streaming;
   - control/status en JSON;
   - datos LiDAR en binario.

6. **Config Store**
   - persistencia versionada;
   - validación y checksum;
   - recuperación ante corrupción.

7. **Setup Manager**
   - modo AP;
   - portal HTTP mínimo;
   - onboarding en campo.

8. **Device State Manager**
   - máquina de estados global del equipo.

---

## 6. Principios de diseño

1. **Nada de `sleep` en el hot path**
2. **Captura, servo y red deben estar desacoplados**
3. **Persistente y runtime son conceptos distintos**
4. **Control y datos no deben compartir formato necesariamente**
5. **Toda etapa debe dejar trazabilidad de estado y avance**
6. **Un problema a la vez, con validación antes de pasar al siguiente**

---

## 7. RFC consolidada — configuración y control en campo

### Objetivo de campo

Permitir que el dispositivo:

- se configure sin recompilar;
- opere con redes locales cambiantes, incluido hotspot móvil;
- apunte a servidor cloud configurable;
- reciba comandos remotos;
- exponga parámetros de escaneo configurables;
- sobreviva a reinicios y fallos de red con estados claros.

### Modo operativo deseado

#### Modo Setup
- levanta AP propio si no hay config válida o si se fuerza reconfiguración;
- expone portal web local;
- guarda Wi‑Fi, cloud, identidad y defaults de escaneo.

#### Modo Operación
- conecta a Wi‑Fi configurado;
- conecta a cloud;
- publica estado;
- acepta comandos remotos;
- transmite puntos LiDAR.

### Separación fundamental

#### Configuración persistente
- Wi‑Fi
- cloud
- `device_id`
- token/credenciales del dispositivo
- defaults de escaneo
- parámetros de servicio

#### Runtime
- `scan.start`
- `scan.stop`
- `scan.pause`
- `scan.resume`
- `scan.set_profile`
- `scan.set_params`

### Compatibilidad con la arquitectura objetivo

La arquitectura propuesta en este documento **soporta bien** esta RFC porque:

- el servo no bloqueante permite atender red y comandos mientras se escanea;
- UART desacoplada evita que el manejo de conectividad destruya la adquisición;
- control JSON + datos binarios separan claridad operativa de eficiencia;
- la máquina de estados hace posible setup, operación, pausa, error y recuperación.

---

## 8. Máquina de estados objetivo

### Estado global del dispositivo

- `UNCONFIGURED`
- `SETUP_AP`
- `SETUP_PORTAL`
- `CONFIG_SAVED`
- `CONNECTING_WIFI`
- `WIFI_READY`
- `CONNECTING_CLOUD`
- `IDLE`
- `ERROR`

### Estado del escaneo

- `STOPPED`
- `STARTING`
- `SCANNING`
- `PAUSING`
- `PAUSED`
- `STOPPING`
- `HOMING`

### Regla importante

No mezclar el estado del dispositivo con el del escaneo en una sola enum gigante. Son dos dimensiones distintas.

---

## 9. Estrategia de comunicación recomendada

### Control / estado
- WebSocket con mensajes **JSON**
- útil para:
  - comandos;
  - estado;
  - errores;
  - diagnóstico.

### Datos LiDAR
- WebSocket con frames **binarios**
- útil para:
  - menor uso de CPU;
  - menor ancho de banda;
  - menor latencia;
  - formato más estable para batches.

---

## 10. Roadmap maestro por etapas

## Etapa 0 — saneamiento inicial

### Objetivo
Tener una base mínima más razonable sin rediseñar todo de golpe.

### Estado
- **en progreso**

### Checklist
- [x] documentar cuello de botella inicial
- [x] consolidar roadmap en documento maestro único
- [x] atacar primer P0 de UART

---

## Etapa 1 — performance del core

### Objetivo
Eliminar bloqueos gruesos y preparar un pipeline más sano.

### Estado
- **en progreso**

### Subetapas

#### 1.1 UART / ingestión
- [x] revisar `uart_read_byte_timeout()` y `uart_read_bytes_timeout()`
- [x] eliminar polling grueso con `sleep_ms(1)`
- [x] cambiar timeout por frame en lectura múltiple
- [ ] validar en hardware integridad de frames de 47 bytes
- [x] evolucionar a UART por IRQ + ring buffer
- [x] introducir parser incremental

#### 1.2 Servo / movimiento no bloqueante
- [x] eliminar `sleep_ms(200)` después del movimiento
- [x] introducir máquina de estados mínima del servo
- [x] definir settling sin bloquear el loop principal
- [ ] verificar en hardware que no se pierdan puntos durante transición

#### 1.3 Pipeline de puntos
- [ ] separar captura de transmisión
- [ ] introducir cola desacoplada de puntos
- [ ] definir política de backpressure

#### 1.4 Payload y envío
- [x] documentar payload textual actual
- [x] diseñar payload binario
- [x] migrar ángulos a enteros escalados
- [x] adaptar backend receptor
- [ ] validar interoperabilidad real firmware → backend con frames binarios
- [ ] confirmar coexistencia rollout texto/binario con captura real

#### 1.5 Buffering interno
- [x] reemplazar cola lineal + `memmove` por ring buffer
- [ ] validar comportamiento con backlog de red

#### 1.6 Afinado del hot path
- [x] chequear handshake completo antes de enviar datos LiDAR
- [ ] reducir `printf` en hot path
- [x] fijar política explícita de batching / flush

---

## Etapa 2 — arquitectura limpia para crecer

### Objetivo
Preparar el firmware para soportar operación de campo y control remoto sin mezclar responsabilidades.

### Estado
- **pendiente**

### Checklist
- [ ] introducir `scan_controller`
- [ ] separar config/defaults de runtime overrides
- [ ] extraer parámetros hardcodeados del flujo principal
- [ ] introducir `device_state_manager`
- [ ] definir interfaces entre adquisición, servo, cloud y control

---

## Etapa 3 — configuración persistente

### Objetivo
Eliminar dependencia de recompilación para Wi‑Fi, cloud y defaults.

### Estado
- **pendiente**

### Checklist
- [ ] definir estructura persistente versionada
- [ ] agregar validación mínima de config
- [ ] agregar checksum / integridad
- [ ] implementar lectura segura al boot
- [ ] implementar escritura segura/atómica
- [ ] eliminar credenciales y servidor hardcodeados del flujo principal

---

## Etapa 4 — setup en campo

### Objetivo
Permitir onboarding sin reflashear.

### Estado
- **pendiente**

### Checklist
- [ ] modo AP de setup
- [ ] portal HTTP mínimo
- [ ] formulario de configuración
- [ ] persistencia desde portal
- [ ] mecanismo físico para volver a setup
- [ ] endpoint local de diagnóstico básico

---

## Etapa 5 — máquina de estados y observabilidad

### Objetivo
Hacer el sistema entendible y operable en campo.

### Estado
- **pendiente**

### Checklist
- [ ] centralizar estado global del dispositivo
- [ ] centralizar estado del escaneo
- [ ] reportar estado local y remoto
- [ ] exponer errores distinguibles
- [ ] agregar métricas mínimas:
  - [ ] puntos recibidos
  - [ ] puntos enviados
  - [ ] puntos descartados
  - [ ] máximo backlog
  - [ ] latencia de envío estimada

---

## Etapa 6 — control remoto

### Objetivo
Permitir operación desde backend.

### Estado
- **pendiente**

### Checklist
- [ ] `scan.start`
- [ ] `scan.stop`
- [ ] `scan.pause`
- [ ] `scan.resume`
- [ ] `scan.home_servo`
- [ ] `device.ping`
- [ ] `device.get_status`
- [ ] `device.get_config_summary`
- [ ] `device.enter_setup`
- [ ] `device.factory_reset`

---

## Etapa 7 — perfiles y política operativa

### Objetivo
Permitir uso real en diferentes escenarios de campo.

### Estado
- **pendiente**

### Checklist
- [ ] perfiles predefinidos
- [ ] overrides runtime
- [ ] defaults seguros
- [ ] política offline explícita
- [ ] estrategia ante pérdida de cloud durante escaneo

---

## 11. Estado de avance actual

### Completado
- documento maestro consolidado
- roadmap de performance definido
- compatibilidad con RFC de campo analizada
- mejora inicial P0 de UART implementada:
  - se eliminó `sleep_ms(1)` del polling por byte;
  - la lectura múltiple ahora usa deadline por frame, no por byte.
- mejora inicial de servo no bloqueante implementada:
  - se eliminó el `sleep_ms(200)` posterior al movimiento;
  - el servo ahora entra en estado de `Settling` y luego vuelve a `Sampling` sin bloquear el loop principal;
  - durante settling se drenan frames LiDAR pero no se usan para muestreo.
- mejora estructural de ingestión UART implementada:
  - RX del LiDAR ahora entra por IRQ hacia un ring buffer dedicado;
  - `uart_read_byte_timeout()` y `uart_read_bytes_timeout()` consumen primero desde ese buffer, preservando la API pública;
  - el cambio mantiene el parser actual basado en frames completos para limitar el alcance y el riesgo.
- mejora incremental del parser LiDAR implementada:
  - `process_lidar_data()` ya no depende de header + lectura bloqueante de frame completo;
  - un parser incremental recompone frames de 47 bytes byte a byte desde la fuente UART existente;
  - ante CRC o framing inválido, el parser busca el próximo header dentro del buffer parcial para resincronizar sin vaciar el stream.
- saneamiento mínimo del send path WebSocket implementado:
  - `send_points_batch()` ahora reserva overhead de framing/masking antes de llenar el payload textual;
  - si `WS::BuildPacket()` falla o devuelve longitud inválida, ya no se llama a `tcp_write()`;
  - el envío de datos queda gated por `handshake_complete`, no solo por TCP conectado;
  - los logs de payload lleno ahora indican defer de puntos pendientes en lugar de “dropping point” engañoso;
  - el log de sample completado conserva la cantidad real de puntos antes del reset del contador.
- mejora estructural mínima del backlog TX implementada:
  - la cola interna de puntos pasó de arreglo lineal con `memmove()` a ring buffer, preservando la API pública de `TCPClient`;
  - al confirmar un envío exitoso solo se avanza el head lógico de la cola, evitando copias O(n) por batch;
  - el loop principal ahora intenta drenar múltiples batches consecutivos mientras haya backlog suficiente y `tcp_write()` siga aceptando datos.
- migración incremental inicial a batches binarios coordinados implementada:
  - el firmware ahora agrupa envíos por ángulo de servo y arma frames WebSocket binarios compactos;
  - cada batch lleva un header explícito (`magic` + `version` + `servo_angle_tenths` + `point_count`) y luego records compactos por punto sin repetir inclinación;
  - los ángulos transmitidos pasaron a escala entera en décimas para bajar costo de serialización y evitar padding implícito de structs C;
  - el backend ahora detecta `bytes` vs `str` antes de `json.loads`, mantiene la ruta legacy de texto y parsea el nuevo formato binario hacia la misma representación interna/JSON existente para browser.

### En progreso
- transición desde firmware lineal a firmware más desacoplado

### Pendiente crítico inmediato
- validar en hardware integridad de frames con RX por IRQ + ring buffer
- validar en hardware la nueva estrategia de settling del servo
- validar en hardware el comportamiento del nuevo ring buffer TX bajo backlog sostenido
- validar en hardware el rollout de frames binarios y medir mejora real de CPU/ancho de banda
- confirmar con captura real que el backend mantiene compatibilidad simultánea con payload legacy textual y nuevo payload binario
- reducir `printf` del hot path y definir política clara de flush/backlog ante red inestable

---

## 12. Riesgos principales

1. **Complejidad creciente**
   - la arquitectura correcta agrega piezas, pero evita un firmware inmanejable.

2. **Optimizar sin medir en hardware**
   - las decisiones deben validarse con pruebas reales.

3. **Mezclar demasiadas migraciones juntas**
   - por eso el plan está secuenciado.

4. **Persistencia mal diseñada**
   - puede introducir corrupción y problemas de campo.

5. **Control remoto sin estados claros**
   - vuelve caótica la operación en despliegue.

---

## 13. Regla de ejecución del proyecto

Antes de pasar a la siguiente subetapa:

1. implementar el cambio;
2. documentar qué cambió;
3. registrar qué falta validar;
4. revisar si rompe la arquitectura objetivo o la RFC de campo;
5. recién entonces avanzar.

---

## 14. Próximo paso recomendado

### **Atacar continuación de Etapa 1.5/1.6 — validación real del backlog TX + siguiente reducción de costo por payload**

Prioridad inmediata:

- validar en hardware cuánto baja el backlog con la nueva cola TX por ring buffer y el drenaje multi-batch;
- medir si el límite ahora pasa a ser capacidad real de `tcp_write()` y/o presión del backlog tras sacar la serialización textual del camino principal;
- si el batch binario valida bien en hardware, recién después avanzar a backpressure explícito con datos medidos.

Ese es el siguiente paso con mejor relación **impacto / riesgo / alineación arquitectónica**.
