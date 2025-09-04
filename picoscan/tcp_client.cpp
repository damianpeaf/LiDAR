#include "tcp_client.hpp"
#include "ws.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>

TCPClient::TCPClient() : points_count(0), tcp_pcb(nullptr), tx_buffer_len(0),
                         rx_buffer_len(0), connected(TCP_DISCONNECTED), handshake_complete(false)
{
}

void TCPClient::set_server_address(const char *ip, uint16_t port)
{
    ip4addr_aton(ip, &remote_addr);
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
        printf("Connect failed %d\n", err);
        return err;
    }

    client->tx_buffer_len = sprintf((char *)client->tx_buffer,
                                    "GET / HTTP/1.1\r\nHost: 192.168.1.24:3000\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\nSec-WebSocket-Protocol: chat, superchat\r\nSec-WebSocket-Version: 13\r\n\r\n");

    err = tcp_write(client->tcp_pcb, client->tx_buffer, client->tx_buffer_len, TCP_WRITE_FLAG_COPY);
    client->connected = TCP_CONNECTED;

    printf("Connected\r\n");
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
        // Buscar "101 Switching Protocols" para confirmar handshake exitoso
        bool found_switching_protocols = false;
        for (struct pbuf *q = p; q != NULL && !found_switching_protocols; q = q->next)
        {
            char *payload_str = (char *)q->payload;
            if (strstr(payload_str, "101") != NULL && strstr(payload_str, "Switching Protocols") != NULL)
            {
                found_switching_protocols = true;
                client->handshake_complete = true;
                printf("WebSocket handshake completed\r\n");
            }
        }

        if (!found_switching_protocols)
        {
            printf("WebSocket handshake failed\r\n");
        }
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
    return err;
}

err_t TCPClient::connect_to_server()
{
    if (connected != TCP_DISCONNECTED)
        return ERR_OK;

    tcp_pcb = tcp_new_ip_type(IP_GET_TYPE(&remote_addr));
    if (!tcp_pcb)
    {
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
    err_t err = tcp_connect(tcp_pcb, &remote_addr, 3000, tcp_client_connected_callback);
    cyw43_arch_lwip_end();

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

void TCPClient::add_point(float angle, uint distance, uint intensity, float servo_angle)
{
    if (points_count < MAX_QUEUED_POINTS)
    {
        points[points_count].angle = angle;
        points[points_count].distance = distance;
        points[points_count].intensity = intensity;
        points[points_count].servo_angle = servo_angle;
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

bool TCPClient::is_handshake_complete() const
{
    return handshake_complete;
}

bool TCPClient::send_points_batch(int batch_size)
{
    if (points_count < batch_size || !is_connected())
        return false;

    static char payload_buffer[TX_BUF_SIZE];
    int payload_len = 0;
    int points_in_payload = 0;
    float last_servo_angle = -1.0f;

    for (int i = 0; i < points_count; i++)
    {
        if (points[i].servo_angle != last_servo_angle)
        {
            int header_len = snprintf(payload_buffer + payload_len, TX_BUF_SIZE - payload_len, "%.1f|",
                                      points[i].servo_angle);
            if (payload_len + header_len >= TX_BUF_SIZE)
            {

                printf("Payload buffer full 1, dropping point\n");
                break;
            }
            payload_len += header_len;
            last_servo_angle = points[i].servo_angle;
        }

        int len = snprintf(payload_buffer + payload_len, TX_BUF_SIZE - payload_len, "%u;%u;%.1f;",
                           points[i].distance, points[i].intensity, points[i].angle);

        if (payload_len + len >= TX_BUF_SIZE)
        {
            printf("Payload buffer full 2, dropping point\n");
            break;
        }
        payload_len += len;
        points_in_payload++;
    }

    if (points_in_payload > 0)
    {
        cyw43_arch_lwip_begin();
        tx_buffer_len = WS::BuildPacket((char *)tx_buffer, TX_BUF_SIZE, WEBSOCKET_OPCODE_TEXT,
                                        payload_buffer, payload_len, 1);
        err_t err = tcp_write(tcp_pcb, tx_buffer, tx_buffer_len, TCP_WRITE_FLAG_COPY);

        if (err == ERR_OK)
        {
            tcp_output(tcp_pcb);
        }
        cyw43_arch_lwip_end();

        if (err == ERR_OK)
        {
            int remaining = points_count - points_in_payload;
            printf("Sent %d points, %d remaining in buffer\n", points_in_payload, remaining);
            if (remaining > 0)
            {
                memmove(points, &points[points_in_payload], remaining * sizeof(LidarPointWithServo));
            }
            points_count = remaining;
            return true;
        }
    }

    return false;
}

void TCPClient::poll()
{
    cyw43_arch_poll();
}