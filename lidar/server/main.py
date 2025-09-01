import os
import math
import asyncio
import websockets
import json


web_clients = set()

def parse_sensor_data(message):
    try:
        # Dividir por "|" para obtener los grupos de inclinación
        inclination_groups = message.strip().split('|')
        
        all_points = []
        current_inclination = None
        
        for group_index, group in enumerate(inclination_groups):
            if not group:
                continue
            
            parts = group.split(';')
            if not parts:
                continue
            
            # Si es el primer grupo, el primer elemento es la inclinación
            if group_index == 0:
                try:
                    current_inclination = float(parts[0])
                    data_parts = parts[1:]  # Los datos empiezan desde el índice 1
                except (ValueError, IndexError):
                    continue
            else:
                # Para grupos posteriores, todos los elementos son datos
                # EXCEPTO posiblemente el último que podría ser la nueva inclinación
                data_parts = parts
                
                # Verificar si el último elemento puede ser una nueva inclinación
                # Si el número de elementos no es múltiplo de 3, el último podría ser inclinación
                if len(data_parts) % 3 == 1:
                    try:
                        # El último elemento podría ser la nueva inclinación
                        new_inclination = float(data_parts[-1])
                        data_parts = data_parts[:-1]  # Remover la inclinación de los datos
                    except ValueError:
                        # Si no se puede convertir a float, no es inclinación
                        pass
            
            # Procesar los puntos de datos (grupos de 3: distancia, intensidad, ángulo)
            for i in range(0, len(data_parts), 3):
                if i + 2 < len(data_parts):
                    try:
                        distance = float(data_parts[i])
                        intensity = float(data_parts[i + 1])
                        angle = float(data_parts[i + 2])
                        
                        all_points.append({
                            'inclination': current_inclination,
                            'distance': distance,
                            'intensity': intensity,
                            'pan_angle': angle
                        })
                    except ValueError:
                        continue
            
            # Si encontramos una nueva inclinación al final, actualizarla
            if group_index > 0 and len(parts) % 3 == 1:
                try:
                    current_inclination = float(parts[-1])
                except ValueError:
                    pass
        
        return all_points
    
    except Exception as e:
        print(f"Error parseando datos del sensor: {e}")
        return []

def convert_to_cartesian(inclination, pan_angle, distance, wheel_base=15.35):
 
    inc_rad = math.radians(inclination)
    pan_rad = math.radians(pan_angle)
    
    
    x = wheel_base * math.cos(inc_rad) + distance * math.cos(pan_rad) * math.sin(inc_rad)
    y = distance * math.sin(pan_rad)
    z = wheel_base * math.sin(inc_rad) - distance * math.cos(pan_rad) * math.cos(inc_rad)
    
    return x, y, z

async def broadcast_to_web_clients(data):
  
  
    if web_clients:
        
        message = json.dumps(data)
        
        
        disconnected = []
        
        for client in web_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosedError:
                disconnected.append(client)
            except Exception as e:
                print(f"Error enviando a cliente web: {e}")
                disconnected.append(client)
        
        
        for client in disconnected:
            web_clients.discard(client)


def save_points_to_file(points, filename="sensor_points.json"):
    """
    Guarda puntos en un archivo JSON, agregándolos a los existentes
    en lugar de sobrescribirlos.
    """
    try:
        # Leer puntos existentes si el archivo ya existe
        existing_points = []
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    existing_points = json.load(f)
                    # Asegurar que existing_points es una lista
                    if not isinstance(existing_points, list):
                        existing_points = []
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error leyendo archivo existente {filename}: {e}")
                print("Creando archivo nuevo...")
                existing_points = []

        # Agregar los nuevos puntos
        existing_points.extend(points)

        # Guardar todos los puntos nuevamente
        with open(filename, "w") as f:
            json.dump(existing_points, f, indent=4)

        print(f"Guardados {len(points)} nuevos puntos. Total de puntos en {filename}: {len(existing_points)}")
        
    except Exception as e:
        print(f"Error guardando puntos en {filename}: {e}")


async def server(ws):
    print("Cliente conectado:", ws.remote_address)
    try:
        async for message in ws:
            try:
                
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = None

                
                if data and data.get('type') == 'register' and data.get('client') == 'web':
                    web_clients.add(ws)
                    print(f"Cliente web registrado: {ws.remote_address}")
                    

                
                elif isinstance(message, str) and ";" in message:
                    print(f"Cliente identificado como Pico: {ws.remote_address}")

                    sensor_points = parse_sensor_data(message)
                    # print(sensor_points)
                    
                    if sensor_points:
                        print(f"Puntos parseados: {len(sensor_points)}")
                        
                        
                        processed_points = []
                        wheelBase = 15.35
                        
                        for point in sensor_points:
                            inclination = point['inclination']
                            panAngle = point['pan_angle']
                            distance = point['distance']
                            intensity = point['intensity']
                            
                            
                            x, y, z = convert_to_cartesian(inclination, panAngle, distance, wheelBase)
                            
                            processed_point = {
                                'intensity': intensity,
                                'x': round(x, 2),
                                'y': round(y, 2),
                                'z': round(z, 2)
                            }
                            
                            processed_points.append(processed_point)
                        
                        print(f"Puntos procesados: {len(processed_points)}")

                        await broadcast_to_web_clients(processed_points)
                        # save_points_to_file(processed_points)

                    else:
                        print("No se pudieron parsear datos válidos del sensor")
                        await ws.send("ERROR:PARSE_FAILED")

                else:
                    print(f"Mensaje desconocido de {ws.remote_address}: {message}")
                    if not data:  
                        await ws.send("ERROR:UNKNOWN_FORMAT")

            except Exception as e:
                print(f"Error procesando mensaje: {e}")
                try:
                    await ws.send(f"ERROR:{str(e)}")
                except:
                    pass

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Conexión cerrada: {e}")
    except Exception as e:
        print(f"Error en el servidor: {e}")
    finally:
        web_clients.discard(ws)
        print(f"Cliente desconectado: {ws.remote_address}")

async def main():
    async with websockets.serve(server, "0.0.0.0", 3000):
        print("Servidor iniciado en ws://0.0.0.0:3000")
        print("Esperando conexiones...")
        print("- Clientes web deben enviar: {'type': 'register', 'client': 'web'}")
        print("- Dispositivos Pico deben enviar datos en formato: inclinacion|distancia;intensidad;angulo;...")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())