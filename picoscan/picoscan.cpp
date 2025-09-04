#include <cstdio>
#include <cstring>

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

#include "lidar.hpp"
#include "uart_utils.hpp"
#include "servo_controller.hpp"
#include "tcp_client.hpp"
#include "wifi_manager.hpp"

#define UART_ID uart1
#define BAUD_RATE 230400
#define UART_TX_PIN 8
#define UART_RX_PIN 9
#define SERVO_PIN 15

#define TCP_SERVER_IP "192.168.1.24"
#define TCP_PORT 3000
#define BATCH_SIZE_TO_SEND 100

class PicoScanApplication
{
private:
    ServoController servo;
    TCPClient tcp_client;

    void init_uart()
    {
        uart_init(UART_ID, BAUD_RATE);
        gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
        gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
        uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);
        uart_clear_buffer(UART_ID);
    }

    bool init_wifi()
    {
        const char ssid[] = "CLARO1_8E2AAB";
        const char pass[] = "841qlCREpc";

        if (!WiFiManager::initialize("UK"))
        {
            printf("Failed to initialize WiFi\n");
            return false;
        }

        if (!WiFiManager::connect(ssid, pass, 10000))
        {
            printf("Failed to connect to WiFi\n");
            return false;
        }

        return true;
    }

    bool init_network()
    {
        tcp_client.set_server_address(TCP_SERVER_IP, TCP_PORT);
        printf("Connecting to %s port %u\n", TCP_SERVER_IP, TCP_PORT);
        return tcp_client.connect_to_server() != ERR_ABRT;
    }

    void handle_connection()
    {
        if (tcp_client.is_disconnected())
        {
            tcp_client.connect_to_server();
            sleep_ms(1000);
        }
    }

    void process_lidar_data()
    {
        uint8_t frame[FRAME_SIZE];
        LidarPoint points[POINT_PER_PACK];

        uint8_t byte;
        if (uart_read_byte_timeout(UART_ID, &byte, 1000) && byte == HEADER)
        {
            frame[0] = HEADER;
            if (uart_read_bytes_timeout(UART_ID, &frame[1], FRAME_SIZE - 1, 100))
            {
                int num_points = parse_points(frame, points);
                float current_servo_angle = servo.get_current_angle();

                for (int i = 0; i < num_points; i++)
                {
                    if (points[i].distance <= 0 || points[i].distance > 12000 ||
                        points[i].intensity < 0 || points[i].intensity > 255 ||
                        points[i].angle < 0 || points[i].angle > 360)
                    {
                        continue;
                    }

                    if (servo.check_complete_lidar_rotation(points[i].angle))
                    {
                        printf("Completed sample at servo angle %.1f\n", current_servo_angle);
                    }

                    tcp_client.add_point(points[i].angle, points[i].distance,
                                         points[i].intensity, current_servo_angle);
                }

                if (servo.should_move_servo())
                {
                    printf("Position complete! Moving servo to next position...\n");
                    servo.move_to_next_position();
                    sleep_ms(200);
                }
            }
        }
    }

    void handle_data_transmission()
    {
        if (tcp_client.get_points_count() >= BATCH_SIZE_TO_SEND)
        {
            tcp_client.send_points_batch(BATCH_SIZE_TO_SEND);
        }
    }

public:
    PicoScanApplication() : servo(SERVO_PIN)
    {
    }

    bool initialize()
    {
        stdio_init_all();

        init_uart();
        servo.init();

        printf("Starting precise LiDAR scan. Servo at %.1f degrees\n", servo.get_current_angle());

        if (!init_wifi())
        {
            return false;
        }

        if (!init_network())
        {
            return false;
        }

        return true;
    }

    void run()
    {
        while (true)
        {
            tcp_client.poll();
            handle_connection();

            if (!tcp_client.is_connected())
            {
                sleep_ms(10);
                continue;
            }

            // No es necesario limpiar buffer RX - optimizado para solo envío

            process_lidar_data();
            handle_data_transmission();
        }
    }
};

int main()
{
    PicoScanApplication app;

    if (!app.initialize())
    {
        printf("Failed to initialize application\n");
        return 1;
    }

    app.run();
    return 0;
}