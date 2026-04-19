import os
import math
import asyncio
import struct
import websockets
import redis.asyncio as redis
import json
import uuid
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import boto3
import httpx

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_KEY = "lidar_points"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
DEVICE_PASSWORD = os.getenv("DEVICE_PASSWORD", "")

R2_BUCKET = os.getenv("R2_BUCKET", "")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "")

BINARY_BATCH_MAGIC = b"PS"
BINARY_BATCH_VERSION = 1
BINARY_BATCH_HEADER_SIZE = 8
BINARY_POINT_RECORD_SIZE = 5

web_clients = set()
authenticated_web_clients = {}
redis_client = None

# Variables para calcular puntos por segundo
total_points_processed = 0
start_time = None
scan_started_at = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    print("Conexión a Redis establecida")


def get_ws_path(ws):
    if hasattr(ws, "request") and ws.request and hasattr(ws.request, "path"):
        return ws.request.path
    return getattr(ws, "path", "")


def extract_ws_token(ws):
    raw_path = get_ws_path(ws)
    if not raw_path:
        return None

    query = urlparse(raw_path).query
    if not query:
        return None

    token = parse_qs(query).get("token", [None])[0]
    return token


async def verify_supabase_jwt(token):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY or not token:
        return None

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
    }

    url = f"{SUPABASE_URL}/auth/v1/user"
    timeout = httpx.Timeout(5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception as e:
        print(f"Error validando JWT con Supabase: {e}")
        return None


async def get_profile_status(user_id):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    params = {
        "select": "status",
        "id": f"eq.{user_id}",
        "limit": 1,
    }

    url = f"{SUPABASE_URL}/rest/v1/profiles"
    timeout = httpx.Timeout(5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return None
        payload = response.json()
        if not payload:
            return None
        return payload[0].get("status")
    except Exception as e:
        print(f"Error consultando perfil en Supabase: {e}")
        return None


def get_scan_stats():
    duration_seconds = 0.0
    points_per_second = 0.0

    if scan_started_at is not None:
        duration_seconds = max(0.0, time.time() - scan_started_at)

    if duration_seconds > 0:
        points_per_second = total_points_processed / duration_seconds

    return {
        "point_count": total_points_processed,
        "points_per_second": points_per_second,
        "duration_seconds": duration_seconds,
    }


def build_r2_url(key):
    base = R2_PUBLIC_BASE_URL.rstrip("/")
    if base:
        return f"{base}/{key}"
    return f"r2://{R2_BUCKET}/{key}"


def upload_json_to_r2_blocking(bucket, key, payload):
    client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=payload,
        ContentType="application/json",
    )


async def insert_scan_metadata(user_id, r2_url, stats):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase service role no configurado")

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload = {
        "user_id": user_id,
        "r2_url": r2_url,
        "point_count": stats["point_count"],
        "points_per_second": stats["points_per_second"],
        "duration_seconds": stats["duration_seconds"],
    }

    url = f"{SUPABASE_URL}/rest/v1/scans"
    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Insert scans falló ({response.status_code}): {response.text}"
        )

    rows = response.json()
    if not rows:
        return None
    return rows[0].get("id")


async def save_scan_to_r2(points, user_id):
    if not points:
        raise RuntimeError("No hay puntos para guardar")

    required = [R2_BUCKET, R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]
    if not all(required):
        raise RuntimeError("Credenciales R2 incompletas")

    key = f"scans/{user_id}/{uuid.uuid4()}.json"
    payload = json.dumps(points).encode("utf-8")

    await asyncio.to_thread(upload_json_to_r2_blocking, R2_BUCKET, key, payload)

    r2_url = build_r2_url(key)
    stats = get_scan_stats()
    scan_id = await insert_scan_metadata(user_id, r2_url, stats)

    return {
        "scan_id": scan_id,
        "url": r2_url,
    }


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
    global total_points_processed, start_time, scan_started_at

    try:
        await redis_client.delete(REDIS_KEY)
        total_points_processed = 0
        start_time = None
        scan_started_at = None
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


