# Validación rápida main vs feature

## Artefactos persistentes

- **Firmware serial**: `tools/validation/runs/<timestamp>_<branch>_<commit>/`
  - `metadata.json`
  - `validation_stats.jsonl`
  - `summary.json`
- **Backend**: `services/lidar-server/validation_runs/run_<timestamp>_pid*/`
  - `metadata.json`
  - `events.jsonl`
  - `snapshots.jsonl`
  - `summary.json`

## Captura serial

```bash
python tools/validation/capture_validation_stats.py --port /dev/tty.usbmodemXXXX
```

El cronómetro **arranca recién cuando llega el primer `VALIDATION_STATS`**, así no contaminar la comparación con el tiempo muerto antes de que el firmware empiece a emitir.

Por default la consola muestra una barra de progreso con objetivo de **5 minutos**. Podés cambiarlo con `--target-duration-seconds`.

Opcionalmente podés cambiar baudrate o directorio base:

```bash
python tools/validation/capture_validation_stats.py \
  --port /dev/tty.usbmodemXXXX \
  --baud 230400 \
  --target-duration-seconds 300 \
  --output-dir /tmp/picoscan-validation
```

En el `summary.json` de cada corrida también quedan persistidos:

- `first_data_at`
- `elapsed_from_first_data_seconds`
- `target_duration_seconds`

## Lectura rápida

- Todas las líneas relevantes del firmware salen con prefijo `VALIDATION_STATS `.
- El backend persiste snapshots periódicos y summary final aunque no mires la consola.
- Para comparar branches, repetí la misma corrida sobre `main` y sobre tu feature branch, y luego compará los JSON/JSONL generados.
