"""
Minimal broadcast server to match pygame_websocket_client.py.

Behavior:
  - Each connecting client is assigned an id.
  - When a client sends {"x": ..., "y": ...}, the server tags it with
    the sender's id and broadcasts it to every OTHER connected client.
  - No game logic, no validation, no persistence — just relays state.
    That's enough for the client's interpolation code to work, since
    it only cares about receiving {"x", "y"} messages for the opponent.

This uses one shared set of connected clients, so it works for any
number of players, not just 2 (each client will just see updates from
all others, not just one).

Requires: pip install websockets
Run: python game_server.py
"""

import asyncio
import json
import itertools

import websockets

HOST = "localhost"
PORT = 8765

# Connected clients: websocket -> client_id
clients = {}
id_counter = itertools.count(1)


async def handler(ws):
    client_id = next(id_counter)
    clients[ws] = client_id
    print(f"[server] client {client_id} connected ({len(clients)} total)")

    try:
        async for message in ws:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            # Tag the message with who sent it, then relay to everyone else.
            data["id"] = client_id
            outgoing = json.dumps(data)
            print(outgoing)

            await broadcast(outgoing, exclude=ws)

    except websockets.ConnectionClosed:
        pass
    finally:
        del clients[ws]
        print(f"[server] client {client_id} disconnected ({len(clients)} total)")


async def broadcast(message: str, exclude=None):
    if not clients:
        return
    recipients = [c for c in clients if c is not exclude]
    if not recipients:
        return
    # send concurrently, ignore any that fail (e.g. mid-disconnect)
    await asyncio.gather(
        *(safe_send(ws, message) for ws in recipients),
        return_exceptions=True,
    )


async def safe_send(ws, message):
    try:
        await ws.send(message)
    except websockets.ConnectionClosed:
        pass


async def main():
    async with websockets.serve(handler, HOST, PORT):
        print(f"[server] listening on ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())