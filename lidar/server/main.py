import asyncio
import websockets
import json

# Conjunto para rastrear clientes web conectados
web_clients = set()

async def server(ws):
    print("Cliente conectado:", ws.remote_address)
    try:
        async for message in ws:
            # print plain message
            print(f"Mensaje recibido: {message}")
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