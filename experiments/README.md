# Experiments

Material histórico, pruebas de concepto, implementaciones previas y ramas de exploración.

## Objetivo

Separar claramente la línea principal del trabajo exploratorio sin perder trazabilidad.

## Contenido

- `integration_poc/` — pruebas tempranas en Python / MicroPython
- `integraton_poc/` — POC histórico preservando typo original
- `ld19/` — trabajos previos sobre LD19 y visualización 2D
- `ld19c/` — variante en C para LD19
- `lidar/` — implementación histórica monolítica (device/gui/docker-compose)
- `main/`, `motors_poc/`, `servo_poc/`, `stepper_poc/`, `tf_poc/`, `wstest/` — prototipos específicos

## Regla

Estos directorios se preservan como referencia histórica. La evolución activa ocurre en:

- `../firmware/picoscan`
- `../services/lidar-server`
- `../apps/visualizer`
