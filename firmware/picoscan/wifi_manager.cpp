#include "wifi_manager.hpp"
#include <cstdio>
#include <cstring>
#include "telemetry.hpp"

bool WiFiManager::initialize(const char* country)
{
    uint32_t country_code = CYW43_COUNTRY_UK;
    
    if (strcmp(country, "US") == 0) {
        country_code = CYW43_COUNTRY_USA;
    } else if (strcmp(country, "UK") == 0) {
        country_code = CYW43_COUNTRY_UK;
    }
    
    if (cyw43_arch_init_with_country(country_code))
    {
        printf("Failed to initialize WiFi\n");
        telemetry::note_wifi_event("init_failed", country);
        return false;
    }

    cyw43_arch_enable_sta_mode();
    telemetry::note_wifi_event("initialized", country);
    return true;
}

bool WiFiManager::connect(const char* ssid, const char* password, uint32_t timeout_ms)
{
    printf("Connecting to WiFi: %s\n", ssid);
    telemetry::note_wifi_event("connect_attempt", ssid);
    
    if (cyw43_arch_wifi_connect_timeout_ms(ssid, password, CYW43_AUTH_WPA2_AES_PSK, timeout_ms))
    {
        printf("Failed to connect to WiFi\n");
        telemetry::note_wifi_event("connect_failed", ssid);
        return false;
    }

    printf("Successfully connected to WiFi\n");
    telemetry::note_wifi_event("connected", ssid);
    return true;
}

void WiFiManager::disconnect()
{
    cyw43_arch_deinit();
    telemetry::note_wifi_event("deinitialized");
}

bool WiFiManager::is_connected()
{
    return cyw43_wifi_link_status(&cyw43_state, CYW43_ITF_STA) == CYW43_LINK_UP;
}
