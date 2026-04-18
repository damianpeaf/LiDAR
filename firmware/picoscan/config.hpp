#pragma once

// ── Hardware ──────────────────────────────────────────────────────────────────
#include "hardware/uart.h"

#define CFG_UART_ID       uart1
#define CFG_BAUD_RATE     230400
#define CFG_UART_TX_PIN   8
#define CFG_UART_RX_PIN   9
#define CFG_SERVO_PIN     15

// ── Network ───────────────────────────────────────────────────────────────────
#define CFG_WIFI_SSID     "P1"
#define CFG_WIFI_PASS     "holamundo12346"
#define CFG_WIFI_COUNTRY  "UK"
#define CFG_TCP_IP        "10.208.207.87"
#define CFG_TCP_PORT      3000

// ── Scan defaults ─────────────────────────────────────────────────────────────
#define CFG_BATCH_SIZE    100
