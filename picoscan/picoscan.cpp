#include <string.h>
#include <math.h>
#include <vector>
#include <cstdlib>
#include <cstdio>

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

#include "lwip/pbuf.h"
#include "lwip/tcp.h"

#include "ws.h"
#include "lidar.hpp"
#include "uart_utils.hpp"

#define TEST_TCP_SERVER_IP "192.168.1.24"
#define TCP_PORT 3000

#define BUF_SIZE 2048

#define TCP_DISCONNECTED 0
#define TCP_CONNECTING 1
#define TCP_CONNECTED 2

#define MAX_QUEUED_POINTS 5000

#define UART_ID uart1
#define BAUD_RATE 230400
#define UART_TX_PIN 8
#define UART_RX_PIN 9

#define SERVO_PIN 15

// Configuración del servo para alta precisión
#define SERVO_MIN_PULSE 500  // Mínimo pulso en microsegundos
#define SERVO_MAX_PULSE 2500 // Máximo pulso en microsegundos
#define SERVO_STEP_SIZE 5    // Paso mínimo en microsegundos (alta resolución)
#define SAMPLES_PER_POSITION 2
#define MIN_POINTS_PER_SAMPLE 5000 // Mínimo de puntos por muestra para considerar una vuelta completa

typedef struct
{
    float angle;
    uint distance;
    uint intensity;
    float servo_angle;
} LidarPointWithServo;

typedef struct TCP_CLIENT_T_
{
    LidarPointWithServo points[MAX_QUEUED_POINTS];
    int points_count;
    struct tcp_pcb *tcp_pcb;
    ip_addr_t remote_addr;
    uint8_t buffer[BUF_SIZE];
    uint8_t rx_buffer[BUF_SIZE];
    int buffer_len;
    int rx_buffer_len;
    int sent_len;
    int connected;
} TCP_CLIENT_T;

uint slice_num;
uint16_t wrap_value;
uint current_servo_pulse = SERVO_MIN_PULSE;
int servo_direction = 1;
int samples_collected_at_position = 0;
int points_in_current_sample = 0;
float last_lidar_angle = -1.0f;
bool waiting_for_complete_rotation = false;

void servo_init(uint gpio_pin)
{
    gpio_set_function(gpio_pin, GPIO_FUNC_PWM);
    slice_num = pwm_gpio_to_slice_num(gpio_pin);

    float clock_div = 40.0f;
    pwm_set_clkdiv(slice_num, clock_div);
    wrap_value = 62500 - 1;
    pwm_set_wrap(slice_num, wrap_value);
    pwm_set_enabled(slice_num, true);
}

float pulse_to_degrees(uint pulse_us)
{
    return (float)(pulse_us - SERVO_MIN_PULSE) * 180.0f / (SERVO_MAX_PULSE - SERVO_MIN_PULSE);
}

void servo_set_pulse_us(uint gpio_pin, uint pulse_us)
{
    uint16_t level = (pulse_us * wrap_value) / 20000;
    pwm_set_gpio_level(gpio_pin, level);
}

// Nueva función para mover el servo al siguiente paso
void move_servo_to_next_position()
{
    current_servo_pulse += servo_direction * SERVO_STEP_SIZE;

    // Cambiar dirección al llegar a los extremos
    if (current_servo_pulse >= SERVO_MAX_PULSE)
    {
        current_servo_pulse = SERVO_MAX_PULSE;
        servo_direction = -1;
    }
    else if (current_servo_pulse <= SERVO_MIN_PULSE)
    {
        current_servo_pulse = SERVO_MIN_PULSE;
        servo_direction = 1;
    }

    servo_set_pulse_us(SERVO_PIN, current_servo_pulse);

    // Reset contadores para la nueva posición
    samples_collected_at_position = 0;
    points_in_current_sample = 0;
    last_lidar_angle = -1.0f;
    waiting_for_complete_rotation = false;

    printf("Servo moved to pulse %d (%.1f degrees), collecting samples...\n",
           current_servo_pulse, pulse_to_degrees(current_servo_pulse));
}

// Función para verificar si hemos completado una vuelta completa del LiDAR
bool check_complete_lidar_rotation(float current_angle)
{
    if (!waiting_for_complete_rotation)
    {
        // Comenzar a esperar una rotación completa
        waiting_for_complete_rotation = true;
        last_lidar_angle = current_angle;
        points_in_current_sample = 1;
        return false;
    }

    points_in_current_sample++;

    // Verificar si hemos dado una vuelta completa (el ángulo ha regresado cerca del inicial)
    if (points_in_current_sample >= MIN_POINTS_PER_SAMPLE)
    {
        float angle_diff = fabs(current_angle - last_lidar_angle);
        // Considerar tanto diferencia pequeña como cruce por 0/360
        if (angle_diff < 10.0f || angle_diff > 350.0f)
        {
            samples_collected_at_position++;
            points_in_current_sample = 0;
            waiting_for_complete_rotation = false;

            printf("Sample %d completed at servo angle %.1f degrees (%d points)\n",
                   samples_collected_at_position, pulse_to_degrees(current_servo_pulse),
                   points_in_current_sample);

            return true;
        }
    }

    return false;
}

