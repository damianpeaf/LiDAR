#include <stdio.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

// Configuración UART
#define UART_ID uart1
#define BAUD_RATE 230400
#define UART_TX_PIN 8
#define UART_RX_PIN 9

// Constantes LIDAR
#define HEADER 0x54
#define POINT_PER_PACK 12
#define FRAME_SIZE 47

// Tabla CRC
static const uint8_t CRC_TABLE[256] = {
    0x00, 0x4d, 0x9a, 0xd7, 0x79, 0x34, 0xe3, 0xae, 0xf2, 0xbf, 0x68, 0x25, 0x8b, 0xc6, 0x11, 0x5c,
    0xa9, 0xe4, 0x33, 0x7e, 0xd0, 0x9d, 0x4a, 0x07, 0x5b, 0x16, 0xc1, 0x8c, 0x22, 0x6f, 0xb8, 0xf5,
    0x1f, 0x52, 0x85, 0xc8, 0x66, 0x2b, 0xfc, 0xb1, 0xed, 0xa0, 0x77, 0x3a, 0x94, 0xd9, 0x0e, 0x43,
    0xb6, 0xfb, 0x2c, 0x61, 0xcf, 0x82, 0x55, 0x18, 0x44, 0x09, 0xde, 0x93, 0x3d, 0x70, 0xa7, 0xea,
    0x3e, 0x73, 0xa4, 0xe9, 0x47, 0x0a, 0xdd, 0x90, 0xcc, 0x81, 0x56, 0x1b, 0xb5, 0xf8, 0x2f, 0x62,
    0x97, 0xda, 0x0d, 0x40, 0xee, 0xa3, 0x74, 0x39, 0x65, 0x28, 0xff, 0xb2, 0x1c, 0x51, 0x86, 0xcb,
    0x21, 0x6c, 0xbb, 0xf6, 0x58, 0x15, 0xc2, 0x8f, 0xd3, 0x9e, 0x49, 0x04, 0xaa, 0xe7, 0x30, 0x7d,
    0x88, 0xc5, 0x12, 0x5f, 0xf1, 0xbc, 0x6b, 0x26, 0x7a, 0x37, 0xe0, 0xad, 0x03, 0x4e, 0x99, 0xd4,
    0x7c, 0x31, 0xe6, 0xab, 0x05, 0x48, 0x9f, 0xd2, 0x8e, 0xc3, 0x14, 0x59, 0xf7, 0xba, 0x6d, 0x20,
    0xd5, 0x98, 0x4f, 0x02, 0xac, 0xe1, 0x36, 0x7b, 0x27, 0x6a, 0xbd, 0xf0, 0x5e, 0x13, 0xc4, 0x89,
    0x63, 0x2e, 0xf9, 0xb4, 0x1a, 0x57, 0x80, 0xcd, 0x91, 0xdc, 0x0b, 0x46, 0xe8, 0xa5, 0x72, 0x3f,
    0xca, 0x87, 0x50, 0x1d, 0xb3, 0xfe, 0x29, 0x64, 0x38, 0x75, 0xa2, 0xef, 0x41, 0x0c, 0xdb, 0x96,
    0x42, 0x0f, 0xd8, 0x95, 0x3b, 0x76, 0xa1, 0xec, 0xb0, 0xfd, 0x2a, 0x67, 0xc9, 0x84, 0x53, 0x1e,
    0xeb, 0xa6, 0x71, 0x3c, 0x92, 0xdf, 0x08, 0x45, 0x19, 0x54, 0x83, 0xce, 0x60, 0x2d, 0xfa, 0xb7,
    0x5d, 0x10, 0xc7, 0x8a, 0x24, 0x69, 0xbe, 0xf3, 0xaf, 0xe2, 0x35, 0x78, 0xd6, 0x9b, 0x4c, 0x01,
    0xf4, 0xb9, 0x6e, 0x23, 0x8d, 0xc0, 0x17, 0x5a, 0x06, 0x4b, 0x9c, 0xd1, 0x7f, 0x32, 0xe5, 0xa8};

// Estructura para un punto LIDAR
typedef struct
{
    float angle;
    uint16_t distance;
    uint8_t intensity;
    bool valid;
} lidar_point_t;

// Función para calcular CRC8
uint8_t calc_crc8(const uint8_t *data, size_t len)
{
    uint8_t crc = 0;
    for (size_t i = 0; i < len; i++)
    {
        crc = CRC_TABLE[(crc ^ data[i]) & 0xff];
    }
    return crc;
}

