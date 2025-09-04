#ifndef TCP_CLIENT_HPP
#define TCP_CLIENT_HPP

#include "pico/cyw43_arch.h"
#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "lidar.hpp"

// Optimización de memoria: buffers separados para TX/RX
#define TX_BUF_SIZE 2048       // Buffer completo para envío de datos
#define RX_BUF_SIZE 512        // Buffer mínimo solo para handshake WebSocket
#define MAX_QUEUED_POINTS 5000

typedef struct
{
    float angle;
    uint distance;
    uint intensity;
    float servo_angle;
} LidarPointWithServo;

enum ConnectionState
{
    TCP_DISCONNECTED = 0,
    TCP_CONNECTING = 1,
    TCP_CONNECTED = 2
};

class TCPClient
{
private:
    LidarPointWithServo points[MAX_QUEUED_POINTS];
    int points_count;
    struct tcp_pcb *tcp_pcb;
    ip_addr_t remote_addr;
    uint8_t tx_buffer[TX_BUF_SIZE];     // Buffer para envío
    uint8_t rx_buffer[RX_BUF_SIZE];     // Buffer mínimo para handshake
    int tx_buffer_len;
    int rx_buffer_len;
    int connected;
    bool handshake_complete;
    
    static err_t tcp_client_sent_callback(void *arg, struct tcp_pcb *tpcb, u16_t len);
    static err_t tcp_client_connected_callback(void *arg, struct tcp_pcb *tpcb, err_t err);
    static err_t tcp_client_poll_callback(void *arg, struct tcp_pcb *tpcb);
    static void tcp_client_err_callback(void *arg, err_t err);
    static err_t tcp_client_recv_callback(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err);
    
    err_t close_connection();

public:
    TCPClient();
    
    void set_server_address(const char* ip, uint16_t port);
    err_t connect_to_server();
    bool is_connected() const;
    bool is_disconnected() const;
    
    void add_point(float angle, uint distance, uint intensity, float servo_angle);
    int get_points_count() const;
    bool is_handshake_complete() const;
    
    bool send_points_batch(int batch_size);
    
    void poll();
};

#endif // TCP_CLIENT_HPP