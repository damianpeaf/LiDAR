import os
import math
import asyncio
import csv
import struct
import websockets
import redis.asyncio as redis
import json
import uuid
import time
from pathlib import Path
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_KEY = "lidar_points"
SERVICE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path.cwd())).resolve()
NETWORK_TELEMETRY_CSV = Path(
    os.getenv(
        "NETWORK_TELEMETRY_CSV",
        SERVICE_ROOT / "network_telemetry.csv",
    )
)

BINARY_BATCH_MAGIC = b"PS"
BINARY_BATCH_VERSION = 1
BINARY_BATCH_HEADER_SIZE = 8
BINARY_POINT_RECORD_SIZE = 5

web_clients = set()
redis_client = None

network_stats = {
    "started_at": None,
    "last_message_at": None,
    "text_units": 0,
    "binary_units": 0,
    "text_bytes": 0,
    "binary_bytes": 0,
    "sensor_units": 0,
    "sensor_bytes": 0,
    "estimated_ws_frame_bytes": 0,
    "points_parsed": 0,
    "points_processed": 0,
    "parse_failures": 0,
    "redis_failures": 0,
    "broadcast_failures": 0,
    "web_units": 0,
    "web_bytes": 0,
}
network_telemetry_header_written = False

# Variables para calcular puntos por segundo
total_points_processed = 0
start_time = None


def _now_iso():
    return datetime.now().isoformat()


def _network_duration_s(now=None):
    if network_stats["started_at"] is None:
        return 0.0
    return (now or time.time()) - network_stats["started_at"]


def _ensure_network_telemetry_header():
    global network_telemetry_header_written

    if network_telemetry_header_written:
        return

    NETWORK_TELEMETRY_CSV.parent.mkdir(parents=True, exist_ok=True)
    network_telemetry_header_written = NETWORK_TELEMETRY_CSV.exists() and NETWORK_TELEMETRY_CSV.stat().st_size > 0
    if network_telemetry_header_written:
        return

    with NETWORK_TELEMETRY_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "timestamp",
                "duration_s",
                "last_unit_type",
                "sensor_units",
                "sensor_bytes",
                "estimated_ws_frame_bytes",
                "throughput_bytes_s",
                "estimated_ws_throughput_bytes_s",
                "mean_bytes_unit",
                "text_units",
                "text_bytes",
                "binary_units",
                "binary_bytes",
                "points_parsed",
                "points_processed",
                "parse_failures",
                "redis_failures",
                "broadcast_failures",
                "web_units",
                "web_bytes",
            ]
        )
    network_telemetry_header_written = True


def record_inbound_unit(unit_type, byte_count):
    now = time.time()
    if unit_type in {"binary", "text"} and network_stats["started_at"] is None:
        network_stats["started_at"] = now

    network_stats["last_message_at"] = now

    estimated_ws_frame_bytes = estimate_client_ws_frame_bytes(byte_count)

    if unit_type == "binary":
        network_stats["binary_units"] += 1
        network_stats["binary_bytes"] += byte_count
        network_stats["sensor_units"] += 1
        network_stats["sensor_bytes"] += byte_count
        network_stats["estimated_ws_frame_bytes"] += estimated_ws_frame_bytes
    elif unit_type == "text":
        network_stats["text_units"] += 1
        network_stats["text_bytes"] += byte_count
        network_stats["sensor_units"] += 1
        network_stats["sensor_bytes"] += byte_count
        network_stats["estimated_ws_frame_bytes"] += estimated_ws_frame_bytes
    else:
        network_stats["web_units"] += 1
        network_stats["web_bytes"] += byte_count


def estimate_client_ws_frame_bytes(payload_bytes):
    if payload_bytes <= 125:
        header_bytes = 2
    elif payload_bytes <= 65535:
        header_bytes = 4
    else:
        header_bytes = 10

    return payload_bytes + header_bytes + 4


def write_network_telemetry(unit_type):
    _ensure_network_telemetry_header()

    duration_s = _network_duration_s()
    throughput_bytes_s = network_stats["sensor_bytes"] / duration_s if duration_s > 0 else 0
    estimated_ws_throughput_bytes_s = (
        network_stats["estimated_ws_frame_bytes"] / duration_s if duration_s > 0 else 0
    )
    mean_bytes_unit = (
        network_stats["sensor_bytes"] / network_stats["sensor_units"]
        if network_stats["sensor_units"] > 0
        else 0
    )

    with NETWORK_TELEMETRY_CSV.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                _now_iso(),
                f"{duration_s:.3f}",
                unit_type,
                network_stats["sensor_units"],
                network_stats["sensor_bytes"],
                network_stats["estimated_ws_frame_bytes"],
                f"{throughput_bytes_s:.3f}",
                f"{estimated_ws_throughput_bytes_s:.3f}",
                f"{mean_bytes_unit:.3f}",
                network_stats["text_units"],
                network_stats["text_bytes"],
                network_stats["binary_units"],
                network_stats["binary_bytes"],
                network_stats["points_parsed"],
                network_stats["points_processed"],
                network_stats["parse_failures"],
                network_stats["redis_failures"],
                network_stats["broadcast_failures"],
                network_stats["web_units"],
                network_stats["web_bytes"],
            ]
        )

    print(
        "NET|event=stats"
        f"|duration_s={duration_s:.3f}"
        f"|last_unit_type={unit_type}"
        f"|sensor_units={network_stats['sensor_units']}"
        f"|sensor_bytes={network_stats['sensor_bytes']}"
        f"|estimated_ws_frame_bytes={network_stats['estimated_ws_frame_bytes']}"
        f"|throughput_bytes_s={throughput_bytes_s:.3f}"
        f"|estimated_ws_throughput_bytes_s={estimated_ws_throughput_bytes_s:.3f}"
        f"|mean_bytes_unit={mean_bytes_unit:.3f}"
        f"|parse_failures={network_stats['parse_failures']}"
        f"|redis_failures={network_stats['redis_failures']}"
        f"|broadcast_failures={network_stats['broadcast_failures']}"
    )


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


