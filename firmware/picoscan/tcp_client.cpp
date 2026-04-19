#include "tcp_client.hpp"
#include "ws.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "config.hpp"
#include "pico/time.h"

namespace
{
    constexpr uint8_t kBinaryBatchMagic0 = 'P';
    constexpr uint8_t kBinaryBatchMagic1 = 'S';
    constexpr uint8_t kBinaryBatchVersion = 1;
    constexpr uint8_t kBinaryBatchFlags = 0;
    // Forzamos payload <=125 bytes para evitar el path de longitud extendida (126/127)
    // del builder WS actual, que es el sospechoso principal de frames inválidos.
    constexpr int kTargetMaxWsFrameBytes = 120;
    constexpr uint32_t kMinSendIntervalMs = 60;
    constexpr uint16_t kMinTcpSndbufBytes = 300;
    constexpr uint16_t kMaxTcpSendQueueLen = 3;

#if CFG_DEBUG_SERIAL
#define DBG_PRINTF(...) printf(__VA_ARGS__)
#else
#define DBG_PRINTF(...)
#endif
}

// La secuencia de upgrade HTTP a WebSocket se armó tomando como referencia
// ejemplos públicos de la comunidad para Pico W, en particular el trabajo de Sam Kent,
// y luego se adaptó a las necesidades de este proyecto.
// Referencia utilizada como punto de partida general
// https://github.com/samjkent/picow-websocket

TCPClient::TCPClient() : points_head(0), points_tail(0), points_count(0), tcp_pcb(nullptr), tx_buffer_len(0),
                         rx_buffer_len(0), connected(TCP_DISCONNECTED), handshake_complete(false),
                         device_authenticated(false), auth_pending(false), remote_port(3000)
{
    device_password[0] = '\0';
    server_host_[0] = '\0';
    memset(&remote_addr, 0, sizeof(remote_addr));
}

void TCPClient::set_server_address(const char *host, uint16_t port)
{
    strncpy(server_host_, host, sizeof(server_host_) - 1);
    server_host_[sizeof(server_host_) - 1] = '\0';
    remote_port = port;
    memset(&remote_addr, 0, sizeof(remote_addr));
}

namespace
{
    struct DnsWait
    {
        ip_addr_t addr;
        volatile bool done;
        volatile bool ok;
    };

    void dns_found_cb(const char *name, const ip_addr_t *addr, void *arg)
    {
        DnsWait *w = (DnsWait *)arg;
        if (addr)
        {
            w->addr = *addr;
            w->ok = true;
        }
        w->done = true;
    }
}

bool TCPClient::resolve_hostname_blocking(const char *host)
{
    DnsWait w = {};
    w.done = false;
    w.ok = false;

    printf("[dns] resolving '%s'...\n", host);

    cyw43_arch_lwip_begin();
    err_t err = dns_gethostbyname(host, &w.addr, dns_found_cb, &w);
    cyw43_arch_lwip_end();

    if (err == ERR_OK)
    {
        // Already cached
        w.ok = true;
        w.done = true;
    }
    else if (err != ERR_INPROGRESS)
    {
        printf("[dns] error %d resolving '%s'\n", err, host);
        return false;
    }

    uint32_t start = to_ms_since_boot(get_absolute_time());
    while (!w.done)
    {
        cyw43_arch_poll();
        sleep_ms(10);
        if (to_ms_since_boot(get_absolute_time()) - start > 10000)
        {
            printf("[dns] timeout resolving '%s'\n", host);
            return false;
        }
    }

    if (!w.ok)
    {
        printf("[dns] failed to resolve '%s'\n", host);
        return false;
    }

    char ip_str[16];
    ip4addr_ntoa_r(ip_2_ip4(&w.addr), ip_str, sizeof(ip_str));
    printf("[dns] '%s' -> %s\n", host, ip_str);

    remote_addr = w.addr;
    return true;
}

void TCPClient::set_device_password(const char *password)
{
    if (!password)
    {
        device_password[0] = '\0';
        return;
    }

    strncpy(device_password, password, sizeof(device_password) - 1);
    device_password[sizeof(device_password) - 1] = '\0';
}

err_t TCPClient::tcp_client_sent_callback(void *arg, struct tcp_pcb *tpcb, u16_t len)
{
    return ERR_OK;
}

