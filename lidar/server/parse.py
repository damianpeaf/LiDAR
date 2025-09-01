


# Función alternativa más simple si el formato es más predecible
def parse_sensor_data_v2(message):
    """
    Versión alternativa asumiendo que la estructura es:
    inclinacion|datos;datos;...;nueva_inclinacion|datos;datos;...
    """
    try:
        all_points = []
        current_inclination = None
        
        # Dividir por "|"
        groups = message.strip().split('|')
        
        for group in groups:
            if not group:
                continue
                
            parts = group.split(';')
            
            # El primer elemento del primer grupo es siempre inclinación
            if current_inclination is None:
                current_inclination = float(parts[0])
                parts = parts[1:]
            
            # Procesar datos en grupos de 3
            i = 0
            while i + 2 < len(parts):
                try:
                    distance = float(parts[i])
                    intensity = float(parts[i + 1])
                    angle = float(parts[i + 2])
                    
                    all_points.append({
                        'inclination': current_inclination,
                        'distance': distance,
                        'intensity': intensity,
                        'pan_angle': angle
                    })
                    
                    i += 3
                except ValueError:
                    i += 1
                    continue
            
            # Si queda un elemento al final, es la nueva inclinación
            if i < len(parts):
                try:
                    current_inclination = float(parts[i])
                except ValueError:
                    pass
        
        return all_points
    
    except Exception as e:
        print(f"Error parseando datos del sensor: {e}")
        return []


# Pruebas
test_data = "90.0|1;1;1;2;2;2;91.0|3;3;3;4;4;4"

print("Versión 1:")
result1 = parse_sensor_data(test_data)
for point in result1:
    print(point)

print("\nVersionión 2:")
result2 = parse_sensor_data_v2(test_data)
for point in result2:
    print(point)