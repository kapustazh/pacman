# """Entry point for the Pac-Man project."""

# import sys

# from src.config.config import load_config
# from src.game.game_state import GameState


# def main() -> int:
#     """Start the Pac-Man game."""
#     if len(sys.argv) != 2:
#         print("Usage: python3 pac-man.py config.json")
#         return 1

#     config = load_config(sys.argv[1])
#     game = GameState(config)
#     game.start()

#     return 0

import os
import sys
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SRC_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_ROOT))
ICON_PATH = Path(__file__).resolve().parent / "assets" / "icon" / "image.png"

import pygame  # noqa: E402

from core.engine import GameEngine  # noqa: E402
from sprites.assets import Assets  # noqa: E402
from states.menu_state import MenuState  # noqa: E402
from states.text import ArcadeTextRenderer  # noqa: E402

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


def main() -> None:
    pygame.init()
    pygame.key.set_repeat(0)
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pac-Man")
    if ICON_PATH.exists():
        pygame.display.set_icon(pygame.image.load(ICON_PATH))

    assets = Assets()
    assets.load()
    text = ArcadeTextRenderer()
    text.preload()
    engine = GameEngine(screen, assets, text, MenuState())
    engine.run()

    pygame.quit()


if __name__ == "__main__":
    main()
