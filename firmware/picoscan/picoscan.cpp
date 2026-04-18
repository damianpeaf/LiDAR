#include <cstdio>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"
#include "hardware/watchdog.h"

#include "config.hpp"
#include "config_store.hpp"
#include "device_state_manager.hpp"
#include "setup_manager.hpp"
#include "scan_controller.hpp"
#include "servo_controller.hpp"
#include "tcp_client.hpp"
#include "wifi_manager.hpp"
#include "uart_utils.hpp"

// ── Detección del botón de setup ──────────────────────────────────────────────

static bool is_setup_forced()
{
    gpio_init(CFG_SETUP_BUTTON_PIN);
    gpio_set_dir(CFG_SETUP_BUTTON_PIN, GPIO_IN);
    gpio_pull_up(CFG_SETUP_BUTTON_PIN);
    sleep_ms(10);
    return !gpio_get(CFG_SETUP_BUTTON_PIN);  // activo en bajo
}

// ── Aplicación principal ──────────────────────────────────────────────────────

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
        // Espera hasta 3s a que el host abra el puerto serial USB
        for (int i = 0; i < 30 && !stdio_usb_connected(); i++) sleep_ms(100);

        bool forced  = is_setup_forced();
        bool has_cfg = ConfigStore::load(cfg_);

        if (forced || !has_cfg) {
            run_setup();
            // run_setup() retorna cuando el usuario guardó config.
            // Reiniciamos para arrancar en modo operación limpio.
            printf("[main] reiniciando...\n");
            watchdog_enable(500, 1);
            while (true) tight_loop_contents();
        }

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
        p.batch_size = cfg_.batch_size;
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
    PersistentConfig   cfg_;
    DeviceStateManager state_;
    ServoController    servo_;
    TCPClient          tcp_;
    ScanController     scan_;

    void run_setup()
    {
        // cyw43 debe estar inicializado antes de levantar el AP
        if (!WiFiManager::initialize(CFG_DEFAULT_WIFI_COUNTRY)) {
            printf("[setup] cyw43 init failed\n");
            return;
        }
        state_.transition_to(DeviceState::SETUP_AP);
        SetupManager setup;
        setup.run(cfg_);
        state_.transition_to(DeviceState::SETUP_PORTAL);
    }

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
        if (!WiFiManager::initialize(cfg_.wifi_country)) {
            printf("[wifi] init failed\n");
            return false;
        }
        if (!WiFiManager::connect(cfg_.wifi_ssid, cfg_.wifi_pass, 10000)) {
            printf("[wifi] connect failed\n");
            return false;
        }
        return true;
    }

    bool init_network()
    {
        tcp_.set_server_address(cfg_.tcp_ip, cfg_.tcp_port);
        printf("[net] connecting to %s:%u\n", cfg_.tcp_ip, cfg_.tcp_port);
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
