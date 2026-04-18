#include <cstdio>
#include <cstring>

#include "pico/stdlib.h"
#include "pico/flash.h"
#include "hardware/flash.h"
#include "hardware/sync.h"

#include "config_store.hpp"
#include "config.hpp"

// Último sector de flash — alejado del firmware para minimizar riesgo de colisión
static constexpr uint32_t CONFIG_FLASH_OFFSET =
    PICO_FLASH_SIZE_BYTES - FLASH_SECTOR_SIZE;

// Dirección de lectura en el espacio XIP (memoria mapeada)
static const PersistentConfig *FLASH_CONFIG =
    reinterpret_cast<const PersistentConfig *>(XIP_BASE + CONFIG_FLASH_OFFSET);

// ── CRC-32 (polinomio estándar 0xEDB88320) ───────────────────────────────────

uint32_t ConfigStore::crc32(const void *data, size_t len)
{
    const uint8_t *p = static_cast<const uint8_t *>(data);
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc ^= p[i];
        for (int b = 0; b < 8; b++)
            crc = (crc >> 1) ^ (0xEDB88320u & -(crc & 1u));
    }
    return ~crc;
}

// ── Validación ────────────────────────────────────────────────────────────────

bool ConfigStore::is_valid(const PersistentConfig &cfg)
{
    if (cfg.magic != MAGIC)    return false;
    if (cfg.version != VERSION) return false;
    if (cfg.size != sizeof(PersistentConfig)) return false;

    // Checksum cubre todo excepto el propio campo checksum (últimos 4 bytes)
    size_t cover = sizeof(PersistentConfig) - sizeof(uint32_t);
    uint32_t expected = crc32(&cfg, cover);
    return cfg.checksum == expected;
}

// ── Lectura ───────────────────────────────────────────────────────────────────

bool ConfigStore::load(PersistentConfig &out)
{
    // La flash XIP es directamente legible como memoria
    if (!is_valid(*FLASH_CONFIG)) {
        printf("[config] no valid config in flash\n");
        return false;
    }
    memcpy(&out, FLASH_CONFIG, sizeof(PersistentConfig));
    printf("[config] loaded from flash (v%u)\n", out.version);
    return true;
}

// ── Escritura segura ──────────────────────────────────────────────────────────

struct WriteParams {
    uint32_t offset;
    uint8_t  page[FLASH_PAGE_SIZE];  // primera página (config cabe en 256 bytes)
};

static void __no_inline_not_in_flash_func(do_flash_write)(void *param)
{
    auto *p = static_cast<WriteParams *>(param);
    flash_range_erase(p->offset, FLASH_SECTOR_SIZE);
    flash_range_program(p->offset, p->page, FLASH_PAGE_SIZE);
}

bool ConfigStore::save(const PersistentConfig &cfg)
{
    if (!is_valid(cfg)) {
        printf("[config] refusing to save invalid config\n");
        return false;
    }

    WriteParams params;
    params.offset = CONFIG_FLASH_OFFSET;
    memset(params.page, 0xFF, FLASH_PAGE_SIZE);
    memcpy(params.page, &cfg, sizeof(PersistentConfig));

    // flash_safe_execute pausa el core1 y deshabilita interrupciones durante la escritura
    int rc = flash_safe_execute(do_flash_write, &params, 1000);
    if (rc != PICO_OK) {
        printf("[config] flash_safe_execute failed: %d\n", rc);
        return false;
    }

    printf("[config] saved to flash\n");
    return true;
}

// ── Factory reset ─────────────────────────────────────────────────────────────

struct EraseParams { uint32_t offset; };

static void __no_inline_not_in_flash_func(do_flash_erase)(void *param)
{
    auto *p = static_cast<EraseParams *>(param);
    flash_range_erase(p->offset, FLASH_SECTOR_SIZE);
}

bool ConfigStore::erase()
{
    EraseParams params{ CONFIG_FLASH_OFFSET };
    int rc = flash_safe_execute(do_flash_erase, &params, 1000);
    if (rc != PICO_OK) {
        printf("[config] erase failed: %d\n", rc);
        return false;
    }
    printf("[config] flash erased\n");
    return true;
}

// ── Defaults de compilación ───────────────────────────────────────────────────

void ConfigStore::fill_defaults(PersistentConfig &cfg)
{
    memset(&cfg, 0, sizeof(cfg));
    cfg.magic   = MAGIC;
    cfg.version = VERSION;
    cfg.size    = sizeof(PersistentConfig);

    strncpy(cfg.wifi_ssid,    CFG_DEFAULT_WIFI_SSID,    sizeof(cfg.wifi_ssid)    - 1);
    strncpy(cfg.wifi_pass,    CFG_DEFAULT_WIFI_PASS,    sizeof(cfg.wifi_pass)    - 1);
    strncpy(cfg.wifi_country, CFG_DEFAULT_WIFI_COUNTRY, sizeof(cfg.wifi_country) - 1);
    strncpy(cfg.tcp_ip,       CFG_DEFAULT_TCP_IP,       sizeof(cfg.tcp_ip)       - 1);
    cfg.tcp_port   = CFG_DEFAULT_TCP_PORT;
    cfg.batch_size = CFG_DEFAULT_BATCH_SIZE;

    size_t cover = sizeof(PersistentConfig) - sizeof(uint32_t);
    cfg.checksum = crc32(&cfg, cover);
}
