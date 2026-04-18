import os
import math
import asyncio
import struct
import websockets
import redis.asyncio as redis
import json
import uuid
from datetime import datetime
from pathlib import Path

from validation import ValidationRun

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_KEY = "lidar_points"

BINARY_BATCH_MAGIC = b"PS"
BINARY_BATCH_VERSION = 1
BINARY_BATCH_HEADER_SIZE = 8
BINARY_POINT_RECORD_SIZE = 5

web_clients = set()
redis_client = None
validation_run = ValidationRun(Path(__file__).resolve().parent / "validation_runs")


async def init_redis():
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    print("Conexión a Redis establecida")


def parse_sensor_data(message):
    try:
        inclination_groups = message.strip().split("|")

        all_points = []
        current_inclination = None

        for group_index, group in enumerate(inclination_groups):
            if not group:
                continue

            parts = group.split(";")
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

                        all_points.append(
                            {
                                "inclination": current_inclination,
                                "distance": distance,
                                "intensity": intensity,
                                "pan_angle": angle,
                            }
                        )
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


def parse_binary_sensor_data(payload):
    try:
        if len(payload) < BINARY_BATCH_HEADER_SIZE:
            raise ValueError("payload too short")

        magic, version, flags, inclination_tenths, point_count = struct.unpack_from(
            "<2sBBhH", payload, 0
        )

        if magic != BINARY_BATCH_MAGIC:
            raise ValueError("invalid binary batch magic")

        if version != BINARY_BATCH_VERSION:
            raise ValueError(f"unsupported binary batch version: {version}")

        expected_size = (
            BINARY_BATCH_HEADER_SIZE + point_count * BINARY_POINT_RECORD_SIZE
        )
        if len(payload) != expected_size:
            raise ValueError(
                f"invalid payload size: expected {expected_size}, got {len(payload)}"
            )

        inclination = inclination_tenths / 10.0
        all_points = []

        offset = BINARY_BATCH_HEADER_SIZE
        for _ in range(point_count):
            distance, intensity, pan_angle_tenths = struct.unpack_from(
                "<HBH", payload, offset
            )
            offset += BINARY_POINT_RECORD_SIZE

            all_points.append(
                {
                    "inclination": inclination,
                    "distance": float(distance),
                    "intensity": float(intensity),
                    "pan_angle": pan_angle_tenths / 10.0,
                }
            )

        return all_points

    except Exception as e:
        print(f"Error parseando payload binario del sensor: {e}")
        return []


def convert_to_cartesian(inclination, pan_angle, distance, wheel_base=15.35):
    inc_rad = math.radians(inclination)
    pan_rad = math.radians(pan_angle)

    x = wheel_base * math.cos(inc_rad) + distance * math.cos(pan_rad) * math.sin(
        inc_rad
    )
    y = distance * math.sin(pan_rad)
    z = wheel_base * math.sin(inc_rad) - distance * math.cos(pan_rad) * math.cos(
        inc_rad
    )

    return x, y, z


async def store_points_in_redis(points):
    """Almacena los puntos en Redis sin sobreescribir"""
    try:
        for point in points:
            # Generar ID único para cada punto
            point_id = str(uuid.uuid4())
            point_data = {
                **point,
                "id": point_id,
                "timestamp": datetime.now().isoformat(),
            }

            # Usar HSET para almacenar cada punto con su ID único
            await redis_client.hset(REDIS_KEY, point_id, json.dumps(point_data))

        validation_run.increment("points_stored", len(points))
        print(f"Almacenados {len(points)} puntos en Redis")
    except Exception as e:
        validation_run.increment("redis_store_failures")
        validation_run.record_event(
            "redis_store_failed", error=str(e), points=len(points)
        )
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
                points.append(
                    {
                        "intensity": point["intensity"],
                        "x": point["x"],
                        "y": point["y"],
                        "z": point["z"],
                    }
                )
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
        message = json.dumps({"type": message_type, "data": data})

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

        if disconnected:
            validation_run.set_value("active_web_clients", len(web_clients))


def process_sensor_points(sensor_points):
    if not sensor_points:
        return []

    print(f"Puntos parseados: {len(sensor_points)}")

    processed_points = []
    wheel_base = 15.35

    for point in sensor_points:
        inclination = point["inclination"]
        pan_angle = point["pan_angle"]
        distance = point["distance"]
        intensity = point["intensity"]

        x, y, z = convert_to_cartesian(inclination, pan_angle, distance, wheel_base)

        processed_points.append(
            {
                "intensity": intensity,
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
            }
        )

    print(f"Puntos procesados: {len(processed_points)}")

    return processed_points


