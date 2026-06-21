import os
import sys
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SRC_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_ROOT))
ICON_PATH = Path(__file__).resolve().parent / "assets" / "icon" / "image.png"

import pygame  # noqa: E402

from core.engine import GameEngine  # noqa: E402
from core.resources import AssetsResourceManager  # noqa: E402
from sprites.assets import Assets  # noqa: E402
from states.menu_state import MenuState  # noqa: E402
from states.text import preload_arcade_font  # noqa: E402

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


def main() -> None:
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pac-Man")
    if ICON_PATH.exists():
        pygame.display.set_icon(pygame.image.load(ICON_PATH))

    resources = AssetsResourceManager(Assets())
    resources.load_all()
    preload_arcade_font()
    engine = GameEngine(screen, resources, MenuState())
    engine.run()

    pygame.quit()


if __name__ == "__main__":
    main()
