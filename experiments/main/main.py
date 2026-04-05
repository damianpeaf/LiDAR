from machine import Pin, PWM, UART
import time
import network
import urequests
# ---- Config WiFi ----
SSID = "CLARO1_8E2AAB"  # Replace with your WiFi SSID
PASSWORD = ""  # Replace with your WiFi password
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
# ---- Configuración de los servos ----
pan_servo = PWM(Pin(10))  # GP10: servo de paneo
tilt_servo = PWM(Pin(11))  # GP11: servo de inclinación
pan_servo.freq(50)
tilt_servo.freq(50)
def mover_servo(servo, angulo, angulo_max):
    duty_min = 1638    # ≈ 0.5 ms
    duty_max = 8192    # ≈ 2.5 ms
    duty = int(duty_min + (angulo / angulo_max) * (duty_max - duty_min))
    servo.duty_u16(duty)
# ---- LIDAR ----
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))  # GP8: TX, GP9: RX
def read_lidar():
    if uart1.any():
        uart1.read()  # Clear buffer
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
# ---- Enviar datos a la API ----
def enviar_datos_api(dist, theta, phi, strength):
    try:
        payload = {
            "r": dist,
            "theta": theta,
            "phi": phi,
            "strength": strength
        }
        response = urequests.post(API_URL, json=payload)
        response.close()
    except Exception as e:
        print("Error enviando datos:", e)
# ---- Bucle de barrido esférico ----
def main():
    print("Iniciando WiFi y sistema de escaneo")
    conectar_wifi()

    # Variables locales de la función
    tilt_max = 135
    tilt_actual = 0
    SENSOR_WAIT_MS = 10  # Wait time for LIDAR sensor

    mover_servo(pan_servo, 0, 180)
    mover_servo(tilt_servo, tilt_actual, tilt_max)
    time.sleep(1)

    while tilt_actual <= tilt_max:
        # Paneo: 0 → 180
        for pan in range(0, 181, 1):
            mover_servo(pan_servo, pan, 180)
            print(f"Paneo: {pan}°, Tilt: {tilt_actual}°")
            time.sleep_ms(SENSOR_WAIT_MS)
            result = read_lidar()
            if result:
                dist, strength = result
                if strength > 10:
                    enviar_datos_api(dist, pan, tilt_actual, strength)
            time.sleep(0.05)

        # Subir tilt en 1°
        tilt_actual += 1
        if tilt_actual <= tilt_max:
            mover_servo(tilt_servo, tilt_actual, tilt_max)
            time.sleep(0.2)

        # Paneo: 180 → 0
        for pan in range(180, -1, -1):
            mover_servo(pan_servo, pan, 180)
            print(f"Paneo: {pan}°, Tilt: {tilt_actual}°")
            time.sleep_ms(SENSOR_WAIT_MS)
            result = read_lidar()
            if result:
                dist, strength = result
                if strength > 10:
                    enviar_datos_api(dist, pan, tilt_actual, strength)
            time.sleep(0.05)

        # Subir tilt en 1°
        tilt_actual += 1
        if tilt_actual <= tilt_max:
            mover_servo(tilt_servo, tilt_actual, tilt_max)
            time.sleep(0.2)

if __name__ == "__main__":
    main()
