#ifndef TCP_CLIENT_H
#define TCP_CLIENT_H

#include <string.h>
#include <math.h>
#include <vector>
#include <cstdlib>

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "ws.h"

#define TEST_TCP_SERVER_IP "192.168.1.24"
#define TCP_PORT 3000
#define BUF_SIZE 8192
#define SEND_BUFFER_SIZE 16384  // Buffer mucho más grande para acumular datos
#define TCP_DISCONNECTED 0
#define TCP_CONNECTING 1
#define TCP_CONNECTED 2

typedef struct TCP_CLIENT_T_
{
    struct tcp_pcb *tcp_pcb;
    ip_addr_t remote_addr;
    uint8_t buffer[BUF_SIZE];
    uint8_t rx_buffer[BUF_SIZE];
    uint8_t send_buffer[SEND_BUFFER_SIZE];  // Buffer para acumular datos antes de enviar
    int buffer_len;
    int rx_buffer_len;
    int send_buffer_len;  // Longitud actual del buffer de envío
    int sent_len;
    int connected;
} TCP_CLIENT_T;

TCP_CLIENT_T *tcp_client_init();
void tcp_client_deinit(TCP_CLIENT_T *state);
err_t tcp_client_connect(TCP_CLIENT_T *state);
err_t tcp_client_send(TCP_CLIENT_T *state, char *data, size_t len);
int tcp_client_get_rx_data(TCP_CLIENT_T *state, char *output, size_t max_len);
void tcp_client_force_output(TCP_CLIENT_T *state);
void tcp_client_clear_send_buffer(TCP_CLIENT_T *state);

// Nuevas funciones para manejo de buffer
err_t tcp_client_buffer_send(TCP_CLIENT_T *state, const char *data, size_t len);
err_t tcp_client_flush_buffer(TCP_CLIENT_T *state);
int tcp_client_get_send_buffer_space(TCP_CLIENT_T *state);
bool tcp_client_can_send(TCP_CLIENT_T *state, size_t additional_data);
int tcp_client_get_pending_data(TCP_CLIENT_T *state);

#endif