err_t TCPClient::tcp_client_connected_callback(void *arg, struct tcp_pcb *tpcb, err_t err)
{
    TCPClient *client = (TCPClient *)arg;
    if (err != ERR_OK)
    {
        printf("[net] TCP connect failed: %d\n", err);
        return err;
    }

    char host_ip[16];
    ip4addr_ntoa_r(ip_2_ip4(&client->remote_addr), host_ip, sizeof(host_ip));
    printf("[ws] TCP connected to %s:%u, sending WebSocket upgrade\n", host_ip, client->remote_port);

    client->tx_buffer_len = snprintf((char *)client->tx_buffer,
                                     TX_BUF_SIZE,
                                     "GET / HTTP/1.1\r\n"
                                     "Host: %s:%u\r\n"
                                     "Upgrade: websocket\r\n"
                                     "Connection: Upgrade\r\n"
                                     "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\n"
                                     "Sec-WebSocket-Protocol: chat, superchat\r\n"
                                     "Sec-WebSocket-Version: 13\r\n\r\n",
                                     host_ip,
                                     client->remote_port);

    err = tcp_write(client->tcp_pcb, client->tx_buffer, client->tx_buffer_len, TCP_WRITE_FLAG_COPY);
    if (err != ERR_OK)
    {
        printf("[ws] tcp_write upgrade failed: %d\n", err);
        client->close_connection();
        return err;
    }

    err = tcp_output(client->tcp_pcb);
    if (err != ERR_OK)
    {
        printf("[ws] tcp_output upgrade failed: %d\n", err);
        client->close_connection();
        return err;
    }

    client->connected = TCP_CONNECTED;
    return ERR_OK;
}

err_t TCPClient::tcp_client_poll_callback(void *arg, struct tcp_pcb *tpcb)
{
    return ERR_OK;
}

void TCPClient::tcp_client_err_callback(void *arg, err_t err)
{
    TCPClient *client = (TCPClient *)arg;
    client->connected = TCP_DISCONNECTED;
    if (err != ERR_ABRT)
    {
        printf("tcp_client_err %d\n", err);
    }
}

err_t TCPClient::tcp_client_recv_callback(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err)
{
    TCPClient *client = (TCPClient *)arg;

    if (p == NULL)
    {
        client->close_connection();
        return ERR_OK;
    }

    cyw43_arch_lwip_check();

    // Solo procesamos la respuesta del handshake WebSocket inicial
    if (!client->handshake_complete && p->tot_len > 0)
    {
        printf("[ws] handshake response received (%u bytes)\n", p->tot_len);

        // Print first 200 chars of response for debugging
        char preview[201] = {};
        pbuf_copy_partial(p, preview, sizeof(preview) - 1, 0);
        printf("[ws] response preview: %.200s\n", preview);

        bool found_switching_protocols = (strstr(preview, "101") != NULL &&
                                          strstr(preview, "Switching Protocols") != NULL);

        if (found_switching_protocols)
        {
            client->handshake_complete = true;
            client->device_authenticated = true;
            client->auth_pending = false;
            printf("[ws] handshake OK — device auth bypass enabled\n");
        }
        else
        {
            printf("[ws] handshake FAILED — no '101 Switching Protocols' in response\n");
        }
    }
    else if (p->tot_len > 0)
    {
        printf("[ws] data received after handshake (%u bytes)\n", p->tot_len);
    }

    // Confirmamos la recepción pero no almacenamos los datos
    tcp_recved(tpcb, p->tot_len);
    pbuf_free(p);

    return ERR_OK;
}

err_t TCPClient::close_connection()
{
    err_t err = ERR_OK;
    if (tcp_pcb != NULL)
    {
        tcp_arg(tcp_pcb, NULL);
        tcp_poll(tcp_pcb, NULL, 0);
        tcp_sent(tcp_pcb, NULL);
        tcp_recv(tcp_pcb, NULL);
        tcp_err(tcp_pcb, NULL);
        err = tcp_close(tcp_pcb);
        if (err != ERR_OK)
        {
            tcp_abort(tcp_pcb);
            err = ERR_ABRT;
        }
        tcp_pcb = NULL;
    }
    connected = TCP_DISCONNECTED;
    handshake_complete = false;
    device_authenticated = false;
    auth_pending = false;
    return err;
}

err_t TCPClient::connect_to_server()
{
    if (connected != TCP_DISCONNECTED)
        return ERR_OK;

    // Resolve hostname if not a dotted-decimal IP
    if (!ip4addr_aton(server_host_, ip_2_ip4(&remote_addr)))
    {
        if (!resolve_hostname_blocking(server_host_))
            return ERR_ABRT;
    }

    char ip_str[16];
    ip4addr_ntoa_r(ip_2_ip4(&remote_addr), ip_str, sizeof(ip_str));
    printf("[net] TCP connect -> %s:%u\n", ip_str, remote_port);

    tcp_pcb = tcp_new_ip_type(IP_GET_TYPE(&remote_addr));
    if (!tcp_pcb)
    {
        printf("[net] tcp_new failed\n");
        return ERR_ABRT;
    }

    tcp_arg(tcp_pcb, this);
    tcp_poll(tcp_pcb, tcp_client_poll_callback, 1);
    tcp_sent(tcp_pcb, tcp_client_sent_callback);
    tcp_recv(tcp_pcb, tcp_client_recv_callback);
    tcp_err(tcp_pcb, tcp_client_err_callback);

    tx_buffer_len = 0;
    handshake_complete = false;
    cyw43_arch_lwip_begin();
    connected = TCP_CONNECTING;
    device_authenticated = false;
    auth_pending = false;
    err_t err = tcp_connect(tcp_pcb, &remote_addr, remote_port, tcp_client_connected_callback);
    cyw43_arch_lwip_end();

    if (err != ERR_OK)
        printf("[net] tcp_connect returned %d\n", err);

    return err;
}

