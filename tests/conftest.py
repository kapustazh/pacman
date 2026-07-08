from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pygame  # noqa: E402

from config.config import DEFAULT_CONFIG  # noqa: E402
from game.game_world import GameWorld  # noqa: E402
from game.level import load_level  # noqa: E402
from game.render_config import WorldRenderConfig  # noqa: E402
from sprites.assets import Assets  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def pygame_init() -> Generator[None, None, None]:
    """Initialize pygame once for headless asset loading."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game_world() -> GameWorld:
    """Fresh procedural test world with loaded assets."""
    assets = Assets()
    assets.load()
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    return GameWorld(layout, assets, render_config)
