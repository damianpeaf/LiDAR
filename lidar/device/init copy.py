from machine import Pin, PWM, UART
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

pan_servo = PWM(Pin(10))  # GP10: servo de paneo
tilt_servo = PWM(Pin(11))  # GP11: servo de inclinación
pan_servo.freq(50)
tilt_servo.freq(50)

def mover_servo(servo, angulo):
    duty_min = 1638    # ≈ 0.5 ms
    duty_max = 8192    # ≈ 2.5 ms
    duty = int(duty_min + (angulo / 180) * (duty_max - duty_min))
    servo.duty_u16(duty)

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

data = []

def enviar_datos_api():
    global data
    if not data:
        return
    try:
        data_str = ",".join([str(item) for item in sum(data, ())])
        headers = {'Content-Type': 'text/plain'}
        response = urequests.post(API_URL, data=data_str, headers=headers)
        response.close()
        print("Datos enviados exitosamente")
        data = []  # Clear data after successful send
    except Exception as e:
        print("Error enviando datos:", e)

def main():
    print("Iniciando WiFi y sistema de escaneo")
    conectar_wifi()

    tilt_max = 135
    tilt_actual = 0
    SENSOR_WAIT_MS = 10 

    mover_servo(pan_servo, 0)
    mover_servo(tilt_servo, tilt_actual)
    time.sleep(1)

    while tilt_actual <= tilt_max:
        # Paneo: 0 → 180
        for pan in range(0, 181, 1):
            mover_servo(pan_servo, pan)
            print(f"Paneo: {pan}°, Tilt: {tilt_actual}°")
            time.sleep_ms(SENSOR_WAIT_MS)
            result = read_lidar()
            if result:
                dist, strength = result
                data.append((dist, pan, tilt_actual, strength))
            time.sleep(0.01)

        tilt_actual += 1
        if tilt_actual <= tilt_max:
            mover_servo(tilt_servo, tilt_actual)
            time.sleep(0.2)

        enviar_datos_api()

        # Paneo: 180 → 0
        for pan in range(180, -1, -1):
            mover_servo(pan_servo, pan)
            print(f"Paneo: {pan}°, Tilt: {tilt_actual}°")
            time.sleep_ms(SENSOR_WAIT_MS)
            result = read_lidar()
            if result:
                dist, strength = result
                if strength > 10:
                    data.append((dist, pan, tilt_actual, strength))
            time.sleep(0.01)

        tilt_actual += 1
        if tilt_actual <= tilt_max:
            mover_servo(tilt_servo, tilt_actual)
            time.sleep(0.2)

        enviar_datos_api()

if __name__ == "__main__":
    main()