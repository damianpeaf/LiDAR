from machine import Pin, UART
import struct
import time

# Configuración UART para LIDAR
uart = UART(1, 230400, tx=Pin(8), rx=Pin(9))

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

# Variables de estadísticas
class PerformanceStats:
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        
        # Contadores de datos
        self.bytes_received = 0
        self.bytes_processed = 0
        self.frames_received = 0
        self.frames_processed = 0
        self.points_processed = 0
        
        # Errores
        self.header_errors = 0
        self.size_errors = 0
        self.crc_errors = 0
        self.timeout_errors = 0
        
        # Métricas de rendimiento
        self.min_frame_time = float('inf')
        self.max_frame_time = 0
        self.total_frame_time = 0
        self.frame_times = []
        
        # Datos del LIDAR
        self.min_angle = 360
        self.max_angle = 0
        self.angle_range_covered = set()
        self.min_distance = float('inf')
        self.max_distance = 0
        self.min_intensity = 255
        self.max_intensity = 0
        self.total_intensity = 0
        
        # Tiempos de operaciones
        self.crc_calc_time = 0
        self.parsing_time = 0
        self.uart_read_time = 0

stats = PerformanceStats()

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
    parse_start = time.ticks_us()
    
    # Verificar tamaño
    if len(data) != FRAME_SIZE:
        stats.size_errors += 1
        return None
    
    # Verificar header
    if data[0] != HEADER:
        stats.header_errors += 1
        return None
    
    # Verificar CRC
    crc_start = time.ticks_us()
    if calc_crc8(data[:-1]) != data[-1]:
        stats.crc_calc_time += time.ticks_diff(time.ticks_us(), crc_start)
        stats.crc_errors += 1
        return None
    stats.crc_calc_time += time.ticks_diff(time.ticks_us(), crc_start)
    
    # Procesar datos
    start_angle = struct.unpack('<H', data[4:6])[0]
    end_angle = struct.unpack('<H', data[42:44])[0]
    start_angle_norm = normalize_angle(start_angle)
    end_angle_norm = normalize_angle(end_angle)
    
    # Actualizar estadísticas de ángulos
    stats.min_angle = min(stats.min_angle, start_angle_norm)
    stats.max_angle = max(stats.max_angle, end_angle_norm)
    stats.angle_range_covered.add(int(start_angle_norm))
    stats.angle_range_covered.add(int(end_angle_norm))
    
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
            
            # Actualizar estadísticas de puntos
            stats.points_processed += 1
            stats.min_distance = min(stats.min_distance, distance)
            stats.max_distance = max(stats.max_distance, distance)
            stats.min_intensity = min(stats.min_intensity, intensity)
            stats.max_intensity = max(stats.max_intensity, intensity)
            stats.total_intensity += intensity
    
    stats.parsing_time += time.ticks_diff(time.ticks_us(), parse_start)
    return points

def find_header():
    timeout_start = time.ticks_ms()
    while True:
        uart_start = time.ticks_us()
        byte = uart.read(1)
        stats.uart_read_time += time.ticks_diff(time.ticks_us(), uart_start)
        
        if byte:
            stats.bytes_received += 1
            if byte[0] == HEADER:
                return True
        
        # Timeout después de 100ms sin datos
        if time.ticks_diff(time.ticks_ms(), timeout_start) > 100:
            stats.timeout_errors += 1
            timeout_start = time.ticks_ms()