def process_sensor_points(sensor_points):
    global total_points_processed, start_time, scan_started_at

    if not sensor_points:
        return []

    if start_time is None:
        start_time = time.time()
    if scan_started_at is None:
        scan_started_at = time.time()

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

    if message_type == "clear_scan":
        client_auth = authenticated_web_clients.get(ws)
        if not client_auth:
            await ws.send(json.dumps({"type": "error", "code": 401}))
            return

        print(f"Solicitud de limpieza de escaneo de: {ws.remote_address}")
        success = await clear_points_from_redis()

        if success:
            # Notificar a todos los clientes web que se limpiaron los datos
            await broadcast_to_web_clients([], "scan_cleared")
            await ws.send(json.dumps({"type": "clear_response", "success": True}))
        else:
            await ws.send(json.dumps({"type": "clear_response", "success": False}))

    elif message_type == "save_scan":
        client_auth = authenticated_web_clients.get(ws)
        if not client_auth:
            await ws.send(json.dumps({"type": "error", "code": 401}))
            return

        try:
            points = await get_all_points_from_redis()
            result = await save_scan_to_r2(points, client_auth["user_id"])
            await ws.send(
                json.dumps(
                    {
                        "type": "save_response",
                        "success": True,
                        "scan_id": result["scan_id"],
                        "url": result["url"],
                    }
                )
            )
        except Exception as e:
            print(f"Error guardando escaneo en R2: {e}")
            await ws.send(
                json.dumps(
                    {
                        "type": "save_response",
                        "success": False,
                    }
                )
            )