bool TCPClient::is_connected() const
{
    return connected == TCP_CONNECTED;
}

bool TCPClient::is_disconnected() const
{
    return connected == TCP_DISCONNECTED;
}

int16_t TCPClient::scale_angle_tenths(float angle)
{
    return static_cast<int16_t>(lroundf(angle * 10.0f));
}

bool TCPClient::append_u8(uint8_t *buffer, int capacity, int &offset, uint8_t value)
{
    if (offset >= capacity)
    {
        return false;
    }

    buffer[offset++] = value;
    return true;
}

bool TCPClient::append_u16_le(uint8_t *buffer, int capacity, int &offset, uint16_t value)
{
    if (offset + 2 > capacity)
    {
        return false;
    }

    buffer[offset++] = static_cast<uint8_t>(value & 0xFF);
    buffer[offset++] = static_cast<uint8_t>((value >> 8) & 0xFF);
    return true;
}

void TCPClient::add_point(float angle, uint distance, uint intensity, float servo_angle)
{
    if (points_count < MAX_QUEUED_POINTS)
    {
        points[points_tail].pan_angle_tenths = static_cast<uint16_t>(scale_angle_tenths(angle));
        points[points_tail].distance_mm = static_cast<uint16_t>(distance);
        points[points_tail].intensity = static_cast<uint8_t>(intensity);
        points[points_tail].servo_angle_tenths = scale_angle_tenths(servo_angle);
        points_tail = (points_tail + 1) % MAX_QUEUED_POINTS;
        points_count++;
    }
    else
    {
        printf("Point buffer full, dropping point\n");
    }
}

int TCPClient::get_points_count() const
{
    return points_count;
}

bool TCPClient::is_point_queue_full() const
{
    return points_count >= MAX_QUEUED_POINTS;
}

int TCPClient::point_index_from_offset(int offset) const
{
    return (points_head + offset) % MAX_QUEUED_POINTS;
}

const LidarPointWithServo &TCPClient::queued_point_at(int offset) const
{
    return points[point_index_from_offset(offset)];
}

void TCPClient::drop_queued_points(int count)
{
    if (count <= 0)
    {
        return;
    }

    if (count >= points_count)
    {
        points_head = 0;
        points_tail = 0;
        points_count = 0;
        return;
    }

    points_head = point_index_from_offset(count);
    points_count -= count;
}

bool TCPClient::is_handshake_complete() const
{
    return handshake_complete;
}

bool TCPClient::send_device_auth()
{
    if (!is_connected() || !is_handshake_complete() || device_authenticated || auth_pending)
    {
        return false;
    }

    if (device_password[0] == '\0')
    {
        printf("[auth] ERROR: device_password is empty — cannot authenticate\n");
        return false;
    }

    printf("[auth] sending auth with password='%s'\n", device_password);

    char auth_json[128];
    int auth_len = snprintf(auth_json, sizeof(auth_json),
                            "{\"type\":\"auth\",\"password\":\"%s\"}",
                            device_password);
    if (auth_len <= 0 || auth_len >= (int)sizeof(auth_json))
    {
        printf("[auth] payload build failed (len=%d)\n", auth_len);
        return false;
    }

    err_t err = ERR_VAL;
    cyw43_arch_lwip_begin();
    tx_buffer_len = WS::BuildPacket((char *)tx_buffer, TX_BUF_SIZE, WEBSOCKET_OPCODE_TEXT,
                                    auth_json, auth_len, 1);

    if (tx_buffer_len > 0 && tx_buffer_len <= TX_BUF_SIZE)
    {
        err = tcp_write(tcp_pcb, tx_buffer, tx_buffer_len, TCP_WRITE_FLAG_COPY);
                if (err == ERR_OK)
                {
                    err = tcp_output(tcp_pcb);
                }
    }
    cyw43_arch_lwip_end();

    if (err == ERR_OK)
    {
        auth_pending = true;
        printf("[auth] message sent OK (ws frame %d bytes)\n", tx_buffer_len);
        return true;
    }

    printf("[auth] tcp_write failed: %d\n", err);
    return false;
}

