from machine import Pin, PWM, UART
import time

# ---- Configuración del servo ----
SERVO_PIN = 10

def angle_to_duty_u16(angle):
    pulse_ms = 0.5 + (angle / 180.0) * 2.0  # de 0.5ms a 2.5ms
    duty = int((pulse_ms / 20.0) * 65535)   # PWM de 50Hz
    return duty

servo_pwm = PWM(Pin(SERVO_PIN))
servo_pwm.freq(50)

def set_servo_angle(angle):
    # Asegurar que el ángulo esté en el rango válido
    angle = max(0, min(180, angle))
    servo_pwm.duty_u16(angle_to_duty_u16(angle))

# ---- Configuración del motor paso a paso ----
IN1 = Pin(4, Pin.OUT)
IN2 = Pin(5, Pin.OUT)
IN3 = Pin(6, Pin.OUT)
IN4 = Pin(7, Pin.OUT)

# Lista de pines para facilitar el control
motor_pins = [IN1, IN2, IN3, IN4]

# Inicializar todos los pines a OFF para evitar corrientes de retención al inicio
for pin in motor_pins:
    pin.value(0)

# Secuencia para el control del motor (secuencia de mayor torque que funcionó)
step_sequence = [
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 1],
    [1, 0, 0, 1]
]

# Función para establecer los pines según la secuencia
def set_step(step):
    for i in range(4):
        motor_pins[i].value(step[i])
    
    # Tiempo de espera después de establecer los pines
    time.sleep_ms(10)  # 10ms para permitir que el motor desarrolle torque

# Función para girar el motor en sentido horario
def rotate_clockwise(degrees):
    steps_per_degree = 1  # Ajustar según la calibración de tu motor
    
    for angle in range(degrees):
        # Dar un paso
        for step in step_sequence:
            set_step(step)
    
    # Apagar todos los pines al finalizar para evitar sobrecalentamiento
    for pin in motor_pins:
        pin.value(0)

# Función para girar el motor en sentido antihorario
def rotate_counterclockwise(degrees):
    steps_per_degree = 1  # Ajustar según la calibración de tu motor
    
    for angle in range(degrees):
        # Dar un paso
        for step in reversed(step_sequence):
            set_step(step)
    
    # Apagar todos los pines al finalizar para evitar sobrecalentamiento
    for pin in motor_pins:
        pin.value(0)

# ---- Configuración del LiDAR ----
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
lidar_buffer = bytearray(9)

def read_lidar():
    # Vaciar el buffer de recepción
    if uart1.any():
        uart1.read()
    
    # Esperar datos nuevos
    timeout = 0
    while uart1.any() < 9 and timeout < 100:
        time.sleep_ms(1)
        timeout += 1
    
    if uart1.any() < 9:
        return None
    
    # Leer la trama completa
    data = uart1.read(9)
    if not data or len(data) < 9:
        return None
    
    # Verificar cabecera
    if data[0] != 0x59 or data[1] != 0x59:
        return None
    
    # Verificar checksum
    checksum = sum(data[:8]) & 0xFF
    if checksum != data[8]:
        return None
    
    dist = data[2] | (data[3] << 8)
    strength = data[4] | (data[5] << 8)
    return (dist, strength)

# ---- Escaneo ----
MAX_VERTICAL_ANGLE = 120
MIN_VERTICAL_ANGLE = 0
VERTICAL_STEP = 1  # Incremento de 1° para el cabeceo
HORIZONTAL_STEP = 1  # Incremento de 1° para el giro horizontal

# Tiempo de espera para mejor estabilidad y lectura del sensor
SENSOR_WAIT_MS = 100  # Mayor tiempo para asegurar estabilidad mecánica antes de la lectura

def scan_forward():
    """Escanea de 0 a 180 grados (sentido horario)"""
    for theta in range(0, 181, HORIZONTAL_STEP):
        # Realizar la medición
        time.sleep_ms(SENSOR_WAIT_MS)
        result = read_lidar()
        
        if result:
            dist, strength = result
            # Solo registrar lecturas válidas (con fuerza de señal adecuada)
            if strength > 10:  # Umbral ajustable según el sensor
                print(f'{{"r":{dist},"theta":{theta},"phi":{current_vertical_angle},"strength":{strength}}}')
        
        # Mover el motor al siguiente ángulo horizontal (solo si no es el último)
        if theta < 180:
            rotate_clockwise(HORIZONTAL_STEP)

def scan_backward():
    """Escanea de 180 a 0 grados (sentido antihorario)"""
    for theta in range(180, -1, -HORIZONTAL_STEP):
        # Realizar la medición
        time.sleep_ms(SENSOR_WAIT_MS)
        result = read_lidar()
        
        if result:
            dist, strength = result
            # Solo registrar lecturas válidas (con fuerza de señal adecuada)
            if strength > 10:  # Umbral ajustable según el sensor
                print(f'{{"r":{dist},"theta":{theta},"phi":{current_vertical_angle},"strength":{strength}}}')
        
        # Mover el motor al siguiente ángulo horizontal (solo si no es el último)
        if theta > 0:
            rotate_counterclockwise(HORIZONTAL_STEP)

# ---- Main ----
def main():
    print("Sistema de escaneo LIDAR iniciado")
    
    global current_vertical_angle
    # Inicializar posición vertical
    current_vertical_angle = MAX_VERTICAL_ANGLE
    set_servo_angle(current_vertical_angle)
    time.sleep_ms(500)  # Tiempo para estabilización
    
    # Bucle principal continuo
    while True:
        # 1) Escaneo de 0 a 180 grados (sentido horario)
        scan_forward()
        
        # 2) Bajar un grado el cabeceo
        current_vertical_angle -= VERTICAL_STEP
        if current_vertical_angle < MIN_VERTICAL_ANGLE:
            current_vertical_angle = MAX_VERTICAL_ANGLE  # Reiniciar al máximo cuando llegue al mínimo
        set_servo_angle(current_vertical_angle)
        time.sleep_ms(100)  # Tiempo para que el servo se estabilice
        
        # 3) Escaneo de 180 a 0 grados (sentido antihorario)
        scan_backward()
        
        # 4) Bajar un grado el cabeceo
        current_vertical_angle -= VERTICAL_STEP
        if current_vertical_angle < MIN_VERTICAL_ANGLE:
            current_vertical_angle = MAX_VERTICAL_ANGLE  # Reiniciar al máximo cuando llegue al mínimo
        set_servo_angle(current_vertical_angle)
        time.sleep_ms(100)  # Tiempo para que el servo se estabilice

# Variable global para el ángulo vertical actual
current_vertical_angle = MAX_VERTICAL_ANGLE

# Ejecutar el programa
if __name__ == "__main__":
    main()