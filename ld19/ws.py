from machine import Pin, UART
import struct
import ujson
import network
import socket
import urandom
from time import sleep

# Configuración UART para LIDAR
uart = UART(1, 230400, tx=Pin(8), rx=Pin(9))

# Configuración de red y WebSocket
SSID = "CLARO1_8E2AAB"
PASSWORD = "841qlCREpc"
API_URL = "192.168.1.24"
PORT = 3000

# Constantes LIDAR
HEADER = 0x54
POINT_PER_PACK = 12
FRAME_SIZE = 47

# Tabla CRC
CRC_TABLE = [
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
    0xf4, 0xb9, 0x6e, 0x23, 0x8d, 0xc0, 0x17, 0x5a, 0x06, 0x4b, 0x9c, 0xd1, 0x7f, 0x32, 0xe5, 0xa8
]

def calc_crc8(data):
    crc = 0
    for byte in data:
        crc = CRC_TABLE[(crc ^ byte) & 0xff]
    return crc

def normalize_angle(angle):
    angle_deg = angle / 100.0
    while angle_deg < 0:
        angle_deg += 360
    while angle_deg >= 360:
        angle_deg -= 360
    return round(angle_deg, 2)

def parse_lidar_points_only(data):
    if len(data) != FRAME_SIZE or data[0] != HEADER:
        return None
    if CRC_TABLE and calc_crc8(data[:-1]) != data[-1]:
        return None
    start_angle = struct.unpack('<H', data[4:6])[0]
    end_angle = struct.unpack('<H', data[42:44])[0]
    start_angle_norm = normalize_angle(start_angle)
    end_angle_norm = normalize_angle(end_angle)
    if end_angle_norm < start_angle_norm:
        end_angle_norm += 360
    step = (end_angle_norm - start_angle_norm) / (POINT_PER_PACK - 1) if POINT_PER_PACK > 1 else 0
    points_data = data[6:42]
    points = []
    for i in range(POINT_PER_PACK):
        offset = i * 3
        distance, intensity = struct.unpack('<HB', points_data[offset:offset+3])
        angle = start_angle_norm + step * i
        if angle >= 360:
            angle -= 360
        if distance > 0:
            points.append({
                'a': round(angle, 1),
                'd': distance,
                'i': intensity
            })
    return points

def find_header():
    while True:
        byte = uart.read(1)
        if byte and byte[0] == HEADER:
            return True
        if not byte:
            sleep(0.001)

def send_websocket_message(s, data):
    try:
        payload = ujson.dumps(data).encode()
        payload_len = len(payload)
        mask = bytearray([urandom.getrandbits(8) for _ in range(4)])
        masked_payload = bytearray(payload_len)
        for i in range(payload_len):
            masked_payload[i] = payload[i] ^ mask[i % 4]
        
        # Construir trama WebSocket
        frame = bytearray()
        frame.append(0x81)  # Opcode texto, FIN=1
        # Longitud del payload
        if payload_len <= 125:
            frame.append(payload_len | 0x80)  # Longitud con bit de máscara
        elif payload_len <= 65535:
            frame.append(126 | 0x80)  # Longitud extendida de 16 bits
            frame.extend(struct.pack('>H', payload_len))
        else:
            frame.append(127 | 0x80)  # Longitud extendida de 64 bits
            frame.extend(struct.pack('>Q', payload_len))
        frame.extend(mask)
        frame.extend(masked_payload)
        
        print("Enviando trama WebSocket:", [hex(b) for b in frame[:10]], "...")  # Depuración: primeros 10 bytes
        s.send(frame)
        print("Datos enviados:", data)
    except Exception as e:
        print("Error enviando mensaje WebSocket:", e)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando WiFi...")
        wlan.connect(SSID, PASSWORD)
        timeout = 0
        while not wlan.isconnected() and timeout < 30:
            sleep(1)
            timeout += 1
        if wlan.isconnected():
            print("WiFi conectado:", wlan.ifconfig())
            return wlan
        else:
            print("Error: no se pudo conectar a WiFi")
            return None
    return wlan

def main():
    uart.read()  # Limpiar buffer UART
    wlan = conectar_wifi()
    if not wlan:
        print("No se pudo conectar a WiFi, deteniendo...")
        return

    print("Conectando a WebSocket...")
    addr = socket.getaddrinfo(API_URL, PORT)[0][-1]
    s = socket.socket()
    try:
        s.connect(addr)
        print("Conectado al servidor:", addr)

        print("Enviando handshake WebSocket...")
        s.send(b"GET / HTTP/1.1\r\nHost: 192.168.1.24\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\nSec-WebSocket-Version: 13\r\n\r\n")
        sleep(2)
        print("Handshake enviado, esperando respuesta...")
        response = s.recv(1024)
        print("Respuesta del servidor:", response.decode())

        print("Iniciando lectura de LIDAR y envío de datos...")
        while True:
            if not find_header():
                continue
            remaining_data = uart.read(FRAME_SIZE - 1)
            if not remaining_data or len(remaining_data) != FRAME_SIZE - 1:
                continue
            frame_data = bytes([HEADER]) + remaining_data
            points = parse_lidar_points_only(frame_data)
            if points:
                print("Puntos LIDAR procesados:", points)  # Depuración
                payload = {'points': points}
                send_websocket_message(s, payload)
    except Exception as e:
        print("Error en el cliente:", e)
    finally:
        s.close()
        print("Conexión cerrada")

if __name__ == "__main__":
    main()