def parse_json_sensor_data(data):
    try:
        points = data.get("points", [])
        inclination = float(data.get("inclination", data.get("servo_deg", 0.0)))
        parsed_points = []

        for point in points:
            parsed_points.append(
                {
                    "inclination": float(point.get("inclination", inclination)),
                    "distance": float(point.get("distance", point.get("d"))),
                    "intensity": float(point.get("intensity", point.get("i"))),
                    "pan_angle": float(point.get("pan_angle", point.get("a"))),
                }
            )

        return parsed_points

    except Exception as e:
        print(f"Error parseando payload JSON del sensor: {e}")
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

        print(f"Almacenados {len(points)} puntos en Redis")
    except Exception as e:
        network_stats["redis_failures"] += 1
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
                network_stats["broadcast_failures"] += 1
                disconnected.append(client)
            except Exception as e:
                network_stats["broadcast_failures"] += 1
                print(f"Error enviando a cliente web: {e}")
                disconnected.append(client)

        for client in disconnected:
            web_clients.discard(client)


def process_sensor_points(sensor_points):
    global total_points_processed, start_time

    if not sensor_points:
        return []

    if start_time is None:
        start_time = time.time()

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

    total_points_processed += len(processed_points)
    elapsed_time = time.time() - start_time
    points_per_second = total_points_processed / elapsed_time if elapsed_time > 0 else 0

    print(f"Puntos procesados: {len(processed_points)}")
    print(f"Media puntos/s: {points_per_second:.2f}")

    return processed_points


async def handle_web_client_message(ws, data):
    """Maneja mensajes específicos del cliente web"""
    message_type = data.get("type")

    if message_type == "register" and data.get("client") == "web":
        web_clients.add(ws)
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
    print("Cliente conectado:", ws.remote_address)
    try:
        async for message in ws:
            try:
                if isinstance(message, bytes):
                    unit_type = "binary"
                    record_inbound_unit(unit_type, len(message))
                    print(
                        f"Cliente identificado como Pico (binario): {ws.remote_address}"
                    )
                    sensor_points = parse_binary_sensor_data(message)
                elif isinstance(message, str):
                    message_bytes = len(message.encode("utf-8"))
                    data = None
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        data = None

                    if data and isinstance(data, dict) and isinstance(data.get("points"), list):
                        unit_type = "text"
                        record_inbound_unit(unit_type, message_bytes)
                        print(
                            f"Cliente identificado como Pico (JSON): {ws.remote_address}"
                        )
                        sensor_points = parse_json_sensor_data(data)
                    elif data and isinstance(data, dict):
                        record_inbound_unit("web", message_bytes)
                        await handle_web_client_message(ws, data)
                        continue
                    elif ";" not in message:
                        print(f"Mensaje desconocido de {ws.remote_address}: {message}")
                        await ws.send("ERROR:UNKNOWN_FORMAT")
                        continue
                    else:
                        unit_type = "text"
                        record_inbound_unit(unit_type, message_bytes)
                        print(
                            f"Cliente identificado como Pico (texto): {ws.remote_address}"
                        )
                        sensor_points = parse_sensor_data(message)
                else:
                    print(
                        f"Tipo de mensaje desconocido de {ws.remote_address}: {type(message)}"
                    )
                    await ws.send("ERROR:UNKNOWN_FORMAT")
                    continue

                processed_points = process_sensor_points(sensor_points)
                network_stats["points_parsed"] += len(sensor_points)
                network_stats["points_processed"] += len(processed_points)

                if processed_points:
                    await store_points_in_redis(processed_points)
                    await broadcast_to_web_clients(processed_points, "new_points")
                else:
                    network_stats["parse_failures"] += 1
                    print("No se pudieron parsear datos válidos del sensor")
                    await ws.send("ERROR:PARSE_FAILED")

                write_network_telemetry(unit_type)

            except Exception as e:
                network_stats["parse_failures"] += 1
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
        print("- Dispositivos Pico aceptan texto legado y batches binarios compactos")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