async def server(ws):
    addr = ws.remote_address
    print(f"[WS] nueva conexión de {addr}")
    print(f"[WS] DEVICE_PASSWORD configurado: {'SI (' + str(len(DEVICE_PASSWORD)) + ' chars)' if DEVICE_PASSWORD else 'NO (vacío!)'}")
    client_type = None

    try:
        async for message in ws:
            try:
                if client_type is None:
                    if isinstance(message, bytes):
                        print(f"[WS] {addr} envió binario sin autenticarse ({len(message)} bytes) — rechazando")
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "error",
                                    "code": 401,
                                    "reason": "device_auth_required",
                                }
                            )
                        )
                        await ws.close(code=1008, reason="device_auth_required")
                        break

                    if not isinstance(message, str):
                        print(f"[WS] {addr} tipo de mensaje inesperado: {type(message)}")
                        await ws.close(code=1003, reason="unsupported_message_type")
                        break

                    print(f"[WS] {addr} mensaje texto (sin auth): {message[:200]!r}")

                    data = None
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        print(f"[WS] {addr} no es JSON válido — rechazando")
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "error",
                                    "code": 401,
                                    "reason": "auth_message_required",
                                }
                            )
                        )
                        await ws.close(code=1008, reason="auth_message_required")
                        break

                    if data.get("type") == "auth":
                        password = data.get("password", "")
                        print(f"[AUTH] intento de auth desde {addr}")
                        print(f"[AUTH] password recibida: {password!r} ({len(password)} chars)")
                        print(f"[AUTH] password esperada: {DEVICE_PASSWORD!r} ({len(DEVICE_PASSWORD)} chars)")
                        if not DEVICE_PASSWORD or password != DEVICE_PASSWORD:
                            print(f"[AUTH] RECHAZADO desde {addr}")
                            await ws.send(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "code": 401,
                                        "reason": "invalid_device_password",
                                    }
                                )
                            )
                            await ws.close(code=1008, reason="invalid_device_password")
                            break

                        client_type = "device"
                        await ws.send(
                            json.dumps({"type": "auth_response", "success": True})
                        )
                        print(f"[AUTH] dispositivo AUTENTICADO: {addr}")
                        continue

                    if data.get("type") == "register" and data.get("client") == "web":
                        token = data.get("token") or extract_ws_token(ws)
                        user = await verify_supabase_jwt(token)
                        if not user:
                            await ws.send(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "code": 401,
                                        "reason": "invalid_or_missing_token",
                                    }
                                )
                            )
                            await ws.close(code=1008, reason="invalid_or_missing_token")
                            break

                        profile_status = await get_profile_status(user.get("id"))
                        if profile_status != "approved":
                            await ws.send(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "code": 403,
                                        "reason": "user_not_approved",
                                    }
                                )
                            )
                            await ws.close(code=1008, reason="user_not_approved")
                            break

                        client_type = "web"
                        web_clients.add(ws)
                        authenticated_web_clients[ws] = {
                            "user_id": user.get("id"),
                        }
                        print(
                            f"Cliente web autenticado: {ws.remote_address} ({user.get('id')})"
                        )

                        current_points = await get_all_points_from_redis()
                        await ws.send(
                            json.dumps(
                                {"type": "initial_state", "data": current_points}
                            )
                        )
                        continue

                    await ws.send(
                        json.dumps(
                            {
                                "type": "error",
                                "code": 401,
                                "reason": "unknown_client_type",
                            }
                        )
                    )
                    await ws.close(code=1008, reason="unknown_client_type")
                    break

                if client_type == "device" and isinstance(message, bytes):
                    print(f"[DATA] binario de {addr} ({len(message)} bytes)")
                    sensor_points = parse_binary_sensor_data(message)

                elif client_type == "device" and isinstance(message, str):
                    data = None
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        data = None

                    if data and isinstance(data, dict):
                        await handle_web_client_message(ws, data)
                        continue

                    if ";" not in message:
                        print(f"Mensaje desconocido de {ws.remote_address}: {message}")
                        await ws.send("ERROR:UNKNOWN_FORMAT")
                        continue

                    print(
                        f"Cliente identificado como Pico (texto): {ws.remote_address}"
                    )
                    sensor_points = parse_sensor_data(message)

                elif client_type == "web" and isinstance(message, str):
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        await ws.send("ERROR:UNKNOWN_FORMAT")
                        continue

                    if data and isinstance(data, dict):
                        await handle_web_client_message(ws, data)
                    continue

                else:
                    print(
                        f"Tipo de mensaje desconocido de {ws.remote_address}: {type(message)}"
                    )
                    await ws.send("ERROR:UNKNOWN_FORMAT")
                    continue

                processed_points = process_sensor_points(sensor_points)

                if processed_points:
                    await store_points_in_redis(processed_points)
                    await broadcast_to_web_clients(processed_points, "new_points")
                else:
                    print("No se pudieron parsear datos válidos del sensor")
                    await ws.send("ERROR:PARSE_FAILED")

            except Exception as e:
                print(f"Error procesando mensaje: {e}")
                try:
                    await ws.send(f"ERROR:{str(e)}")
                except:
                    pass

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[WS] conexión cerrada ({addr}): {e}")
    except Exception as e:
        print(f"[WS] error en handler ({addr}): {e}")
    finally:
        web_clients.discard(ws)
        authenticated_web_clients.pop(ws, None)
        print(f"[WS] desconectado: {addr} (era: {client_type or 'sin identificar'})")


async def main():
    await init_redis()

    port = int(os.getenv("PORT", "3000"))

    print("=" * 60)
    print(f"[SERVER] LiDAR WebSocket Server arrancando en puerto {port}")
    print(f"[SERVER] DEVICE_PASSWORD: {'configurada (' + str(len(DEVICE_PASSWORD)) + ' chars)' if DEVICE_PASSWORD else '!!! NO CONFIGURADA — auth fallará !!!'}")
    print(f"[SERVER] SUPABASE_URL: {'configurada' if SUPABASE_URL else 'no configurada'}")
    print(f"[SERVER] R2_BUCKET: {R2_BUCKET or '(no configurado)'}")
    print("=" * 60)

    async with websockets.serve(server, "0.0.0.0", port):
        print(f"[SERVER] escuchando en ws://0.0.0.0:{port}")
        print("[SERVER] Protocolo: primer mensaje debe ser auth (device) o register (web)")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
