import pygame
import random
import sys
import asyncio

# --- Setup ---
pygame.init()

WIDTH, HEIGHT = 640, 480
SQUARE_SIZE = 30
SPEED = 5

RED = (220, 40, 40)
GREEN = (40, 200, 80)
BG_COLOR = (25, 25, 30)

def random_green_position(player_rect):
    """Pick a random position for the green square that doesn't overlap the player."""
    while True:
        x = random.randint(0, WIDTH - SQUARE_SIZE)
        y = random.randint(0, HEIGHT - SQUARE_SIZE)
        green_rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
        if not green_rect.colliderect(player_rect):
            return green_rect

# Player (red square) starts in the middle
player = pygame.Rect(WIDTH // 2 - SQUARE_SIZE // 2, HEIGHT // 2 - SQUARE_SIZE // 2,
                      SQUARE_SIZE, SQUARE_SIZE)

async def run_game(send_queue: asyncio.Queue):
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Red vs Green Square")
    clock = pygame.time.Clock()

    # Green square starts somewhere random, not overlapping the player
    green = random_green_position(player)

    score = 0

    SERVER_LISTEN_TIMER = pygame.USEREVENT + 1
    pygame.time.set_timer(SERVER_LISTEN_TIMER, 500)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(f"Final score: {score}")
                running = False
            elif event.type == SERVER_LISTEN_TIMER:
                await send_queue.put(f"Score: {score}")
                await asyncio.sleep(0)

        # --- Input ---
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a]:
            dx = -SPEED
        if keys[pygame.K_d]:
            dx = SPEED
        if keys[pygame.K_w]:
            dy = -SPEED
        if keys[pygame.K_s]:
            dy = SPEED

        player.x += dx
        player.y += dy

        # Keep player on screen
        player.clamp_ip(screen.get_rect())

        # --- Collision check ---
        if player.colliderect(green):
            score += 1
            print(f"Touched! Score: {score}")
            green = random_green_position(player)

        # --- Draw ---
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GREEN, green)
        pygame.draw.rect(screen, RED, player)
        pygame.display.flip()

        clock.tick(45)

    pygame.quit()
    sys.exit()