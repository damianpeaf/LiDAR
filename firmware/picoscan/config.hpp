#pragma once

// ── Hardware (no persistido — fijo por diseño de PCB) ─────────────────────────
#include "hardware/uart.h"
#include "telemetry.hpp"

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
#define CFG_DEFAULT_WIFI_SSID     "CLARO1_8E2AAB"
#define CFG_DEFAULT_WIFI_PASS     "841qlCREpc"
#define CFG_DEFAULT_WIFI_COUNTRY  "UK"
#define CFG_DEFAULT_TCP_IP        "192.168.1.31"
#define CFG_DEFAULT_TCP_PORT      3000
#define CFG_DEFAULT_BATCH_SIZE    100
#define CFG_USE_COMPILE_TIME_NETWORK_DEFAULTS 1

// ── Telemetría y perfiles experimentales ──────────────────────────────────────
constexpr ExperimentProfile CFG_EXPERIMENT_PROFILE = ExperimentProfile::Scan;
constexpr uint32_t CFG_TELEMETRY_PERIODIC_INTERVAL_MS = 1000;
constexpr uint32_t CFG_BENCHMARK_DURATION_SECONDS = 60;
constexpr uint32_t CFG_PRECISION_TARGET_POINTS = 300;
constexpr uint32_t CFG_TELEMETRY_POINT_STRIDE = 1;
constexpr float CFG_PRECISION_ANGLE_CENTER_DEG = 180.0f;
constexpr float CFG_PRECISION_ANGLE_HALF_WIDTH_DEG = 5.0f;

// ── Escaneo 3D objeto referencia ──────────────────────────────────────────────
constexpr bool CFG_SCAN_EMIT_POINT_EVENTS = true;
constexpr float CFG_SCAN_ANGLE_CENTER_DEG = 187.5f;
constexpr float CFG_SCAN_ANGLE_HALF_WIDTH_DEG = 7.5f;
constexpr float CFG_SCAN_SERVO_MIN_DEG = 0.0f;
constexpr float CFG_SCAN_SERVO_MAX_DEG = 30.0f;
constexpr uint32_t CFG_SCAN_TARGET_SWEEP_PASSES = 5;
