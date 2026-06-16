import os
import sys
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SRC_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_ROOT))

import pygame  # noqa: E402

from rendering.render import DemoRenderer  # noqa: E402
from sprites.assets import Assets  # noqa: E402

BG_COLOR = (0, 0, 0)
SPRITE_STRIDE = 20
SCREEN_WIDTH = SPRITE_STRIDE * 10 + 16
SCREEN_HEIGHT = 120


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pac-Man Asset Demo")

    assets = Assets()
    assets.load()
    renderer = DemoRenderer(assets)
    clock = pygame.time.Clock()

    running = True
    while running:
        now_ms = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG_COLOR)
        renderer.render(screen, now_ms)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
