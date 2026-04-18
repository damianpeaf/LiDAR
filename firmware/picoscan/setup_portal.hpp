#pragma once

// HTML embebido para el portal de setup
// Formato usado en setup_manager.cpp vía tcp_write()

static const char PORTAL_HTML[] =
    "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
    "<title>PicoScan Setup</title>"
    "<style>"
    "body{font-family:sans-serif;max-width:480px;margin:40px auto;padding:0 16px}"
    "h1{color:#333}h2{color:#555;margin-top:20px;border-bottom:1px solid #ddd;padding-bottom:4px}"
    "label{display:block;font-size:.85rem;color:#555;margin-top:10px}"
    "input{display:block;width:100%;padding:7px;margin-top:3px;box-sizing:border-box;border:1px solid #ccc;border-radius:3px}"
    ".note{background:#fff3cd;border:1px solid #ffc107;padding:10px 14px;border-radius:4px;margin:12px 0;font-size:.85rem}"
    "button{width:100%;padding:11px;margin-top:20px;background:#0d6efd;color:#fff;border:none;border-radius:4px;font-size:1rem;cursor:pointer}"
    "</style></head><body>"
    "<h1>PicoScan &mdash; Setup</h1>"
    "<div class=\"note\">Si tu dispositivo no obtuvo IP automática, configura:<br>"
    "IP&nbsp;192.168.4.2/24 &nbsp;&bull;&nbsp; Gateway&nbsp;192.168.4.1</div>"
    "<form method=\"POST\" action=\"/save\">"
    "<h2>WiFi</h2>"
    "<label>SSID<input name=\"ssid\" required autocomplete=\"off\"></label>"
    "<label>Contraseña<input name=\"pass\" type=\"password\"></label>"
    "<label>País (código ISO, ej. UK)<input name=\"country\" value=\"UK\" maxlength=\"2\"></label>"
    "<h2>Servidor</h2>"
    "<label>IP o hostname<input name=\"ip\" required placeholder=\"192.168.1.x\"></label>"
    "<label>Puerto<input name=\"port\" type=\"number\" value=\"3000\" min=\"1\" max=\"65535\"></label>"
    "<h2>Escaneo</h2>"
    "<label>Batch size<input name=\"batch\" type=\"number\" value=\"100\" min=\"10\" max=\"1000\"></label>"
    "<button type=\"submit\">Guardar y reiniciar</button>"
    "</form>"
    "</body></html>";

static const char PORTAL_OK_HTML[] =
    "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
    "<meta http-equiv=\"refresh\" content=\"4\">"
    "<title>PicoScan</title></head><body style=\"font-family:sans-serif;max-width:480px;margin:60px auto;text-align:center\">"
    "<h2 style=\"color:#198754\">&#10003; Config guardada</h2>"
    "<p>El dispositivo reiniciará en unos segundos y se conectará a la red configurada.</p>"
    "</body></html>";

static const char PORTAL_ERR_HTML[] =
    "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>PicoScan</title></head>"
    "<body style=\"font-family:sans-serif;max-width:480px;margin:60px auto;text-align:center\">"
    "<h2 style=\"color:#dc3545\">&#10007; Error al guardar</h2>"
    "<p>Verifica los datos e intenta nuevamente.</p>"
    "<a href=\"/\">Volver</a>"
    "</body></html>";
