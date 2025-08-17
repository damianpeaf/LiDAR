import asyncio
import websockets
import json

# Conjunto para rastrear clientes web conectados
web_clients = set()

async def server(ws):
    print("Cliente conectado:", ws.remote_address)
    try:
        async for message in ws:
            try:
                # Intentar decodificar como JSON
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = None

                # Si el mensaje es de un cliente web que se registra
                if data and data.get('type') == 'register' and data.get('client') == 'web':
                    web_clients.add(ws)
                    print(f"Cliente web registrado: {ws.remote_address}")

                # Si el mensaje viene del Pico (tira de valores separados por ;)
                elif isinstance(message, str) and ";" in message:
                    print(f"Cliente identificado como Pico: {ws.remote_address}")

                    parts = message.strip().split(";")
                    points = []

                    # Agrupar de 3 en 3: (angulo, distancia, intensidad)
                    for i in range(0, len(parts) - 2, 3):
                        try:
                            a = float(parts[i])
                            d = float(parts[i + 1])
                            inten = float(parts[i + 2])
                            points.append({"a": a, "d": d, "i": inten})
                        except ValueError:
                            continue  # ignorar datos inválidos

                    # Convertir a JSON para reenviar
                    json_message = json.dumps({"points": points})
                    
                    # print(json_message)

                    if web_clients:
                        for web_client in list(web_clients):
                            try:
                                await web_client.send(json_message)
                                print(f"Datos enviados al cliente web {web_client.remote_address}")
                            except Exception as e:
                                print(f"Error enviando a cliente web {web_client.remote_address}: {e}")
                                web_clients.discard(web_client)

                else:
                    print(f"Mensaje desconocido de {ws.remote_address}: {message}")

            except Exception as e:
                print(f"Error en el servidor: {e}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Conexión cerrada: {e}")
    finally:
        web_clients.discard(ws)
        print(f"Cliente desconectado: {ws.remote_address}")

async def main():
    async with websockets.serve(server, "0.0.0.0", 3000):
        print("Servidor iniciado en ws://0.0.0.0:3000")
        await asyncio.Future()

asyncio.run(main())
