import asyncio
import websockets

async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello, server!")
        print("snd:\tHello, server!")
        async for message in websocket:
            print("rcv:\t",message)

if __name__ == "__main__":
    asyncio.run(main())