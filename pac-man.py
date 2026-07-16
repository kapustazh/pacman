import os
import sys
from pathlib import Path
from typing import Any

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SRC_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_ROOT))

import pygame  # noqa: E402

from config.config import resolve_config  # noqa: E402
from core import paths  # noqa: E402
from core.engine import GameEngine  # noqa: E402
from managers.highscore_manager import HighscoreManager  # noqa: E402
from sprites.assets import AssetError, Assets  # noqa: E402
from states.menu_state import MenuState  # noqa: E402
from states.text import ArcadeTextRenderer  # noqa: E402

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
HIGHSCORES_FILE = "highscores.json"
ICON_PATH = paths.resource_root() / "assets" / "icon" / "image.png"


def highscore_path(config: dict[str, Any]) -> str:
    """Store highscores next to the executable in release builds.

    Args:
        config: The configuration dictionary.

    Returns:
        The path to the highscores file.
    """
    filename = Path(
        str(config.get("highscore_filename", HIGHSCORES_FILE))
    ).name
    if paths.is_frozen_build():
        return str(paths.user_data_dir() / filename)
    return str(config.get("highscore_filename", HIGHSCORES_FILE))


def main() -> None:
    """Initialize pygame, load assets, and run the game loop.

    Returns:
        None
    """
    config = resolve_config()
    pygame.init()
    pygame.key.set_repeat(0)
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), vsync=1)
    pygame.display.set_caption("Pac-Man")
    if ICON_PATH.exists():
        pygame.display.set_icon(pygame.image.load(ICON_PATH))

    assets = Assets()
    text = ArcadeTextRenderer()
    try:
        assets.load()
        text.preload()
    except (AssetError, FileNotFoundError) as exc:
        print(f"Warning: {exc}")
        pygame.quit()
        sys.exit(1)
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
