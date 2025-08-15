from machine import Pin, UART
import struct
import json
import network
import urequests
import time
import _thread
from time import sleep

uart = UART(1, 230400, tx=Pin(8), rx=Pin(9))

SSID = "CLARO1_8E2AAB"
PASSWORD = "841qlCREpc"
API_URL = "http://192.168.1.24:3000/api/ld19-lidar"

HEADER = 0x54
POINT_PER_PACK = 12
FRAME_SIZE = 47

data_buffer = []
buffer_lock = False

SEND_INTERVAL = 2  # Reducido para enviar más frecuentemente
MAX_BUFFER_SIZE = 50  # Reducido para usar menos memoria

# Aquí colocarás manualmente la tabla CRC
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
    """Extrae solo los puntos con ángulo, distancia e intensidad"""
    if len(data) != FRAME_SIZE or data[0] != HEADER:
        return None
    
    if CRC_TABLE and calc_crc8(data[:-1]) != data[-1]:
        return None
    
    # Extraer ángulos de inicio y fin
    start_angle = struct.unpack('<H', data[4:6])[0]
    end_angle = struct.unpack('<H', data[42:44])[0]
    
    # Normalizar ángulos
    start_angle_norm = normalize_angle(start_angle)
    end_angle_norm = normalize_angle(end_angle)
    
    if end_angle_norm < start_angle_norm:
        end_angle_norm += 360
    
    # Calcular step angular
    step = (end_angle_norm - start_angle_norm) / (POINT_PER_PACK - 1) if POINT_PER_PACK > 1 else 0
    
    # Extraer solo los puntos
    points_data = data[6:42]
    points = []
    
    for i in range(POINT_PER_PACK):
        offset = i * 3
        distance, intensity = struct.unpack('<HB', points_data[offset:offset+3])
        
        # Calcular ángulo del punto
        angle = start_angle_norm + step * i
        if angle >= 360:
            angle -= 360
        
        # Solo agregar puntos válidos (con distancia > 0)
        if distance > 0:
            points.append({
                'a': round(angle, 1),      # ángulo (acortado)
                'd': distance,             # distancia
                'i': intensity             # intensidad
            })
    
    return points

def find_header():
    while True:
        byte = uart.read(1)
        if byte and byte[0] == HEADER:
            return True
        if not byte:
            sleep(0.001)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando WiFi...")
        wlan.connect(SSID, PASSWORD)
        timeout = 0
        while not wlan.isconnected() and timeout < 30:
            time.sleep(1)
            timeout += 1
        if wlan.isconnected():
            print("WiFi conectado:", wlan.ifconfig())
        else:
            print("Error: no se pudo conectar a WiFi")
        return wlan.isconnected()
    return True

def add_to_buffer(points):
    """Agrega solo los puntos al buffer"""
    global data_buffer, buffer_lock
    if not points:  # No agregar si no hay puntos válidos
        return
        
    while buffer_lock:
        sleep(0.001)
    buffer_lock = True
    try:
        # Agregar puntos directamente (no frames completos)
        data_buffer.extend(points)
        
        # Limitar tamaño del buffer
        if len(data_buffer) > MAX_BUFFER_SIZE:
            # Remover puntos más antiguos
            excess = len(data_buffer) - MAX_BUFFER_SIZE
            data_buffer = data_buffer[excess:]
    finally:
        buffer_lock = False

def get_buffer_data():
    """Obtiene todos los puntos del buffer"""
    global data_buffer, buffer_lock
    while buffer_lock:
        sleep(0.001)
    buffer_lock = True
    try:
        if data_buffer:
            data_copy = data_buffer[:]
            data_buffer = []
            return data_copy
        return []
    finally:
        buffer_lock = False

def enviar_datos_api():
    """Envía solo los puntos al API"""
    points_to_send = get_buffer_data()
    if not points_to_send:
        return
    
    try:
        # Payload simplificado - solo puntos
        payload = {
            'points': points_to_send
        }
        
        headers = {'Content-Type': 'application/json'}
        json_data = json.dumps(payload)
        
        res = urequests.post(API_URL, data=json_data, headers=headers)
        
        if res.status_code == 200:
            print(f"Enviados {len(points_to_send)} puntos")
        else:
            print(f"Error HTTP {res.status_code}")
        res.close()
        
    except Exception as e:
        print(f"Error enviando: {e}")

def api_sender_thread():
    """Hilo para enviar datos al API"""
    while True:
        try:
            enviar_datos_api()
            sleep(SEND_INTERVAL)
        except Exception as e:
            print(f"Error hilo API: {e}")
            sleep(SEND_INTERVAL)

def read_lidar_data_optimized():
    """Lee datos del LIDAR enviando solo puntos"""
    wifi_connected = False
    
    # Conectar WiFi
    if SSID and PASSWORD:
        wifi_connected = conectar_wifi()
        if wifi_connected and API_URL:
            try:
                _thread.start_new_thread(api_sender_thread, ())
                print("Hilo API iniciado")
            except Exception as e:
                print(f"Error iniciando hilo: {e}")
                wifi_connected = False
    
    try:
        while True:
            if not find_header():
                continue
            
            remaining_data = uart.read(FRAME_SIZE - 1)
            if not remaining_data or len(remaining_data) != FRAME_SIZE - 1:
                continue
            
            frame_data = bytes([HEADER]) + remaining_data
            
            # Extraer solo los puntos
            points = parse_lidar_points_only(frame_data)
            
            if points and wifi_connected and API_URL:
                add_to_buffer(points)
                    
    except KeyboardInterrupt:
        print("Detenido por el usuario")
        if wifi_connected and data_buffer:
            enviar_datos_api()

if __name__ == "__main__":
    uart.read()  # Limpiar buffer UART
    read_lidar_data_optimized()