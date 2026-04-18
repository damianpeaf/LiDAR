#include <cstdio>
#include <cstring>
#include <cstdlib>

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "lwip/ip4_addr.h"

#include "setup_manager.hpp"
#include "setup_portal.hpp"
#include "config.hpp"

SetupManager *SetupManager::instance_ = nullptr;

// ── Contexto por conexión (uno a la vez) ──────────────────────────────────────

struct HttpConn {
    char buf[2048];
    int  len;
};

static HttpConn g_conn;
static struct tcp_pcb *g_active_pcb = nullptr;

// ── Constructor ───────────────────────────────────────────────────────────────

SetupManager::SetupManager() : done_(false), server_pcb_(nullptr)
{
    instance_ = this;
    memset(&saved_cfg_, 0, sizeof(saved_cfg_));
}

bool SetupManager::is_done() const { return done_; }

// ── Punto de entrada público ──────────────────────────────────────────────────

void SetupManager::run(PersistentConfig &cfg_out)
{
    enable_ap();
    start_http_server();

    printf("[setup] AP listo. Conéctate a '%s' y abre http://192.168.4.1\n", CFG_AP_SSID);

    while (!done_) {
        cyw43_arch_poll();
        sleep_ms(1);
    }

    cfg_out = saved_cfg_;
}

// ── AP ────────────────────────────────────────────────────────────────────────

void SetupManager::enable_ap()
{
    cyw43_arch_enable_ap_mode(CFG_AP_SSID, CFG_AP_PASS, CYW43_AUTH_WPA2_AES_PSK);
    printf("[setup] AP '%s' activo\n", CFG_AP_SSID);
}

// ── Servidor HTTP ─────────────────────────────────────────────────────────────

void SetupManager::start_http_server()
{
    cyw43_arch_lwip_begin();

    struct tcp_pcb *pcb = tcp_new_ip_type(IPADDR_TYPE_V4);
    if (!pcb) { printf("[setup] tcp_new failed\n"); cyw43_arch_lwip_end(); return; }

    if (tcp_bind(pcb, IP_ADDR_ANY, 80) != ERR_OK) {
        printf("[setup] tcp_bind failed\n");
        tcp_abort(pcb);
        cyw43_arch_lwip_end();
        return;
    }

    server_pcb_ = tcp_listen_with_backlog(pcb, 2);
    tcp_arg(server_pcb_, instance_);
    tcp_accept(server_pcb_, on_accept);

    cyw43_arch_lwip_end();
    printf("[setup] HTTP server en puerto 80\n");
}

// ── on_accept ─────────────────────────────────────────────────────────────────

err_t SetupManager::on_accept(void * /*arg*/, struct tcp_pcb *newpcb, err_t err)
{
    if (err != ERR_OK || !newpcb) return ERR_VAL;

    if (g_active_pcb) {
        // Solo atendemos una conexión a la vez
        tcp_abort(newpcb);
        return ERR_ABRT;
    }

    tcp_setprio(newpcb, TCP_PRIO_MIN);
    memset(&g_conn, 0, sizeof(g_conn));
    g_active_pcb = newpcb;

    tcp_arg(newpcb, nullptr);
    tcp_recv(newpcb, on_recv);
    tcp_err(newpcb, on_err);

    return ERR_OK;
}

// ── on_recv ───────────────────────────────────────────────────────────────────

err_t SetupManager::on_recv(void * /*arg*/, struct tcp_pcb *pcb, struct pbuf *p, err_t err)
{
    if (!p) {
        // Conexión cerrada por el cliente
        g_active_pcb = nullptr;
        tcp_close(pcb);
        return ERR_OK;
    }

    if (err != ERR_OK) {
        pbuf_free(p);
        return err;
    }

    // Acumular datos en el buffer
    int copy_len = (int)p->tot_len;
    if (g_conn.len + copy_len >= (int)sizeof(g_conn.buf) - 1)
        copy_len = (int)sizeof(g_conn.buf) - 1 - g_conn.len;

    pbuf_copy_partial(p, g_conn.buf + g_conn.len, copy_len, 0);
    g_conn.len += copy_len;
    g_conn.buf[g_conn.len] = '\0';
    tcp_recved(pcb, p->tot_len);
    pbuf_free(p);

    // Procesar cuando tenemos headers completos
    if (strstr(g_conn.buf, "\r\n\r\n")) {
        handle_request(pcb, g_conn.buf, g_conn.len);
        g_conn.len = 0;
    }

    return ERR_OK;
}

// ── on_err ────────────────────────────────────────────────────────────────────

void SetupManager::on_err(void * /*arg*/, err_t /*err*/)
{
    g_active_pcb = nullptr;
    g_conn.len = 0;
}

// ── Despacho de requests ──────────────────────────────────────────────────────

