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
#include "telemetry.hpp"
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

        TelemetryOptions telemetry_options;
        telemetry_options.profile = CFG_EXPERIMENT_PROFILE;
        telemetry_options.periodic_interval_ms = CFG_TELEMETRY_PERIODIC_INTERVAL_MS;
        if (CFG_EXPERIMENT_PROFILE == ExperimentProfile::Benchmark) {
            telemetry_options.servo_enabled = false;
            telemetry_options.network_enabled = false;
            telemetry_options.target_duration_s = CFG_BENCHMARK_DURATION_SECONDS;
        } else if (CFG_EXPERIMENT_PROFILE == ExperimentProfile::Scan) {
            telemetry_options.target_duration_s = CFG_SCAN_TARGET_DURATION_SECONDS;
        } else if (CFG_EXPERIMENT_PROFILE == ExperimentProfile::Precision) {
            telemetry_options.servo_enabled = false;
            telemetry_options.network_enabled = false;
            telemetry_options.target_point_events = CFG_PRECISION_TARGET_POINTS;
            telemetry_options.point_stride = CFG_TELEMETRY_POINT_STRIDE;
        }

        telemetry::init(telemetry_options);

        bool forced  = is_setup_forced();
        bool has_cfg = ConfigStore::load(cfg_);
        telemetry::note_boot(forced, has_cfg);

        if (forced) {
            run_setup();
            // run_setup() retorna cuando el usuario guardó config.
            // Reiniciamos para arrancar en modo operación limpio.
            printf("[main] reiniciando...\n");
            watchdog_enable(500, 1);
            while (true) tight_loop_contents();
        }

        if (!has_cfg) {
            printf("[config] using compile-time defaults\n");
            ConfigStore::fill_defaults(cfg_);
        }

        if (CFG_USE_COMPILE_TIME_NETWORK_DEFAULTS) {
            printf("[config] overriding network config with compile-time defaults\n");
            ConfigStore::fill_defaults(cfg_);
        }

        init_uart();

        ScanParams p;
        p.batch_size = cfg_.batch_size;

        if (CFG_EXPERIMENT_PROFILE == ExperimentProfile::Scan) {
            p.enable_servo = true;
            p.enable_network = true;
            p.emit_point_events = false;
            p.target_duration_s = CFG_SCAN_TARGET_DURATION_SECONDS;
        } else if (CFG_EXPERIMENT_PROFILE == ExperimentProfile::Benchmark) {
            p.enable_servo = false;
            p.enable_network = false;
            p.emit_point_events = false;
            p.target_duration_s = CFG_BENCHMARK_DURATION_SECONDS;
        } else {
            p.enable_servo = false;
            p.enable_network = false;
            p.emit_point_events = true;
            p.filter_point_events_by_angle = true;
            p.point_event_angle_center_deg = CFG_PRECISION_ANGLE_CENTER_DEG;
            p.point_event_angle_half_width_deg = CFG_PRECISION_ANGLE_HALF_WIDTH_DEG;
            p.target_point_events = CFG_PRECISION_TARGET_POINTS;
        }

        telemetry::note_config_loaded(cfg_.wifi_ssid, cfg_.tcp_ip, cfg_.tcp_port, cfg_.batch_size);

        if (p.enable_servo) {
            servo_.init();
        }

        if (p.enable_network) {
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
        } else {
            state_.transition_to(DeviceState::IDLE);
        }

        scan_.set_params(p);

        scan_.start();
        state_.transition_to(DeviceState::SCANNING);

        return true;
    }

    void run()
    {
        while (true) {
            if (scan_.network_enabled()) {
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
            }

            scan_.update();

            if (!scan_.is_running()) {
                sleep_ms(50);
            }
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
        uart_init_rx_irq_ring_buffer(CFG_UART_ID);
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
