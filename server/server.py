import asyncio
import websockets

connected = set()
counter = 0

async def handler(websocket):
    global counter
    connected.add(websocket)
    print(websocket,"\n\n")
    clientId = counter
    counter += 1
    try:
        async for message in websocket:
            print(f"Client {clientId}:\t {message}")
            response = f"Echo: {message}"
            await websocket.send(response)
            print(f"Server to Client {clientId}:\t {response}\n")
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