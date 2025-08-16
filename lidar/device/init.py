from machine import Pin, PWM, UART
import time
import network
import urequests
import _thread

SSID = "CLARO1_8E2AAB"
PASSWORD = ""
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

pan_servo = PWM(Pin(10))
tilt_servo = PWM(Pin(11))
pan_servo.freq(50)
tilt_servo.freq(50)

def mover_servo(servo, angulo):
    """
    Mueve el servo al ángulo especificado (0 a 180 grados)
    
    Parámetros:
    servo: Objeto PWM configurado para el servo
    angulo: Ángulo deseado en grados (0-180)
    """
    # Validar el rango del ángulo
    if not 0 <= angulo <= 180:
        raise ValueError("El ángulo debe estar entre 0 y 180 grados")
    
    # Calcular el duty cycle (ancho de pulso)
    # MG996R: 500µs (0°) a 2500µs (180°)
    # Escala de 16 bits (65535) para Raspberry Pi Pico
    pulse_min = 1638   # 500µs / 20ms * 65535 ≈ 1638
    pulse_max = 8192   # 2500µs / 20ms * 65535 ≈ 8192
    
    # Convertir ángulo a valor PWM
    duty = int(pulse_min + (pulse_max - pulse_min) * (angulo / 180))
    
    # Aplicar el duty cycle al servo
    servo.duty_u16(duty)
    
    # Pequeña pausa para permitir que el servo alcance la posición
    time.sleep_ms(20)

uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))

def read_lidar():
    if uart1.any():
        uart1.read()
    timeout = 0
    while uart1.any() < 9 and timeout < 100:
        time.sleep_ms(1)
        timeout += 1
    if uart1.any() < 9:
        return None
    data = uart1.read(9)
    if not data or len(data) < 9:
        return None
    if data[0] != 0x59 or data[1] != 0x59:
        return None
    checksum = sum(data[:8]) & 0xFF
    if checksum != data[8]:
        return None
    dist = data[2] | (data[3] << 8)
    strength = data[4] | (data[5] << 8)
    return (dist, strength)

data = []
data_lock = _thread.allocate_lock()
send_pending = False

def enviar_datos_worker():
    global data, send_pending
    while True:
        if send_pending:
            with data_lock:
                if data:
                    try:
                        data_str = ",".join([str(item) for item in sum(data, ())])
                        headers = {'Content-Type': 'text/plain'}
                        response = urequests.post(API_URL, data=data_str, headers=headers)
                        response.close()
                        print("Datos enviados exitosamente")
                        data = []
                        send_pending = False
                    except Exception as e:
                        print("Error enviando datos:", e)
                        send_pending = False
        time.sleep_ms(100)

def trigger_send():
    global send_pending
    send_pending = True

def main():
    print("Iniciando WiFi y sistema de escaneo")
    conectar_wifi()
    print("WiFi conectado")

    _thread.start_new_thread(enviar_datos_worker, ())

    tilt_max = 135
    tilt_actual = 0
    
    mover_servo(pan_servo, 0)
    mover_servo(tilt_servo, tilt_actual)

    print("Posicionando servos...")
    time.sleep(2)
    print("Comenzando escaneo LIDAR...")

    while tilt_actual <= tilt_max:
        for pan in range(0, 181, 1):
            mover_servo(pan_servo, pan)
            print(f"Paneo: {pan}°, Tilt: {tilt_actual}°")
            result = read_lidar()
            if result:
                dist, strength = result
                with data_lock:
                    data.append((dist, pan, tilt_actual, strength))

        tilt_actual += 1
        if tilt_actual <= tilt_max:
            mover_servo(tilt_servo, tilt_actual)

        trigger_send()

        for pan in range(180, -1, -1):
            mover_servo(pan_servo, pan)
            print(f"Paneo: {pan}°, Tilt: {tilt_actual}°")
            result = read_lidar()
            if result:
                dist, strength = result
                if strength > 10:
                    with data_lock:
                        data.append((dist, pan, tilt_actual, strength))

        tilt_actual += 1
        if tilt_actual <= tilt_max:
            mover_servo(tilt_servo, tilt_actual)

        trigger_send()

if __name__ == "__main__":
    main()