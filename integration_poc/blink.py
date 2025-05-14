from machine import Pin, PWM, UART
import time
import network
import urequests

# ---- Config WiFi ----
SSID = "TIGO-DBFB"
PASSWORD = "4D9667308433"
API_URL = "http://192.168.0.7:3000/api/lidar-data"

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Conectado a WiFi:", wlan.ifconfig())

# ---- Configuración del servo ----
SERVO_PIN = 10

def angle_to_duty_u16(angle):
    pulse_ms = 0.5 + (angle / 180.0) * 2.0
    duty = int((pulse_ms / 20.0) * 65535)
    return duty

servo_pwm = PWM(Pin(SERVO_PIN))
servo_pwm.freq(50)

def set_servo_angle(angle):
    angle = max(0, min(180, angle))
    servo_pwm.duty_u16(angle_to_duty_u16(angle))

# ---- Motor paso a paso ----
IN1 = Pin(4, Pin.OUT)
IN2 = Pin(5, Pin.OUT)
IN3 = Pin(6, Pin.OUT)
IN4 = Pin(7, Pin.OUT)
motor_pins = [IN1, IN2, IN3, IN4]

for pin in motor_pins:
    pin.value(0)

step_sequence = [
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 1],
    [1, 0, 0, 1]
]

def set_step(step):
    for i in range(4):
        motor_pins[i].value(step[i])
    time.sleep_ms(10)

def rotate_clockwise(degrees):
    for angle in range(degrees):
        for step in step_sequence:
            set_step(step)
    for pin in motor_pins:
        pin.value(0)

def rotate_counterclockwise(degrees):
    for angle in range(degrees):
        for step in reversed(step_sequence):
            set_step(step)
    for pin in motor_pins:
        pin.value(0)

# ---- LIDAR ----
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

# ---- Escaneo ----
MAX_VERTICAL_ANGLE = 120
MIN_VERTICAL_ANGLE = 0
VERTICAL_STEP = 1
HORIZONTAL_STEP = 1
SENSOR_WAIT_MS = 100

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

def scan_forward():
    for theta in range(0, 181, HORIZONTAL_STEP):
        time.sleep_ms(SENSOR_WAIT_MS)
        result = read_lidar()
        if result:
            dist, strength = result
            if strength > 10:
                enviar_datos_api(dist, theta, current_vertical_angle, strength)
        if theta < 180:
            rotate_clockwise(HORIZONTAL_STEP)

def scan_backward():
    for theta in range(180, -1, -HORIZONTAL_STEP):
        time.sleep_ms(SENSOR_WAIT_MS)
        result = read_lidar()
        if result:
            dist, strength = result
            if strength > 10:
                enviar_datos_api(dist, theta, current_vertical_angle, strength)
        if theta > 0:
            rotate_counterclockwise(HORIZONTAL_STEP)

# ---- Main ----
def main():
    print("Iniciando WiFi y sistema de escaneo")
    conectar_wifi()
    global current_vertical_angle
    current_vertical_angle = MAX_VERTICAL_ANGLE
    set_servo_angle(current_vertical_angle)
    time.sleep_ms(500)
    
    while True:
        scan_forward()
        current_vertical_angle -= VERTICAL_STEP
        if current_vertical_angle < MIN_VERTICAL_ANGLE:
            current_vertical_angle = MAX_VERTICAL_ANGLE
        set_servo_angle(current_vertical_angle)
        time.sleep_ms(100)
        scan_backward()
        current_vertical_angle -= VERTICAL_STEP
        if current_vertical_angle < MIN_VERTICAL_ANGLE:
            current_vertical_angle = MAX_VERTICAL_ANGLE
        set_servo_angle(current_vertical_angle)
        time.sleep_ms(100)

current_vertical_angle = MAX_VERTICAL_ANGLE

if __name__ == "__main__":
    main()