void SetupManager::handle_request(struct tcp_pcb *pcb, const char *req, int /*len*/)
{
    // Línea de request: "GET /path HTTP/1.x" o "POST /path HTTP/1.x"
    bool is_post = (strncmp(req, "POST", 4) == 0);
    bool is_get  = (strncmp(req, "GET",  3) == 0);

    // Extraer path
    const char *path_start = strchr(req, ' ');
    if (!path_start) goto bad_request;
    path_start++;

    if (is_get) {
        if (strncmp(path_start, "/ ", 2) == 0 || strncmp(path_start, "/\r", 2) == 0) {
            send_response(pcb, 200, "text/html",
                          PORTAL_HTML, strlen(PORTAL_HTML));
        } else if (strncmp(path_start, "/diag", 5) == 0) {
            char diag[256];
            snprintf(diag, sizeof(diag),
                     "PicoScan Setup Portal\nEstado: esperando configuracion\n");
            send_response(pcb, 200, "text/plain", diag, strlen(diag));
        } else {
            const char *not_found = "Not Found";
            send_response(pcb, 404, "text/plain", not_found, strlen(not_found));
        }
    } else if (is_post && strncmp(path_start, "/save", 5) == 0) {
        // Body está después de \r\n\r\n
        const char *body = strstr(req, "\r\n\r\n");
        if (body) body += 4; else body = "";

        PersistentConfig new_cfg;
        if (parse_form_and_build_config(body, new_cfg) && ConfigStore::save(new_cfg)) {
            send_response(pcb, 200, "text/html",
                          PORTAL_OK_HTML, strlen(PORTAL_OK_HTML));
            if (instance_) {
                instance_->saved_cfg_ = new_cfg;
                instance_->done_ = true;
            }
        } else {
            send_response(pcb, 400, "text/html",
                          PORTAL_ERR_HTML, strlen(PORTAL_ERR_HTML));
        }
    } else {
        bad_request:
        const char *bad = "Bad Request";
        send_response(pcb, 400, "text/plain", bad, strlen(bad));
    }

    g_active_pcb = nullptr;
}

// ── Envío de respuesta HTTP ───────────────────────────────────────────────────

void SetupManager::send_response(struct tcp_pcb *pcb, int status,
                                  const char *content_type,
                                  const char *body, int body_len)
{
    char headers[256];
    const char *status_text = (status == 200) ? "OK"
                            : (status == 400) ? "Bad Request"
                            : "Not Found";

    int hlen = snprintf(headers, sizeof(headers),
        "HTTP/1.0 %d %s\r\n"
        "Content-Type: %s; charset=utf-8\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n",
        status, status_text, content_type, body_len);

    tcp_write(pcb, headers, hlen,  TCP_WRITE_FLAG_COPY | TCP_WRITE_FLAG_MORE);
    tcp_write(pcb, body,    body_len, TCP_WRITE_FLAG_COPY);
    tcp_output(pcb);
    tcp_close(pcb);
}

// ── Parseo de form URL-encoded ────────────────────────────────────────────────

void SetupManager::url_decode(char *dst, const char *src, size_t max_len)
{
    size_t j = 0;
    for (size_t i = 0; src[i] && j < max_len - 1; i++) {
        if (src[i] == '+') {
            dst[j++] = ' ';
        } else if (src[i] == '%' && src[i+1] && src[i+2]) {
            char hex[3] = { src[i+1], src[i+2], '\0' };
            dst[j++] = (char)strtol(hex, nullptr, 16);
            i += 2;
        } else {
            dst[j++] = src[i];
        }
    }
    dst[j] = '\0';
}

bool SetupManager::get_form_field(const char *body, const char *key,
                                   char *out, size_t max_len)
{
    char search[64];
    snprintf(search, sizeof(search), "%s=", key);
    const char *pos = strstr(body, search);
    if (!pos) { out[0] = '\0'; return false; }
    pos += strlen(search);

    const char *end = strchr(pos, '&');
    size_t len = end ? (size_t)(end - pos) : strlen(pos);
    if (len >= max_len) len = max_len - 1;

    char encoded[256] = {};
    memcpy(encoded, pos, len);
    url_decode(out, encoded, max_len);
    return out[0] != '\0';
}

bool SetupManager::parse_form_and_build_config(const char *body, PersistentConfig &out)
{
    ConfigStore::fill_defaults(out);  // parte de los defaults para campos no enviados

    char tmp[64];

    if (!get_form_field(body, "ssid", out.wifi_ssid, sizeof(out.wifi_ssid)))
        return false;
    if (!get_form_field(body, "ip", out.tcp_ip, sizeof(out.tcp_ip)))
        return false;

    get_form_field(body, "pass",    out.wifi_pass,    sizeof(out.wifi_pass));
    get_form_field(body, "country", out.wifi_country, sizeof(out.wifi_country));

    if (get_form_field(body, "port", tmp, sizeof(tmp)))
        out.tcp_port = (uint16_t)atoi(tmp);
    if (get_form_field(body, "batch", tmp, sizeof(tmp)))
        out.batch_size = (uint16_t)atoi(tmp);

    ConfigStore::seal(out);
    return true;
}