// Función para normalizar ángulo
float normalize_angle(float angle)
{
    return fmodf(angle / 100.0f, 360.0f);
}

// Función para parsear los puntos del frame
int parse_points(const uint8_t *frame, lidar_point_t *points)
{
    // Verificar CRC
    if (calc_crc8(frame, FRAME_SIZE - 1) != frame[FRAME_SIZE - 1])
    {
        return 0; // CRC inválido
    }

    // Extraer ángulos inicial y final (little endian)
    uint16_t start_angle_raw = (uint16_t)(frame[5] << 8) | frame[4];
    uint16_t end_angle_raw = (uint16_t)(frame[43] << 8) | frame[42];

    float start_angle = start_angle_raw / 100.0f;
    float end_angle = end_angle_raw / 100.0f;

    // Ajustar ángulo final si es menor que el inicial
    if (end_angle < start_angle)
    {
        end_angle += 360.0f;
    }

    // Calcular paso angular
    float step = (end_angle - start_angle) / (POINT_PER_PACK - 1);

    int valid_points = 0;

    // Procesar cada punto
    for (int i = 0; i < POINT_PER_PACK; i++)
    {
        int offset = 6 + i * 3; // Los datos de puntos empiezan en el byte 6

        // Extraer distancia e intensidad (little endian)
        uint16_t distance = (uint16_t)(frame[offset + 1] << 8) | frame[offset];
        uint8_t intensity = frame[offset + 2];

        // Calcular ángulo para este punto
        float angle = fmodf(start_angle + step * i, 360.0f);

        // Solo agregar puntos válidos (distancia > 0)
        if (distance > 0)
        {
            points[valid_points].angle = roundf(angle * 10.0f) / 10.0f; // Redondear a 1 decimal
            points[valid_points].distance = distance;
            points[valid_points].intensity = intensity;
            points[valid_points].valid = true;
            valid_points++;
        }
    }

    return valid_points;
}

// Función para leer un byte del UART con timeout
bool uart_read_byte_timeout(uart_inst_t *uart, uint8_t *byte, uint32_t timeout_ms)
{
    uint32_t start_time = to_ms_since_boot(get_absolute_time());

    while (to_ms_since_boot(get_absolute_time()) - start_time < timeout_ms)
    {
        if (uart_is_readable(uart))
        {
            *byte = uart_getc(uart);
            return true;
        }
        sleep_ms(1);
    }
    return false;
}

// Función para leer múltiples bytes del UART con timeout
bool uart_read_bytes_timeout(uart_inst_t *uart, uint8_t *buffer, size_t len, uint32_t timeout_ms)
{
    for (size_t i = 0; i < len; i++)
    {
        if (!uart_read_byte_timeout(uart, &buffer[i], timeout_ms))
        {
            return false;
        }
    }
    return true;
}

// Función para limpiar el buffer UART
void uart_clear_buffer(uart_inst_t *uart)
{
    while (uart_is_readable(uart))
    {
        uart_getc(uart);
    }
}

int main()
{
    // Inicializar stdio
    stdio_init_all();

    // Configurar UART
    uart_init(UART_ID, BAUD_RATE);

    // Configurar pines GPIO para UART
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    // Configurar formato UART (8 bits de datos, 1 bit de parada, sin paridad)
    uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);

    printf("LIDAR Reader iniciado\n");
    printf("UART configurado: %d baud, TX pin %d, RX pin %d\n", BAUD_RATE, UART_TX_PIN, UART_RX_PIN);

    uint8_t frame[FRAME_SIZE];
    lidar_point_t points[POINT_PER_PACK];

    // Limpiar buffer inicial
    uart_clear_buffer(UART_ID);

    while (true)
    {
        uint8_t byte;

        // Buscar el header
        if (!uart_read_byte_timeout(UART_ID, &byte, 1000))
        {
            continue;
        }

        if (byte != HEADER)
        {
            continue;
        }

        // Leer el resto del frame
        frame[0] = HEADER;
        if (!uart_read_bytes_timeout(UART_ID, &frame[1], FRAME_SIZE - 1, 100))
        {
            printf("Timeout leyendo frame\n");
            continue;
        }

        // Parsear los puntos
        int num_points = parse_points(frame, points);

        if (num_points > 0)
        {
            // Imprimir todos los puntos válidos
            for (int i = 0; i < num_points; i++)
            {
                printf("Ángulo: %.1f°  Distancia: %d mm  Intensidad: %d\n",
                       points[i].angle, points[i].distance, points[i].intensity);
            }
        }

        // Pequeña pausa para no saturar la salida
        sleep_ms(1);
    }

    return 0;
}