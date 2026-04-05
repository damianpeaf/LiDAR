#include "wifi_manager.hpp"
#include <cstdio>
#include <cstring>

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
        return false;
    }

    cyw43_arch_enable_sta_mode();
    return true;
}

bool WiFiManager::connect(const char* ssid, const char* password, uint32_t timeout_ms)
{
    printf("Connecting to WiFi: %s\n", ssid);
    
    if (cyw43_arch_wifi_connect_timeout_ms(ssid, password, CYW43_AUTH_WPA2_AES_PSK, timeout_ms))
    {
        printf("Failed to connect to WiFi\n");
        return false;
    }

    printf("Successfully connected to WiFi\n");
    return true;
}

void WiFiManager::disconnect()
{
    cyw43_arch_deinit();
}

bool WiFiManager::is_connected()
{
    return cyw43_wifi_link_status(&cyw43_state, CYW43_ITF_STA) == CYW43_LINK_UP;
}