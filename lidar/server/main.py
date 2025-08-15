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
                data = json.loads(message)
                
                # Registrar como cliente web si el mensaje es de tipo 'register' y client 'web'
                if data.get('type') == 'register' and data.get('client') == 'web':
                    web_clients.add(ws)
                    print(f"Cliente web registrado: {ws.remote_address}")
                # Si el mensaje contiene 'points', es la Pico, reenviar a clientes web
                elif 'points' in data:
                    print(f"Cliente identificado como Pico: {ws.remote_address}")
                    if web_clients:
                        for web_client in web_clients:
                            try:
                                await web_client.send(message)
                                print(f"Datos enviados al cliente web {web_client.remote_address}")
                            except Exception as e:
                                print(f"Error enviando a cliente web {web_client.remote_address}: {e}")
                                web_clients.discard(web_client)
                else:
                    print(f"Mensaje desconocido de {ws.remote_address}: {data}")
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON: {e}")
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