def print_performance_report():
    runtime = time.ticks_diff(stats.end_time, stats.start_time) / 1000.0  # En segundos
    
    print("\n" + "="*60)
    print("REPORTE DE RENDIMIENTO - LIDAR MICROPYTHON")
    print("="*60)
    
    print(f"Tiempo de ejecución: {runtime:.2f} segundos")
    print(f"Frecuencia de muestreo UART: 230400 baud")
    
    print("\n--- DATOS PROCESADOS ---")
    print(f"Bytes recibidos: {stats.bytes_received:,}")
    print(f"Bytes procesados: {stats.bytes_processed:,}")
    print(f"Frames recibidos: {stats.frames_received:,}")
    print(f"Frames procesados exitosos: {stats.frames_processed:,}")
    print(f"Puntos LIDAR procesados: {stats.points_processed:,}")
    
    print("\n--- TASAS DE PROCESAMIENTO ---")
    if runtime > 0:
        print(f"Bytes/s: {stats.bytes_received / runtime:,.0f}")
        print(f"Frames/s: {stats.frames_processed / runtime:.1f}")
        print(f"Puntos/s: {stats.points_processed / runtime:,.0f}")
    
    print("\n--- ERRORES ---")
    print(f"Errores de header: {stats.header_errors:,}")
    print(f"Errores de tamaño: {stats.size_errors:,}")
    print(f"Errores de CRC: {stats.crc_errors:,}")
    print(f"Timeouts UART: {stats.timeout_errors:,}")
    
    error_rate = ((stats.header_errors + stats.size_errors + stats.crc_errors) / 
                  max(stats.frames_received, 1)) * 100
    print(f"Tasa de error: {error_rate:.2f}%")
    
    print("\n--- TIEMPOS DE OPERACIÓN (microsegundos) ---")
    print(f"Tiempo total en cálculo CRC: {stats.crc_calc_time:,}")
    print(f"Tiempo total en parsing: {stats.parsing_time:,}")
    print(f"Tiempo total en lectura UART: {stats.uart_read_time:,}")
    
    if stats.frames_processed > 0:
        avg_frame_time = stats.total_frame_time / stats.frames_processed
        print(f"Tiempo promedio por frame: {avg_frame_time:.0f} µs")
        print(f"Tiempo mínimo por frame: {stats.min_frame_time:.0f} µs")
        print(f"Tiempo máximo por frame: {stats.max_frame_time:.0f} µs")
        
        avg_crc_time = stats.crc_calc_time / stats.frames_processed
        avg_parse_time = stats.parsing_time / stats.frames_processed
        print(f"Tiempo promedio CRC por frame: {avg_crc_time:.0f} µs")
        print(f"Tiempo promedio parsing por frame: {avg_parse_time:.0f} µs")
    
    print("\n--- DATOS DEL LIDAR ---")
    print(f"Rango de ángulos: {stats.min_angle:.1f}° - {stats.max_angle:.1f}°")
    print(f"Ángulos únicos cubiertos: {len(stats.angle_range_covered)}")
    print(f"Cobertura angular: {(len(stats.angle_range_covered)/360)*100:.1f}%")
    
    if stats.points_processed > 0:
        print(f"Distancia mínima: {stats.min_distance} mm")
        print(f"Distancia máxima: {stats.max_distance} mm")
        print(f"Intensidad mínima: {stats.min_intensity}")
        print(f"Intensidad máxima: {stats.max_intensity}")
        print(f"Intensidad promedio: {stats.total_intensity / stats.points_processed:.1f}")
    
    print("\n--- EFICIENCIA ---")
    success_rate = (stats.frames_processed / max(stats.frames_received, 1)) * 100
    print(f"Tasa de éxito de frames: {success_rate:.2f}%")
    
    if runtime > 0:
        cpu_util_crc = (stats.crc_calc_time / 1000000) / runtime * 100
        cpu_util_parse = (stats.parsing_time / 1000000) / runtime * 100
        cpu_util_uart = (stats.uart_read_time / 1000000) / runtime * 100
        print(f"CPU usado en CRC: {cpu_util_crc:.2f}%")
        print(f"CPU usado en parsing: {cpu_util_parse:.2f}%")
        print(f"CPU usado en UART: {cpu_util_uart:.2f}%")
    
    print("="*60)

def main():
    uart.read()  # Limpiar buffer UART
    stats.start_time = time.ticks_ms()
    
    # Ejecutar por 30 segundos para obtener métricas representativas
    test_duration = 30000  # 30 segundos en ms
    
    try:
        while time.ticks_diff(time.ticks_ms(), stats.start_time) < test_duration:
            frame_start = time.ticks_us()
            
            if not find_header():
                continue
            
            uart_start = time.ticks_us()
            remaining_data = uart.read(FRAME_SIZE - 1)
            stats.uart_read_time += time.ticks_diff(time.ticks_us(), uart_start)
            
            if not remaining_data or len(remaining_data) != FRAME_SIZE - 1:
                stats.size_errors += 1
                continue
            
            frame_data = bytes([HEADER]) + remaining_data
            stats.bytes_received += len(remaining_data)
            stats.bytes_processed += FRAME_SIZE
            stats.frames_received += 1
            
            points = parse_lidar_points_only(frame_data)
            if points:
                stats.frames_processed += 1
                
                # Calcular tiempo de frame
                frame_time = time.ticks_diff(time.ticks_us(), frame_start)
                stats.min_frame_time = min(stats.min_frame_time, frame_time)
                stats.max_frame_time = max(stats.max_frame_time, frame_time)
                stats.total_frame_time += frame_time
            
    except KeyboardInterrupt:
        pass
    finally:
        stats.end_time = time.ticks_ms()
        print_performance_report()

if __name__ == "__main__":
    main()