import pygame
import sys
import asyncio
import websockets
from time import sleep

event_queue = []

async def run_game(send_queue: asyncio.Queue):

    pygame.init()

    WIDTH, HEIGHT = 600, 400
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Number Game")

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (50, 100, 220)
    GRAY = (120, 120, 120)

    font = pygame.font.SysFont(None, 120)
    label_font = pygame.font.SysFont(None, 36)

    left_number = 0
    right_number = 0

    clock = pygame.time.Clock()

    SERVER_LISTEN_TIMER = pygame.USEREVENT + 1
    pygame.time.set_timer(SERVER_LISTEN_TIMER, 200)

    running = True
    while running:
        old_left_number = left_number
        if len(event_queue) > 0:
            right_number = int(event_queue.pop(0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    left_number += 1
                elif event.key == pygame.K_DOWN:
                    left_number = max(0, left_number - 1)
            elif event.type == SERVER_LISTEN_TIMER:
                await asyncio.sleep(0)

        if old_left_number != left_number:
            await send_queue.put(left_number)

        screen.fill(WHITE)

        # Labels
        left_label = label_font.render("Left (you control)", True, GRAY)
        right_label = label_font.render("Right", True, GRAY)
        screen.blit(left_label, (WIDTH // 4 - left_label.get_width() // 2, 60))
        screen.blit(right_label, (3 * WIDTH // 4 - right_label.get_width() // 2, 60))

        # Numbers
        left_text = font.render(str(left_number), True, BLUE)
        right_text = font.render(str(right_number), True, BLACK)
        screen.blit(left_text, (WIDTH // 4 - left_text.get_width() // 2, HEIGHT // 2 - left_text.get_height() // 2))
        screen.blit(right_text, (3 * WIDTH // 4 - right_text.get_width() // 2, HEIGHT // 2 - right_text.get_height() // 2))

        # Divider line
        pygame.draw.line(screen, GRAY, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)

        # Instructions
        instructions = label_font.render("UP: +1   DOWN: -1 (min 0)", True, GRAY)
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

async def main_loop(send_queue: asyncio.Queue):
    await run_game(send_queue)

async def send_server(websocket, send_queue: asyncio.Queue):
    while True:
        value = await send_queue.get()
        await websocket.send(str(value))
        print(f"sent: {value}")

async def listen_server(websocket):
    async for message in websocket:
        print("server:\t", message)
        event_queue.append(message)

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