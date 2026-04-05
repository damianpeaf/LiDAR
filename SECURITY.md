# Security Policy

## Reporte responsable

Si encontrás una vulnerabilidad o exposición sensible:

1. **No** abras un issue público con detalles explotables.
2. Contactá al mantenedor por un canal privado antes de divulgar.
3. Incluí pasos de reproducción, alcance e impacto.

## Alcance

Especial atención a:

- credenciales o hosts hardcodeados en firmware y servicios
- configuraciones de despliegue
- endpoints WebSocket expuestos
- artefactos históricos que puedan contener datos sensibles

## Nota importante

Este repo preserva material histórico con fines de trazabilidad. La reorganización actual **no reescribe historia git** ni elimina retrospectivamente secretos o datos sensibles ya existentes en commits previos.

Antes de una publicación abierta definitiva, conviene realizar una auditoría manual adicional.
