from machine import Pin, PWM, UART, Timer
import time
import network
import urequests

# ---- Config WiFi ----
SSID = "CLARO1_8E2AAB"  # Replace with your WiFi SSID
PASSWORD = "841qlCREpc"  # Replace with your WiFi password
API_URL = "http://192.168.1.18:3000/api/lidar-data"

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Conectado a WiFi:", wlan.ifconfig())

# Configuración de servos
pan_servo = PWM(Pin(10))  # GP10: servo de paneo
tilt_servo = PWM(Pin(11))  # GP11: servo de inclinación
pan_servo.freq(50)
tilt_servo.freq(50)

def mover_servo(servo, angulo):
    duty_min = 1638    # ≈ 0.5 ms
    duty_max = 8192    # ≈ 2.5 ms
    duty = int(duty_min + (angulo / 180) * (duty_max - duty_min))
    servo.duty_u16(duty)

# UART para LIDAR
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))  # GP8: TX, GP9: RX

def read_lidar_fast():
    """Lectura rápida del LIDAR sin timeouts largos"""
    if uart1.any() >= 9:
        data = uart1.read(9)
        if data and len(data) == 9 and data[0] == 0x59 and data[1] == 0x59:
            checksum = sum(data[:8]) & 0xFF
            if checksum == data[8]:
                dist = data[2] | (data[3] << 8)
                strength = data[4] | (data[5] << 8)
                return (dist, strength)
    return None

# Variables globales
data_buffer = []
scan_active = False
current_pan = 0.0
current_tilt = 0.0
pan_direction = 1  # 1 para adelante, -1 para atrás
tilt_increment = 0.5  # Incremento más pequeño para movimiento más suave

# Parámetros de velocidad ultra rápida
PAN_SPEED = 2.0  # Grados por step (más rápido)
TILT_SPEED = 0.5  # Grados por step para tilt
SCAN_INTERVAL_MS = 5  # Intervalo de escaneo en milisegundos (ultra rápido)

def enviar_datos_api():
    global data_buffer
    if not data_buffer:
        return
    
    try:
        # Enviar en lotes más grandes para eficiencia
        data_str = ",".join([str(item) for item in sum(data_buffer, ())])
        headers = {'Content-Type': 'text/plain'}
        response = urequests.post(API_URL, data=data_str, headers=headers)
        response.close()
        print(f"Enviados {len(data_buffer)} puntos")
        data_buffer = []
    except Exception as e:
        print("Error enviando datos:", e)

def scan_step():
    """Función que ejecuta un paso del escaneo continuo"""
    global current_pan, current_tilt, pan_direction, data_buffer, scan_active
    
    if not scan_active:
        return
    
    # Mover servo de paneo continuamente
    current_pan += PAN_SPEED * pan_direction
    
    # Cambiar dirección y avanzar tilt cuando llegue a los límites
    if current_pan >= 180:
        current_pan = 180
        pan_direction = -1
        current_tilt += TILT_SPEED
        
        # Enviar datos cada vez que completa una pasada
        if data_buffer:
            enviar_datos_api()
            
    elif current_pan <= 0:
        current_pan = 0
        pan_direction = 1
        current_tilt += TILT_SPEED
        
        # Enviar datos cada vez que completa una pasada
        if data_buffer:
            enviar_datos_api()
    
    # Verificar si terminó el escaneo
    if current_tilt > 135:
        scan_active = False
        print("Escaneo completado!")
        return
    
    # Mover servos a posiciones actuales
    mover_servo(pan_servo, int(current_pan))
    mover_servo(tilt_servo, int(current_tilt))
    
    # Leer LIDAR inmediatamente (sin esperas)
    result = read_lidar_fast()
    if result:
        dist, strength = result
        if strength > 10:  # Filtrar lecturas débiles
            data_buffer.append((dist, int(current_pan), int(current_tilt), strength))
    
    print(f"Pan: {current_pan:.1f}°, Tilt: {current_tilt:.1f}°, Buffer: {len(data_buffer)}")

# Timer para escaneo continuo ultra rápido
scan_timer = Timer()

def iniciar_escaneo_continuo():
    """Inicia el escaneo continuo ultra rápido"""
    global scan_active, current_pan, current_tilt, pan_direction
    
    print("Iniciando escaneo continuo ultra rápido...")
    
    # Reset de variables
    current_pan = 0.0
    current_tilt = 0.0
    pan_direction = 1
    scan_active = True
    
    # Posición inicial
    mover_servo(pan_servo, 0)
    mover_servo(tilt_servo, 0)
    time.sleep(0.5)  # Solo una espera inicial
    
    # Limpiar buffer UART
    uart1.read()
    
    # Iniciar timer para escaneo ultra rápido
    scan_timer.init(period=SCAN_INTERVAL_MS, mode=Timer.PERIODIC, callback=lambda t: scan_step())

def detener_escaneo():
    """Detiene el escaneo continuo"""
    global scan_active
    scan_active = False
    scan_timer.deinit()
    
    # Enviar datos restantes
    if data_buffer:
        enviar_datos_api()

def main():
    print("Iniciando sistema de escaneo LIDAR ultra rápido")
    conectar_wifi()
    
    try:
        iniciar_escaneo_continuo()
        
        # Mantener el programa corriendo
        while scan_active:
            time.sleep(0.1)  # Chequeo periódico mínimo
            
        # Enviar datos finales
        if data_buffer:
            enviar_datos_api()
            
        print("Escaneo completado!")
        
    except KeyboardInterrupt:
        print("Escaneo interrumpido por usuario")
        detener_escaneo()
    except Exception as e:
        print(f"Error durante escaneo: {e}")
        detener_escaneo()

if __name__ == "__main__":
    main()