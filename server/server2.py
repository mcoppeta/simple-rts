import asyncio
import websockets

connected = set()
counter = 0

async def send_opponent(current_player, message, metadata=None):
    for connection in list(connected):
        if connection != current_player:
            await connection.send(message)
            print(metadata)

async def handler(websocket):
    global counter
    connected.add(websocket)
    print(f"Client {counter} connected as player {counter % 2}","\n\n")
    clientId = counter
    counter += 1
    try:
        async for message in websocket:
            print(f"Client {clientId} | player {clientId % 2}:\t {message}")
            await send_opponent(websocket, message, f"Server to player {(clientId + 1) % 2}: {message}")
    finally:
        connected.remove(websocket)
        print(f"Client {clientId} disconnected")
        print("connected:")
        print(connected)
        print()

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())