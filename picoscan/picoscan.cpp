#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"
#include "lidar.hpp"
#include "uart_utils.hpp"
#include "tcp_client.h"

// Configuración UART para LIDAR
#define UART_ID uart1
#define BAUD_RATE 230400
#define UART_TX_PIN 8
#define UART_RX_PIN 9

// Configuración Wi-Fi
#define SSID "CLARO1_8E2AAB"
#define PASS "REMOVED"

int main()
{
    // Inicialización
    stdio_init_all();

    // Inicializar UART para LIDAR
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);

    // Inicializar Wi-Fi
    if (cyw43_arch_init_with_country(CYW43_COUNTRY_MEXICO))
    {
        printf("Failed to initialise Wi-Fi\n");
        return 1;
    }
    cyw43_arch_enable_sta_mode();

    if (cyw43_arch_wifi_connect_timeout_ms(SSID, PASS, CYW43_AUTH_WPA2_AES_PSK, 10000))
    {
        printf("Failed to connect to Wi-Fi\n");
        return 1;
    }

    // Inicializar cliente TCP/WebSocket
    TCP_CLIENT_T *state = tcp_client_init();
    if (!state)
    {
        printf("Failed to initialize TCP client\n");
        return 1;
    }

    printf("Connecting to %s port %u\n", ip4addr_ntoa(&state->remote_addr), TCP_PORT);
    tcp_client_connect(state);

    // Buffers y estructuras para LIDAR
    uint8_t frame[FRAME_SIZE];
    LidarPoint points[POINT_PER_PACK];
    uart_clear_buffer(UART_ID);

    // Buffer para datos recibidos por WebSocket
    char output[BUF_SIZE];
    // Buffer para enviar datos al WebSocket
    char send_buffer[100];

    while (true)
    {
        // Leer datos del WebSocket
        int len = tcp_client_get_rx_data(state, output, BUF_SIZE);
        if (len > 0)
        {
            printf("Received: %.*s\n", len, output);
        }

        // Reconectar si está desconectado
        if (state->connected == TCP_DISCONNECTED)
        {
            printf("Reconnecting to WebSocket...\n");
            tcp_client_connect(state);
        }

        // Leer datos del LIDAR
        uint8_t byte;
        if (uart_read_byte_timeout(UART_ID, &byte, 1000) && byte == HEADER)
        {
            frame[0] = HEADER;
            if (uart_read_bytes_timeout(UART_ID, &frame[1], FRAME_SIZE - 1, 100))
            {
                int num_points = parse_points(frame, points);
                for (int i = 0; i < num_points; i++)
                {

                    if (points[i].distance <= 0 || points[i].distance > 12000 || // Max 12m
                        points[i].intensity < 0 || points[i].intensity > 255 ||
                        points[i].angle < 0 || points[i].angle > 360)
                    {
                        printf("Datos inválidos: Ángulo=%.1f, Distancia=%d, Intensidad=%d\n",
                               points[i].angle, points[i].distance, points[i].intensity);
                        continue;
                    }
                    char send_buffer[100] = {0};

                    // Formatear los datos como "ángulo;distancia;intensidad"
                    snprintf(send_buffer, sizeof(send_buffer), "%.1f;%d;%d",
                             points[i].angle, points[i].distance, points[i].intensity);

                    // Enviar por WebSocket si está conectado
                    if (state->connected == TCP_CONNECTED)
                    {
                        err_t err = tcp_client_send(state, send_buffer, strlen(send_buffer));
                        if (err != ERR_OK)
                        {
                            printf("Failed to send data: %d\n", err);
                        }
                        else
                        {
                            printf("Sent: %s\n", send_buffer);
                        }
                    }
                }
            }
            else
            {
                printf("Timeout reading LIDAR frame\n");
            }
        }
    }

    // Limpieza (nunca se alcanza en este caso)
    tcp_client_deinit(state);
    return 0;
}