#ifndef WIFI_MANAGER_HPP
#define WIFI_MANAGER_HPP

#include "pico/cyw43_arch.h"

class WiFiManager
{
public:
    static bool initialize(const char* country = "UK");
    static bool connect(const char* ssid, const char* password, uint32_t timeout_ms = 10000);
    static void disconnect();
    static bool is_connected();
};

#endif // WIFI_MANAGER_HPP