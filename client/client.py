import asyncio
import websockets
from time import sleep
from game import run_game

async def main_loop(send_queue: asyncio.Queue):
    await run_game(send_queue)

async def send_server(websocket, send_queue: asyncio.Queue):
    while True:
        value = await send_queue.get()
        await websocket.send(value)
        print(f"sent: {value}")

async def listen_server(websocket):
    async for message in websocket:
        print("server:\t", message)

async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        send_queue = asyncio.Queue()
        await asyncio.gather(
            main_loop(send_queue),
            send_server(websocket, send_queue),
            listen_server(websocket)
        )

if __name__ == "__main__":
    asyncio.run(main())