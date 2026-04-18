#pragma once

#include "config_store.hpp"
#include "lwip/tcp.h"

class SetupManager {
public:
    SetupManager();

    // Levanta el AP, sirve el portal HTTP y bloquea hasta que la config sea guardada.
    // Retorna la config guardada por el usuario en `cfg_out`.
    void run(PersistentConfig &cfg_out);

    bool is_done() const;

private:
    bool          done_;
    struct tcp_pcb *server_pcb_;
    PersistentConfig saved_cfg_;

    void enable_ap();
    void start_http_server();

    // lwIP callbacks (C-style, usan g_instance para acceder al objeto)
    static err_t on_accept(void *arg, struct tcp_pcb *newpcb, err_t err);
    static err_t on_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err);
    static void  on_err(void *arg, err_t err);

    static void handle_request(struct tcp_pcb *pcb, const char *req, int len);
    static void send_response(struct tcp_pcb *pcb, int status,
                              const char *content_type, const char *body, int body_len);
    static bool parse_form_and_build_config(const char *body, PersistentConfig &out);
    static void url_decode(char *dst, const char *src, size_t max_len);
    static bool get_form_field(const char *body, const char *key,
                               char *out, size_t max_len);

    static SetupManager *instance_;
};