bool TCPClient::send_points_batch(int batch_size)
{
    if (points_count < batch_size || !is_connected() || !is_handshake_complete() || !device_authenticated)
    {
        static uint32_t last_log = 0;
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_log > 5000)
        {
            last_log = now;
            printf("[tx] blocked: pts=%d/%d connected=%d hs=%d auth=%d\n",
                   points_count, batch_size,
                   is_connected(), is_handshake_complete(), device_authenticated);
        }
        return false;
    }

    static uint8_t payload_buffer[MAX_BINARY_PAYLOAD_SIZE];
    static uint32_t last_send_ms = 0;
    int payload_len = 0;
    int points_in_payload = 0;
    const int max_payload_len = (kTargetMaxWsFrameBytes > 8) ? (kTargetMaxWsFrameBytes - 8) : (MAX_BINARY_PAYLOAD_SIZE - 8);

    uint32_t now_ms = to_ms_since_boot(get_absolute_time());
    if (now_ms - last_send_ms < kMinSendIntervalMs)
    {
        return false;
    }

    uint16_t sndbuf = 0;
    uint16_t sndq = 0;
    cyw43_arch_lwip_begin();
    sndbuf = tcp_sndbuf(tcp_pcb);
    sndq = tcp_sndqueuelen(tcp_pcb);
    cyw43_arch_lwip_end();

    if (sndbuf < kMinTcpSndbufBytes || sndq > kMaxTcpSendQueueLen)
    {
        return false;
    }

    const LidarPointWithServo &first_point = queued_point_at(0);
    const int16_t servo_angle_tenths = first_point.servo_angle_tenths;

    if (!append_u8(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, kBinaryBatchMagic0) ||
        !append_u8(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, kBinaryBatchMagic1) ||
        !append_u8(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, kBinaryBatchVersion) ||
        !append_u8(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, kBinaryBatchFlags) ||
        !append_u16_le(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, static_cast<uint16_t>(servo_angle_tenths)) ||
        !append_u16_le(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, 0))
    {
        printf("Binary payload header did not fit in buffer\n");
        return false;
    }

    for (int i = 0; i < points_count; i++)
    {
        const LidarPointWithServo &point = queued_point_at(i);

        if (point.servo_angle_tenths != servo_angle_tenths)
        {
            break;
        }

        if (payload_len + BINARY_POINT_RECORD_SIZE > max_payload_len)
        {
            break;
        }

        if (!append_u16_le(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, point.distance_mm) ||
            !append_u8(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, point.intensity) ||
            !append_u16_le(payload_buffer, MAX_BINARY_PAYLOAD_SIZE, payload_len, point.pan_angle_tenths))
        {
            // printf("Binary payload reached safe WebSocket limit; current point stays queued for the next send\n");
            break;
        }

        points_in_payload++;
    }

    if (points_in_payload > 0)
    {
        payload_buffer[6] = static_cast<uint8_t>(points_in_payload & 0xFF);
        payload_buffer[7] = static_cast<uint8_t>((points_in_payload >> 8) & 0xFF);

        err_t err = ERR_VAL;
        cyw43_arch_lwip_begin();
        tx_buffer_len = WS::BuildPacket((char *)tx_buffer, TX_BUF_SIZE, WEBSOCKET_OPCODE_BINARY,
                                        (char *)payload_buffer, payload_len, 1);

        if (tx_buffer_len <= 0 || tx_buffer_len > TX_BUF_SIZE)
        {
            printf("WebSocket packet build failed, skipping tcp_write\n");
        }
        else
        {
            err = tcp_write(tcp_pcb, tx_buffer, tx_buffer_len, TCP_WRITE_FLAG_COPY);

            if (err == ERR_OK)
            {
                tcp_output(tcp_pcb);
            }
        }
        cyw43_arch_lwip_end();

        if (err == ERR_OK)
        {
            int remaining = points_count - points_in_payload;
            DBG_PRINTF("[dbg][tx] sent batch points=%d servo=%.1f remaining=%d\r\n",
                       points_in_payload,
                       static_cast<float>(servo_angle_tenths) / 10.0f,
                       remaining);
            last_send_ms = now_ms;
            drop_queued_points(points_in_payload);
            return true;
        }

        printf("[tx] send failed: tcp_output=%d payload=%d ws_frame=%d queued=%d\n",
               err, payload_len, tx_buffer_len, points_count);

        if (err == ERR_CONN || err == ERR_CLSD || err == ERR_ABRT)
        {
            printf("[tx] closing connection due to send error=%d\n", err);
            close_connection();
        }
    }

    return false;
}

void TCPClient::poll()
{
    cyw43_arch_poll();
}
