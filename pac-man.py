import os
import sys
from pathlib import Path
from typing import Any

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SRC_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_ROOT))

import pygame  # noqa: E402

from config.config import default_config, load_config  # noqa: E402
from core.engine import GameEngine  # noqa: E402
from core.paths import resource_root, user_data_dir  # noqa: E402
from managers.highscore_manager import HighscoreManager  # noqa: E402
from sprites.assets import Assets  # noqa: E402
from states.menu_state import MenuState  # noqa: E402
from states.text import ArcadeTextRenderer  # noqa: E402

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
HIGHSCORES_FILE = "highscores.json"
ICON_PATH = resource_root() / "assets" / "icon" / "image.png"


def resolve_config() -> dict[str, Any]:
    """Load JSON config when provided, otherwise use built-in defaults."""
    if len(sys.argv) == 1:
        return default_config()
    if len(sys.argv) == 2:
        return load_config(sys.argv[1])
    print("Usage: pac-man.py [config.json]")
    sys.exit(1)


def highscore_path(config: dict[str, Any]) -> str:
    """Store highscores next to the executable in release builds."""
    filename = Path(
        str(config.get("highscore_filename", HIGHSCORES_FILE))
    ).name
    if getattr(sys, "frozen", False):
        return str(user_data_dir() / filename)
    return str(config.get("highscore_filename", HIGHSCORES_FILE))


def main() -> None:
    """Initialize pygame, load assets, and run the game loop."""
    pygame.init()
    pygame.key.set_repeat(0)
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), vsync=1)
    pygame.display.set_caption("Pac-Man")
    if ICON_PATH.exists():
        pygame.display.set_icon(pygame.image.load(ICON_PATH))

    config = resolve_config()
    assets = Assets()
    assets.load()
    text = ArcadeTextRenderer()
    text.preload()
    highscores = HighscoreManager(highscore_path(config))
    highscores.load()
    engine = GameEngine(
        screen,
        assets,
        text,
        highscores,
        config,
        MenuState(),
        window_size=(SCREEN_WIDTH, SCREEN_HEIGHT),
    )
    engine.run()

    pygame.quit()


if __name__ == "__main__":
    main()