async def handle_web_client_message(ws, data):
    """Maneja mensajes específicos del cliente web"""
    message_type = data.get("type")

    if message_type == "register" and data.get("client") == "web":
        web_clients.add(ws)
        validation_run.increment("web_clients_registered")
        validation_run.set_value("active_web_clients", len(web_clients))
        validation_run.record_event(
            "web_client_registered", remote=str(ws.remote_address)
        )
        print(f"Cliente web registrado: {ws.remote_address}")

        # Enviar estado actual al cliente recién conectado
        current_points = await get_all_points_from_redis()
        if current_points:
            await ws.send(json.dumps({"type": "initial_state", "data": current_points}))
            print(f"Estado inicial enviado: {len(current_points)} puntos")
        else:
            await ws.send(json.dumps({"type": "initial_state", "data": []}))

    elif message_type == "clear_scan":
        print(f"Solicitud de limpieza de escaneo de: {ws.remote_address}")
        success = await clear_points_from_redis()

        if success:
            # Notificar a todos los clientes web que se limpiaron los datos
            await broadcast_to_web_clients([], "scan_cleared")
            await ws.send(json.dumps({"type": "clear_response", "success": True}))
        else:
            await ws.send(json.dumps({"type": "clear_response", "success": False}))


async def server(ws):
    validation_run.increment("clients_connected")
    validation_run.increment("active_clients")
    validation_run.record_event("client_connected", remote=str(ws.remote_address))
    print("Cliente conectado:", ws.remote_address)
    try:
        async for message in ws:
            try:
                if isinstance(message, bytes):
                    validation_run.increment("messages_binary")
                    print(
                        f"Cliente identificado como Pico (binario): {ws.remote_address}"
                    )
                    sensor_points = parse_binary_sensor_data(message)
                elif isinstance(message, str):
                    validation_run.increment("messages_text")
                    data = None
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        data = None

                    if data and isinstance(data, dict):
                        await handle_web_client_message(ws, data)
                        continue

                    if ";" not in message:
                        validation_run.increment("unknown_messages")
                        validation_run.record_event(
                            "unknown_text_message",
                            remote=str(ws.remote_address),
                            payload=message,
                        )
                        print(f"Mensaje desconocido de {ws.remote_address}: {message}")
                        await ws.send("ERROR:UNKNOWN_FORMAT")
                        continue

                    print(
                        f"Cliente identificado como Pico (texto): {ws.remote_address}"
                    )
                    sensor_points = parse_sensor_data(message)
                else:
                    validation_run.increment("unknown_messages")
                    print(
                        f"Tipo de mensaje desconocido de {ws.remote_address}: {type(message)}"
                    )
                    await ws.send("ERROR:UNKNOWN_FORMAT")
                    continue

                validation_run.increment("points_parsed", len(sensor_points))
                processed_points = process_sensor_points(sensor_points)
                validation_run.increment("points_processed", len(processed_points))

                if processed_points:
                    await store_points_in_redis(processed_points)
                    await broadcast_to_web_clients(processed_points, "new_points")
                else:
                    validation_run.increment("parse_failures")
                    validation_run.record_event(
                        "parse_failed",
                        remote=str(ws.remote_address),
                        message_kind="bytes" if isinstance(message, bytes) else "text",
                    )
                    print("No se pudieron parsear datos válidos del sensor")
                    await ws.send("ERROR:PARSE_FAILED")

            except Exception as e:
                validation_run.record_event(
                    "message_processing_error",
                    remote=str(ws.remote_address),
                    error=str(e),
                )
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
        validation_run.increment("clients_disconnected")
        validation_run.set_value(
            "active_clients",
            max(int(validation_run.metrics.get("active_clients", 1)) - 1, 0),
        )
        validation_run.set_value("active_web_clients", len(web_clients))
        validation_run.record_event(
            "client_disconnected", remote=str(ws.remote_address)
        )
        print(f"Cliente desconectado: {ws.remote_address}")


async def main():
    # Inicializar Redis
    await init_redis()

    snapshot_task = asyncio.create_task(validation_run.snapshot_loop())
    validation_run.record_event("server_start", bind="0.0.0.0:3000")
    validation_run.snapshot("start")

    try:
        async with websockets.serve(server, "0.0.0.0", 3000):
            print("Servidor iniciado en ws://0.0.0.0:3000")
            print("Conexión a Redis establecida")
            print("Esperando conexiones...")
            print("- Clientes web deben enviar: {'type': 'register', 'client': 'web'}")
            print("- Clientes web pueden limpiar con: {'type': 'clear_scan'}")
            print(
                "- Dispositivos Pico aceptan texto legado y batches binarios compactos"
            )
            await asyncio.Future()
    finally:
        snapshot_task.cancel()
        try:
            await snapshot_task
        except asyncio.CancelledError:
            pass

        validation_run.record_event("server_stop")
        await validation_run.close()


if __name__ == "__main__":
    asyncio.run(main())
