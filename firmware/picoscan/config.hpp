#pragma once

// ── Hardware (no persistido — fijo por diseño de PCB) ─────────────────────────
#include "hardware/uart.h"

#define CFG_UART_ID       uart1
#define CFG_BAUD_RATE     230400
#define CFG_UART_TX_PIN   8
#define CFG_UART_RX_PIN   9
#define CFG_SERVO_PIN     15

// ── Setup en campo ────────────────────────────────────────────────────────────
// GPIO con pull-up interno; mantenlo a GND durante el boot para forzar modo setup.
#define CFG_SETUP_BUTTON_PIN  14
#define CFG_AP_SSID           "PicoScan-Setup"
#define CFG_AP_PASS           "picoscan1"

// ── Defaults de compilación (fallback si no hay config válida en flash) ────────
#define CFG_DEFAULT_WIFI_SSID     "P1"
#define CFG_DEFAULT_WIFI_PASS     "holamundo12346"
#define CFG_DEFAULT_WIFI_COUNTRY  "UK"
#define CFG_DEFAULT_TCP_IP        "10.208.207.87"
#define CFG_DEFAULT_TCP_PORT      3000
#define CFG_DEFAULT_BATCH_SIZE    100
