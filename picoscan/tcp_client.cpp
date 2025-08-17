#include "tcp_client.h"
#include <algorithm>  // Para std::min

static err_t tcp_client_sent(void *arg, struct tcp_pcb *tpcb, u16_t len)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    printf("tcp_client_sent %u\n", len);
    return ERR_OK;
}

static err_t tcp_client_connected(void *arg, struct tcp_pcb *tpcb, err_t err)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    if (err != ERR_OK)
    {
        printf("Connect failed %d\n", err);
        return err;
    }

    state->buffer_len = sprintf((char *)state->buffer,
                                "GET / HTTP/1.1\r\nHost: 192.168.1.24:3000\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\nSec-WebSocket-Protocol: chat, superchat\r\nSec-WebSocket-Version: 13\r\n\r\n");
    err = tcp_write(state->tcp_pcb, state->buffer, state->buffer_len, TCP_WRITE_FLAG_COPY);

    state->connected = TCP_CONNECTED;
    printf("Connected\r\n");
    return ERR_OK;
}

static err_t tcp_client_poll(void *arg, struct tcp_pcb *tpcb)
{
    printf("tcp_client_poll\n");
    return ERR_OK;
}

static void tcp_client_err(void *arg, err_t err)
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
    state->connected = TCP_DISCONNECTED;
    printf("tcp_client_err %s\n", err != ERR_ABRT ? "error" : "abort");
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
            printf("close failed %d, calling abort\n", err);
            tcp_abort(state->tcp_pcb);
            err = ERR_ABRT;
        }
        state->tcp_pcb = NULL;
    }
    state->connected = TCP_DISCONNECTED;
    return err;
}

static err_t tcp_client_recv(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err)
{
    printf("recv \r\n");
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)arg;
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
        printf("tcp_recved \r\n");
        tcp_recved(tpcb, p->tot_len);
    }
    pbuf_free(p);
    return ERR_OK;
}

TCP_CLIENT_T *tcp_client_init()
{
    TCP_CLIENT_T *state = (TCP_CLIENT_T *)calloc(1, sizeof(TCP_CLIENT_T));
    if (!state)
    {
        printf("failed to allocate state\n");
        return NULL;
    }
    ip4addr_aton(TEST_TCP_SERVER_IP, &state->remote_addr);
    state->send_buffer_len = 0;  // Inicializar el buffer de envío
    return state;
}

void tcp_client_deinit(TCP_CLIENT_T *state)
{
    if (state)
    {
        tcp_client_close(state);
        free(state);
    }
}

err_t tcp_client_connect(TCP_CLIENT_T *state)
{
    if (!state || state->connected != TCP_DISCONNECTED)
    {
        return ERR_OK;
    }

    state->tcp_pcb = tcp_new_ip_type(IP_GET_TYPE(&state->remote_addr));
    if (!state->tcp_pcb)
    {
        // print something
        printf("Failed to create TCP PCB\n");
        return ERR_MEM;
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

    return err;
}

err_t tcp_client_send(TCP_CLIENT_T *state, char *data, size_t len)
{
    if (!state || state->connected != TCP_CONNECTED)
    {
        return ERR_CONN;
    }
    state->buffer_len = WS::BuildPacket((char *)state->buffer, BUF_SIZE, WEBSOCKET_OPCODE_TEXT, data, len, 1);
    return tcp_write(state->tcp_pcb, state->buffer, state->buffer_len, TCP_WRITE_FLAG_COPY);
}

int tcp_client_get_rx_data(TCP_CLIENT_T *state, char *output, size_t max_len)
{
    if (!state || !state->rx_buffer_len)
    {
        return 0;
    }
    int len = std::min(state->rx_buffer_len, (int)max_len);
    memcpy(output, state->rx_buffer, len);
    state->rx_buffer_len = 0;
    return len;
}

// Nuevas funciones para manejo de buffer
int tcp_client_get_send_buffer_space(TCP_CLIENT_T *state)
{
    if (!state || state->connected != TCP_CONNECTED || !state->tcp_pcb)
    {
        return 0;
    }
    return tcp_sndbuf(state->tcp_pcb);
}

bool tcp_client_can_send(TCP_CLIENT_T *state, size_t additional_data)
{
    if (!state || state->connected != TCP_CONNECTED)
    {
        return false;
    }
    
    // Verificar si hay espacio en el buffer interno
    if (state->send_buffer_len + additional_data > SEND_BUFFER_SIZE)
    {
        return false;
    }
    
    // Verificar si hay espacio en el buffer TCP
    int tcp_space = tcp_client_get_send_buffer_space(state);
    return tcp_space > 0;
}

err_t tcp_client_buffer_send(TCP_CLIENT_T *state, const char *data, size_t len)
{
    if (!state || state->connected != TCP_CONNECTED)
    {
        return ERR_CONN;
    }
    
    // Si el buffer interno está lleno, intentar enviar lo que hay
    if (state->send_buffer_len + len > SEND_BUFFER_SIZE)
    {
        err_t err = tcp_client_flush_buffer(state);
        if (err != ERR_OK)
        {
            return err;
        }
    }
    
    // Agregar datos al buffer interno
    if (state->send_buffer_len + len <= SEND_BUFFER_SIZE)
    {
        memcpy(state->send_buffer + state->send_buffer_len, data, len);
        state->send_buffer_len += len;
        return ERR_OK;
    }
    
    return ERR_MEM;
}

err_t tcp_client_flush_buffer(TCP_CLIENT_T *state)
{
    if (!state || state->connected != TCP_CONNECTED || state->send_buffer_len == 0)
    {
        return ERR_OK;
    }
    
    // Verificar espacio disponible en el buffer TCP
    int tcp_space = tcp_client_get_send_buffer_space(state);
    if (tcp_space <= 0)
    {
        // Si no hay espacio, forzar envío de lo que hay
        tcp_output(state->tcp_pcb);
        return ERR_MEM;
    }
    
    // Enviar solo lo que cabe en el buffer TCP
    size_t to_send = std::min((size_t)tcp_space, (size_t)state->send_buffer_len);
    
    // Construir el paquete WebSocket
    state->buffer_len = WS::BuildPacket((char *)state->buffer, BUF_SIZE, 
                                       WEBSOCKET_OPCODE_TEXT, 
                                       (char *)state->send_buffer, to_send, 1);
    
    err_t err = tcp_write(state->tcp_pcb, state->buffer, state->buffer_len, TCP_WRITE_FLAG_COPY);
    if (err == ERR_OK)
    {
        // Mover los datos restantes al inicio del buffer
        if (to_send < state->send_buffer_len)
        {
            memmove(state->send_buffer, state->send_buffer + to_send, 
                   state->send_buffer_len - to_send);
            state->send_buffer_len -= to_send;
        }
        else
        {
            state->send_buffer_len = 0;
        }
        
        // Forzar el envío inmediatamente
        tcp_output(state->tcp_pcb);
    }
    else if (err == ERR_MEM)
    {
        // Si no hay memoria, forzar envío de lo que hay
        tcp_output(state->tcp_pcb);
    }
    
    return err;
}

void tcp_client_force_output(TCP_CLIENT_T *state)
{
    if (state && state->connected == TCP_CONNECTED && state->tcp_pcb)
    {
        tcp_output(state->tcp_pcb);
    }
}

void tcp_client_clear_send_buffer(TCP_CLIENT_T *state)
{
    if (state)
    {
        state->send_buffer_len = 0;
    }
}

int tcp_client_get_pending_data(TCP_CLIENT_T *state)
{
    if (!state)
    {
        return 0;
    }
    return state->send_buffer_len;
}