// Función para verificar si debemos mover el servo
bool should_move_servo()
{
    return samples_collected_at_position >= SAMPLES_PER_POSITION;
}

static err_t tcp_client_sent(void *arg, struct tcp_pcb *tpcb, u16_t len)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    return ERR_OK;
}

static err_t tcp_client_connected(void *arg, struct tcp_pcb *tpcb, err_t err)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    if (err != ERR_OK)
    {
        printf("Connect failed %d\n", err);
    }

    state->buffer_len = sprintf((char *)state->buffer, "GET / HTTP/1.1\r\nHost: 192.168.1.24:3000\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\nSec-WebSocket-Protocol: chat, superchat\r\nSec-WebSocket-Version: 13\r\n\r\n");
    err = tcp_write(state->tcp_pcb, state->buffer, state->buffer_len, TCP_WRITE_FLAG_COPY);

    state->connected = TCP_CONNECTED;

    printf("Connected\r\n");
    return ERR_OK;
}

static err_t tcp_client_poll(void *arg, struct tcp_pcb *tpcb)
{
    return ERR_OK;
}

static void tcp_client_err(void *arg, err_t err)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    state->connected = TCP_DISCONNECTED;
    if (err != ERR_ABRT)
    {
        printf("tcp_client_err %d\n", err);
    }
}

static err_t tcp_client_close(void *arg)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    err_t err = ERR_OK;
    if (state->tcp_pcb != NULL)
    {
        tcp_arg(state->tcp_pcb, NULL);
        tcp_poll(state->tcp_pcb, NULL, 0);
        tcp_sent(state->tcp_pcb, NULL);
        tcp_recv(state->tcp_pcb, NULL);
        tcp_err(state->tcp_pcb, NULL);
        err = tcp_close(state->tcp_pcb);
        if (err != ERR_OK)
        {
            tcp_abort(state->tcp_pcb);
            err = ERR_ABRT;
        }
        state->tcp_pcb = NULL;
    }
    state->connected = TCP_DISCONNECTED;
    return err;
}

err_t tcp_client_recv(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    if (!p)
    {
    }

    cyw43_arch_lwip_check();
    state->rx_buffer_len = 0;

    if (p == NULL)
    {
        tcp_client_close(arg);
        return ERR_OK;
    }

    if (p->tot_len > 0)
    {
        for (struct pbuf *q = p; q != NULL; q = q->next)
        {
            if ((state->rx_buffer_len + q->len) < BUF_SIZE)
            {
                WebsocketPacketHeader_t header;
                WS::ParsePacket(&header, (char *)q->payload, q->len);
                memcpy(state->rx_buffer + state->rx_buffer_len, (uint8_t *)q->payload + header.start, header.length);
                state->rx_buffer_len += header.length;
            }
        }
        tcp_recved(tpcb, p->tot_len);
    }
    pbuf_free(p);

    return ERR_OK;
}

static err_t connect(void *arg)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;

    if (state->connected != TCP_DISCONNECTED)
        return ERR_OK;

    state->tcp_pcb = tcp_new_ip_type(IP_GET_TYPE(&state->remote_addr));
    if (!state->tcp_pcb)
    {
        return false;
    }

    tcp_arg(state->tcp_pcb, state);
    tcp_poll(state->tcp_pcb, tcp_client_poll, 1);
    tcp_sent(state->tcp_pcb, tcp_client_sent);
    tcp_recv(state->tcp_pcb, tcp_client_recv);
    tcp_err(state->tcp_pcb, tcp_client_err);

    state->buffer_len = 0;
    cyw43_arch_lwip_begin();
    state->connected = TCP_CONNECTING;
    err_t err = tcp_connect(state->tcp_pcb, &state->remote_addr, TCP_PORT, tcp_client_connected);
    cyw43_arch_lwip_end();

    return ERR_ABRT;
}

