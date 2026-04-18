#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

#include "config.hpp"
#include "device_state_manager.hpp"
#include "scan_controller.hpp"
#include "servo_controller.hpp"
#include "tcp_client.hpp"
#include "wifi_manager.hpp"
#include "uart_utils.hpp"

class PicoScanApplication {
public:
    PicoScanApplication()
        : servo_(CFG_SERVO_PIN)
        , scan_(servo_, tcp_, CFG_UART_ID)
    {
    }

    bool initialize()
    {
        stdio_init_all();

        init_uart();
        servo_.init();

        state_.transition_to(DeviceState::CONNECTING_WIFI);
        if (!init_wifi()) {
            state_.transition_to(DeviceState::ERROR);
            return false;
        }

        state_.transition_to(DeviceState::WIFI_READY);
        state_.transition_to(DeviceState::CONNECTING_CLOUD);
        if (!init_network()) {
            state_.transition_to(DeviceState::ERROR);
            return false;
        }

        state_.transition_to(DeviceState::IDLE);

        ScanParams p;
        p.batch_size = CFG_BATCH_SIZE;
        scan_.set_params(p);

        scan_.start();
        state_.transition_to(DeviceState::SCANNING);

        return true;
    }

    void run()
    {
        while (true) {
            tcp_.poll();

            if (tcp_.is_disconnected()) {
                tcp_.connect_to_server();
                sleep_ms(1000);
                continue;
            }

            if (!tcp_.is_connected()) {
                sleep_ms(10);
                continue;
            }

            scan_.update();
        }
    }

private:
    DeviceStateManager state_;
    ServoController    servo_;
    TCPClient          tcp_;
    ScanController     scan_;

    void init_uart()
    {
        uart_init(CFG_UART_ID, CFG_BAUD_RATE);
        gpio_set_function(CFG_UART_TX_PIN, GPIO_FUNC_UART);
        gpio_set_function(CFG_UART_RX_PIN, GPIO_FUNC_UART);
        uart_set_format(CFG_UART_ID, 8, 1, UART_PARITY_NONE);
        uart_clear_buffer(CFG_UART_ID);
    }

    bool init_wifi()
    {
        if (!WiFiManager::initialize(CFG_WIFI_COUNTRY)) {
            printf("[wifi] init failed\n");
            return false;
        }
        if (!WiFiManager::connect(CFG_WIFI_SSID, CFG_WIFI_PASS, 10000)) {
            printf("[wifi] connect failed\n");
            return false;
        }
        return true;
    }

    bool init_network()
    {
        tcp_.set_server_address(CFG_TCP_IP, CFG_TCP_PORT);
        printf("[net] connecting to %s:%u\n", CFG_TCP_IP, CFG_TCP_PORT);
        return tcp_.connect_to_server() != ERR_ABRT;
    }
};

int main()
{
    PicoScanApplication app;

    if (!app.initialize()) {
        printf("[main] init failed\n");
        return 1;
    }

    app.run();
    return 0;
}
