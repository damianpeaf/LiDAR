import serial
import time

# Ajusta el puerto correcto
ser = serial.Serial('/dev/tty.usbmodem14101', 115200)  # Cambia el puerto según lo que encuentres

# Abre el archivo de salida
with open("salida_lidar.txt", "w") as f:
    print("Escuchando el puerto serial...")

    while True:
        # Lee la línea de datos desde la Raspberry Pi Pico
        line = ser.readline().decode('utf-8', errors='ignore')

        # Si hay datos, imprímelos en consola y guarda en el archivo
        if line:
            print(line.strip())  # Muestra los datos en la consola
            f.write(line)        # Guarda los datos en el archivo

        # Puedes agregar un pequeño retraso si lo deseas para no saturar el archivo
        time.sleep(0.1)  # Ajusta el tiempo de espera si es necesario