int main()
{
    stdio_init_all();

    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);

    servo_init(SERVO_PIN);
    servo_set_pulse_us(SERVO_PIN, current_servo_pulse);

    // Inicializar estado del servo
    samples_collected_at_position = 0;
    points_in_current_sample = 0;
    last_lidar_angle = -1.0f;
    waiting_for_complete_rotation = false;

    printf("Starting precise LiDAR scan. Servo at %.1f degrees\n", pulse_to_degrees(current_servo_pulse));

    char ssid[] = "CLARO1_8E2AAB";
    char pass[] = "841qlCREpc";

    if (cyw43_arch_init_with_country(CYW43_COUNTRY_UK))
    {
        printf("failed to initialise\n");
        return 1;
    }

    cyw43_arch_enable_sta_mode();

    if (cyw43_arch_wifi_connect_timeout_ms(ssid, pass, CYW43_AUTH_WPA2_AES_PSK, 10000))
    {
        return 1;
    }

    TCP_CLIENT_T *state = (TCP_CLIENT_T *)calloc(1, sizeof(TCP_CLIENT_T));
    if (!state)
    {
        printf("failed to allocate state\n");
        return false;
    }
    ip4addr_aton(TEST_TCP_SERVER_IP, &state->remote_addr);

    printf("Connecting to %s port %u\n", ip4addr_ntoa(&state->remote_addr), TCP_PORT);
    connect(state);

    static char payload_buffer[BUF_SIZE];
    const int BATCH_SIZE_TO_SEND = 100;

    uint8_t frame[FRAME_SIZE];
    LidarPoint points[POINT_PER_PACK];
    uart_clear_buffer(UART_ID);

    while (true)
    {
        cyw43_arch_poll();

        if (state->connected == TCP_DISCONNECTED)
        {
            connect(state);
            sleep_ms(1000);
            continue;
        }

        if (state->connected != TCP_CONNECTED)
        {
            sleep_ms(10);
            continue;
        }

        if (state->rx_buffer_len)
        {
            state->rx_buffer_len = 0;
        }

        uint8_t byte;
        if (uart_read_byte_timeout(UART_ID, &byte, 1000) && byte == HEADER)
        {
            frame[0] = HEADER;
            if (uart_read_bytes_timeout(UART_ID, &frame[1], FRAME_SIZE - 1, 100))
            {
                int num_points = parse_points(frame, points);
                float current_servo_angle = pulse_to_degrees(current_servo_pulse);

                for (int i = 0; i < num_points; i++)
                {
                    if (points[i].distance <= 0 || points[i].distance > 12000 ||
                        points[i].intensity < 0 || points[i].intensity > 255 ||
                        points[i].angle < 0 || points[i].angle > 360)
                    {
                        continue;
                    }

                    // Verificar rotación completa del LiDAR
                    if (check_complete_lidar_rotation(points[i].angle))
                    {
                        printf("Completed sample %d/%d at servo angle %.1f\n",
                               samples_collected_at_position, SAMPLES_PER_POSITION, current_servo_angle);
                    }

                    if (state->points_count < MAX_QUEUED_POINTS)
                    {
                        state->points[state->points_count].angle = points[i].angle;
                        state->points[state->points_count].distance = points[i].distance;
                        state->points[state->points_count].intensity = points[i].intensity;
                        state->points[state->points_count].servo_angle = current_servo_angle;
                        state->points_count++;
                    }
                }

                // Verificar si debemos mover el servo
                if (should_move_servo())
                {
                    printf("Position complete! Moving servo to next position...\n");
                    move_servo_to_next_position();
                    sleep_ms(200); // Tiempo para estabilizar el servo
                }
            }
        }

        // Enviar datos cuando tengamos suficientes puntos
        if (state->points_count >= BATCH_SIZE_TO_SEND)
        {
            int payload_len = 0;
            int points_in_payload = 0;
            float last_servo_angle = -1.0f;

            for (int i = 0; i < state->points_count; i++)
            {
                if (state->points[i].servo_angle != last_servo_angle)
                {
                    int header_len = snprintf(payload_buffer + payload_len, BUF_SIZE - payload_len, "%.1f|",
                                              state->points[i].servo_angle);
                    if (payload_len + header_len >= BUF_SIZE)
                        break;
                    payload_len += header_len;
                    last_servo_angle = state->points[i].servo_angle;
                }

                int len = snprintf(payload_buffer + payload_len, BUF_SIZE - payload_len, "%u;%u;%.1f;",
                                   state->points[i].distance, state->points[i].intensity, state->points[i].angle);

                if (payload_len + len >= BUF_SIZE)
                {
                    break;
                }
                payload_len += len;
                points_in_payload++;
            }

            if (points_in_payload > 0)
            {
                cyw43_arch_lwip_begin();
                state->buffer_len = WS::BuildPacket((char *)state->buffer, BUF_SIZE, WEBSOCKET_OPCODE_TEXT, payload_buffer, payload_len, 1);
                err_t err = tcp_write(state->tcp_pcb, state->buffer, state->buffer_len, TCP_WRITE_FLAG_COPY);

                if (err == ERR_OK)
                {
                    tcp_output(state->tcp_pcb);
                }
                cyw43_arch_lwip_end();

                if (err == ERR_OK)
                {
                    int remaining = state->points_count - points_in_payload;
                    if (remaining > 0)
                    {
                        memmove(state->points, &state->points[points_in_payload], remaining * sizeof(LidarPointWithServo));
                    }
                    state->points_count = remaining;
                }
            }
        }
    }

    return 0;
}