"""
Minimal example: pygame game loop + websocket networking running
on a background thread, bridged via a thread-safe queue.

Pattern:
  - Network thread runs its own asyncio event loop, connects to the
    websocket server, and receives messages as fast as they arrive.
  - Each received message is pushed onto a queue.Queue (thread-safe).
  - The pygame main loop drains the queue every frame (non-blocking)
    and keeps only the LATEST opponent state.
  - Opponent position is interpolated between the last two known
    states so movement looks smooth even if updates arrive at a
    lower rate (e.g. 20Hz) than the render loop (60Hz).
  - Outgoing state (your own player) is sent on its own throttled
    timer, independent of the render rate.

Requires: pip install pygame websockets
"""

import asyncio
import json
import queue
import threading
import time

import pygame
import websockets

SERVER_URI = "ws://localhost:8765"  # change to your server
SEND_HZ = 80  # how often WE send our state to the server
print(1.0/SEND_HZ)
WINDOW_SIZE = (800, 600)


class NetworkClient:
    """Runs a websocket connection on a background thread.

    - incoming_queue: messages from the server, drained by the main thread
    - outgoing_queue: messages we want to send, filled by the main thread
    """

    def __init__(self, uri):
        self.uri = uri
        self.incoming_queue = queue.Queue()
        self.outgoing_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def send(self, data: dict):
        """Call from the main (pygame) thread to queue an outgoing message."""
        self.outgoing_queue.put(data)

    def _run(self):
        # Each thread needs its own asyncio event loop.
        asyncio.run(self._main())

    async def _main(self):
        try:
            async with websockets.connect(self.uri) as ws:
                await asyncio.gather(
                    self._receiver(ws),
                    self._sender(ws),
                )
        except Exception as e:
            print(f"[network] connection error: {e}")

    async def _receiver(self, ws):
        """Reads every message as fast as it arrives, no throttling."""
        async for message in ws:
            try:
                data = json.loads(message)
                self.incoming_queue.put(data)
            except json.JSONDecodeError:
                pass
            if self._stop_event.is_set():
                break

    async def _sender(self, ws):
        """Sends whatever the main thread has queued, at a capped rate."""
        interval = 1.0 / SEND_HZ
        while not self._stop_event.is_set():
            try:
                data = self.outgoing_queue.get_nowait()
                await ws.send(json.dumps(data))
            except queue.Empty:
                pass
            await asyncio.sleep(interval)
            #await asyncio.sleep(0)


class OpponentState:
    """Holds the last two known opponent positions for interpolation."""

    def __init__(self):
        self.prev_pos = (400, 300)
        self.target_pos = (400, 300)
        self.prev_time = time.time()
        self.target_time = time.time()

    def update(self, x, y):
        self.prev_pos = self.target_pos
        self.prev_time = self.target_time
        self.target_pos = (x, y)
        self.target_time = time.time()

    def get_interpolated_pos(self):
        now = time.time()
        span = self.target_time - self.prev_time
        if span <= 0:
            return self.target_pos
        t = (now - self.target_time) / span + 1.0  # extrapolate slightly forward
        t = max(0.0, min(t, 1.5))  # clamp so it doesn't run away
        x = self.prev_pos[0] + (self.target_pos[0] - self.prev_pos[0]) * t
        y = self.prev_pos[1] + (self.target_pos[1] - self.prev_pos[1]) * t
        return (x, y)


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    net = NetworkClient(SERVER_URI)
    net.start()

    player_pos = [200, 300]
    opponent = OpponentState()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Local input ---
        keys = pygame.key.get_pressed()
        speed = 4
        if keys[pygame.K_LEFT]:
            player_pos[0] -= speed
        if keys[pygame.K_RIGHT]:
            player_pos[0] += speed
        if keys[pygame.K_UP]:
            player_pos[1] -= speed
        if keys[pygame.K_DOWN]:
            player_pos[1] += speed

        player_pos[0] = max(15, min(player_pos[0], 785))
        player_pos[1] = max(15, min(player_pos[1], 585))

        # Queue our state to send (actual send is throttled inside NetworkClient)
        net.send({"x": player_pos[0], "y": player_pos[1]})

        # --- Drain incoming network messages every frame, keep only latest ---
        latest = None
        while True:
            try:
                latest = net.incoming_queue.get_nowait()
            except queue.Empty:
                break
        if latest is not None:
            opponent.update(latest["x"], latest["y"])

        # --- Render ---
        screen.fill((20, 20, 30))
        pygame.draw.circle(screen, (80, 200, 255), player_pos, 15)  # you
        opp_x, opp_y = opponent.get_interpolated_pos()
        pygame.draw.circle(screen, (255, 100, 100), (int(opp_x), int(opp_y)), 15)  # opponent
        pygame.display.flip()

        clock.tick(60)  # render/read loop runs at 60 FPS regardless of send rate

    net.stop()
    pygame.quit()


if __name__ == "__main__":
    main()