import os
import math
import asyncio
import websockets
import redis.asyncio as redis
import json
import uuid
from datetime import datetime

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_KEY = "lidar_points"

web_clients = set()
redis_client = None

async def init_redis():
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    print("Conexión a Redis establecida")

def parse_sensor_data(message):
    try:
        inclination_groups = message.strip().split('|')
        
        all_points = []
        current_inclination = None
        
        for group_index, group in enumerate(inclination_groups):
            if not group:
                continue
            
            parts = group.split(';')
            if not parts:
                continue
            
            if group_index == 0:
                try:
                    current_inclination = float(parts[0])
                    data_parts = parts[1:]  
                except (ValueError, IndexError):
                    continue
            else:
                data_parts = parts
                
                if len(data_parts) % 3 == 1:
                    try:
                        new_inclination = float(data_parts[-1])
                        data_parts = data_parts[:-1]  
                    except ValueError:
                        pass
            
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

async def store_points_in_redis(points):
    """Almacena los puntos en Redis sin sobreescribir"""
    try:
        for point in points:
            # Generar ID único para cada punto
            point_id = str(uuid.uuid4())
            point_data = {
                **point,
                'id': point_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Usar HSET para almacenar cada punto con su ID único
            await redis_client.hset(REDIS_KEY, point_id, json.dumps(point_data))
        
        print(f"Almacenados {len(points)} puntos en Redis")
    except Exception as e:
        print(f"Error almacenando en Redis: {e}")

async def get_all_points_from_redis():
    """Obtiene todos los puntos almacenados en Redis"""
    try:
        all_points_data = await redis_client.hgetall(REDIS_KEY)
        points = []
        
        for point_json in all_points_data.values():
            try:
                point = json.loads(point_json)
                # Solo enviar los datos necesarios al cliente
                points.append({
                    'intensity': point['intensity'],
                    'x': point['x'],
                    'y': point['y'],
                    'z': point['z']
                })
            except json.JSONDecodeError as e:
                print(f"Error parseando punto desde Redis: {e}")
        
        return points
    except Exception as e:
        print(f"Error obteniendo puntos de Redis: {e}")
        return []

async def clear_points_from_redis():
    """Limpia todos los puntos del escaneo en Redis"""
    try:
        await redis_client.delete(REDIS_KEY)
        print("Puntos limpiados de Redis")
        return True
    except Exception as e:
        print(f"Error limpiando Redis: {e}")
        return False

async def broadcast_to_web_clients(data, message_type="new_points"):
    """Envía datos a todos los clientes web conectados"""
    if web_clients:
        message = json.dumps({
            'type': message_type,
            'data': data
        })
        
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

async def handle_web_client_message(ws, data):
    """Maneja mensajes específicos del cliente web"""
    message_type = data.get('type')
    
    if message_type == 'register' and data.get('client') == 'web':
        web_clients.add(ws)
        print(f"Cliente web registrado: {ws.remote_address}")
        
        # Enviar estado actual al cliente recién conectado
        current_points = await get_all_points_from_redis()
        if current_points:
            await ws.send(json.dumps({
                'type': 'initial_state',
                'data': current_points
            }))
            print(f"Estado inicial enviado: {len(current_points)} puntos")
        else:
            await ws.send(json.dumps({
                'type': 'initial_state',
                'data': []
            }))
    
    elif message_type == 'clear_scan':
        print(f"Solicitud de limpieza de escaneo de: {ws.remote_address}")
        success = await clear_points_from_redis()
        
        if success:
            # Notificar a todos los clientes web que se limpiaron los datos
            await broadcast_to_web_clients([], "scan_cleared")
            await ws.send(json.dumps({
                'type': 'clear_response',
                'success': True
            }))
        else:
            await ws.send(json.dumps({
                'type': 'clear_response',
                'success': False
            }))

async def server(ws):
    print("Cliente conectado:", ws.remote_address)
    try:
        async for message in ws:
            try:
                # Intentar parsear como JSON
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = None

                # Manejar mensajes de clientes web
                if data and isinstance(data, dict):
                    await handle_web_client_message(ws, data)
                
                # Manejar datos de sensor (Pico)
                elif isinstance(message, str) and ";" in message:
                    print(f"Cliente identificado como Pico: {ws.remote_address}")

                    sensor_points = parse_sensor_data(message)
                    
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

                        # Almacenar en Redis
                        await store_points_in_redis(processed_points)
                        
                        # Broadcast solo de los nuevos puntos
                        await broadcast_to_web_clients(processed_points, "new_points")

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
    # Inicializar Redis
    await init_redis()
    
    async with websockets.serve(server, "0.0.0.0", 3000):
        print("Servidor iniciado en ws://0.0.0.0:3000")
        print("Conexión a Redis establecida")
        print("Esperando conexiones...")
        print("- Clientes web deben enviar: {'type': 'register', 'client': 'web'}")
        print("- Clientes web pueden limpiar con: {'type': 'clear_scan'}")
        print("- Dispositivos Pico deben enviar datos en formato: inclinacion|distancia;intensidad;angulo;...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())