#pragma once

#include <cstdint>
#include <cstring>

// Estructura persistida en el último sector de flash (4 KB)
struct PersistentConfig {
    // ── Header ────────────────────────────────────────────────────────────────
    uint32_t magic;       // 0x50534346 ('PSCF')
    uint16_t version;     // versión del layout; incrementar al cambiar campos
    uint16_t size;        // sizeof(PersistentConfig), para detección de layout viejo

    // ── WiFi ──────────────────────────────────────────────────────────────────
    char wifi_ssid[64];
    char wifi_pass[64];
    char wifi_country[4]; // código ISO-3166-1 alpha-2, ej. "UK"

    // ── Cloud ─────────────────────────────────────────────────────────────────
    char tcp_ip[40];      // IPv4 o hostname corto
    uint16_t tcp_port;
    char device_pass[64];

    // ── Scan defaults ─────────────────────────────────────────────────────────
    uint16_t batch_size;

    // ── Integridad ────────────────────────────────────────────────────────────
    uint32_t checksum;    // CRC-32 de todos los bytes anteriores
};

static_assert(sizeof(PersistentConfig) <= 256,
              "PersistentConfig debe caber en una página de flash");

class ConfigStore {
public:
    static constexpr uint32_t MAGIC   = 0x50534346u;
    static constexpr uint16_t VERSION = 2;

    // Carga config desde flash. Retorna false si no hay config válida.
    static bool load(PersistentConfig &out);

    // Escribe config en flash de forma segura (erase + program).
    // Bloquea brevemente el core mientras la flash está en escritura.
    static bool save(const PersistentConfig &cfg);

    // Borra el sector de config (factory reset).
    static bool erase();

    // Rellena `cfg` con los defaults de compilación.
    static void fill_defaults(PersistentConfig &cfg);

    static bool is_valid(const PersistentConfig &cfg);

    // Calcula y escribe checksum en cfg (llamar antes de save()).
    static void seal(PersistentConfig &cfg);

private:
    static uint32_t crc32(const void *data, size_t len);
};
