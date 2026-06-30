from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_ROOT))

import pygame  # noqa: E402

from config.config import DEFAULT_CONFIG
from game.fruit_schedule import fruit_for_level, spawn_seconds_for_level
from game.game_world import GameWorld, spawn_fruit, update_fruit_spawns
from game.level import load_level
from game.render_config import WorldRenderConfig
from sprites.assets import Assets
from sprites.sprite_types import FruitKind, GhostKind


@pytest.fixture(scope="module", autouse=True)
def pygame_init() -> Generator[None, None, None]:
    """Initialize pygame once for headless asset loading."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_fruit_schedule_level_one() -> None:
    assert fruit_for_level(1) == FruitKind.CHERRY
    assert spawn_seconds_for_level(1) == (9, 41)


def test_fruit_schedule_high_levels_use_key() -> None:
    assert fruit_for_level(12) == FruitKind.KEY
    assert spawn_seconds_for_level(12) == (9, 41)


def test_level_ghost_spawns_are_walkable() -> None:
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    assert len(layout.ghost_spawns) == 4
    kinds = {kind for kind, _cell in layout.ghost_spawns}
    assert kinds == set(GhostKind)
    for _kind, cell in layout.ghost_spawns:
        assert not layout.is_wall(cell)


def _build_world() -> GameWorld:
    assets = Assets()
    assets.load()
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    return GameWorld(layout, assets, render_config)


def test_reset_fruit_spawns_clears_index_and_active_fruit() -> None:
    world = _build_world()
    spawn_fruit(world, 0)
    world._fruit_spawn_index = 1

    world.reset_fruit_spawns()

    assert world._fruit_spawn_index == 0
    assert world._fruit is None


def test_reset_fruit_spawns_allows_early_spawn_after_life_lost() -> None:
    world = _build_world()
    world._fruit_spawn_index = 1

    world.reset_fruit_spawns()
    update_fruit_spawns(world, level_elapsed_s=9, now_ms=9_000)

    assert world._fruit is not None
    assert world._fruit_spawn_index == 1
